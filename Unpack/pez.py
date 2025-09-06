from zipfile import ZipFile
import os
import json
import toml
import logging

LEVELS = ["EZ", "HD", "IN", "AT"]

PhiRecorderConfigToml = {
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def prepare_config(isDebug, Ratio):
    """
    生成修改后的config.toml配置文件内容
    
    Args:
        isDebug (bool): 是否为调试模式
        Ratio (float): 谱面比例
    
    Returns:
        str: 修改后的配置文件内容，如果失败返回None
    """
    # 读取原始配置文件
    config_path = "../Render/config.toml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
    except FileNotFoundError:
        logger.error(f"Error: config.toml not found at {config_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading config.toml: {e}")
        return None
    
    # 根据参数修改配置
    if isDebug:
        # 调试模式配置
        config['chartDebugLine'] = 0.4
        config['chartDebugNote'] = 0.3
        config['chartRatio'] = 0.4
    else:
        # 正常模式配置
        config['chartDebugLine'] = 0.0
        config['chartDebugNote'] = 0.0
        config['chartRatio'] = 1.0

    if Ratio == "4:3":
        config['resolution'] = [1280, 960]
    elif Ratio == "16:9":
        config['resolution'] = [1280, 720]

    # 直接返回配置文件内容字符串
    try:
        import io
        config_string = io.StringIO()
        toml.dump(config, config_string)
        config_content = config_string.getvalue()
        config_string.close()
        return config_content
    except Exception as e:
        logger.error(f"Error generating config content: {e}")
        return None


def create_pez(track_id, level_name, type, isDebug=False, Ratio="16:9"):

    """Create a .pez file based on track ID and difficulty level."""
    if level_name not in LEVELS:
        logger.error(f"Error: Invalid level {level_name}. Must be one of {LEVELS}.")
        return

    # Read info.json
    infos = {}
    try:
        with open("info/info.json", encoding="utf8") as f:
            infos = json.load(f)
    except FileNotFoundError:
        logger.error("Error: info.json not found in info directory.")
        return
    except Exception as e:
        logger.error(f"Error reading info.json: {e}")
        return

    # Read difficulty.json
    difficulties = {}
    try:
        with open("info/difficulty.json", encoding="utf8") as f:
            difficulties = json.load(f)
    except FileNotFoundError:
        logger.error("Error: difficulty.json not found in info directory.")
        return
    except Exception as e:
        logger.error(f"Error reading difficulty.json: {e}")
        return

    if track_id not in infos:
        logger.error(f"Error: Track ID {track_id} not found in info.json.")
        return

    info = infos[track_id]
    
    # Check if the track has the requested difficulty level
    if track_id not in difficulties or level_name not in difficulties[track_id] or difficulties[track_id][level_name] is None:
        logger.error(f"Error: Track {track_id} has no {level_name} difficulty.")
        return

    # Create .pez file
    path = f"output/{type}"
    if type == "NewSongs" or type == "DeletedSongs":
        path = f"output/{type}/{track_id}"

    if not os.path.exists(path):
        os.makedirs(path)

    # 转换Ratio为文件名安全的格式
    ratio_safe = Ratio.replace(":", "_")
    # 转换isDebug为简短格式
    debug_suffix = "debug" if isDebug else "normal"
    
    pez_path = f"{path}/{track_id}-{level_name}-{ratio_safe}-{debug_suffix}.pez"
    logger.info(f"Processing: {info['Name']}, Composer: {info['Composer']}, Level: {level_name}")
    
    try:
        with ZipFile(pez_path, "x") as pez:
            # Write info.txt
            info_txt = (
                "#\n"
                f"Name: {info['Name']}\n"
                f"Song: {track_id}.ogg\n"
                f"Picture: {track_id}.png\n"
                f"Chart: {track_id}.json\n"
                f"Level: {level_name} Lv.{difficulties[track_id][level_name]}\n"
                f"Composer: {info['Composer']}\n"
                f"Illustrator: {info['illustrator']}\n"
                f"Charter: {info[level_name]}"
            )
            pez.writestr("info.txt", info_txt)

            # 生成修改后的配置文件内容并直接写入zip
            config_content = prepare_config(isDebug, Ratio)
            if config_content:
                pez.writestr("config.toml", config_content)
            
            # Add files to .pez
            files = [
                (f"chart/{track_id}.0/{level_name}.json", f"{track_id}.json"),
                (f"Illustration/{track_id}.png", f"{track_id}.png"),
                (f"music/{track_id}.ogg", f"{track_id}.ogg"),
            ]
            
            for src, dst in files:
                try:
                    pez.write(src, dst)
                except FileNotFoundError:
                    logger.warning(f"File not found: {src}")
    except Exception as e:
        logger.error(f"Error creating .pez file {pez_path}: {e}")