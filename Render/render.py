import subprocess
import logging
import os
import zipfile
import shutil
import zipfile
import dotenv

dotenv.load_dotenv()

PhiRecorderPath = os.getenv("PhiRecorderPath")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

video_type = ""
pez_name = ""
realname = ""
file_path = ""


def renderHelper():

    logger.debug("Processing file: %s", pez_name)
    if not os.path.exists("../temp/videos"):
        os.makedirs("../temp/videos")
    if not os.path.exists("../temp/config"):
        os.makedirs("../temp/config")

    logger.debug("Extracting config.tom from %s", file_path)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        config = zip_ref.read('config.toml').decode('utf-8')
    with open(f"../temp/config/config_{realname}.toml", 'w', encoding='utf-8') as f:
        f.write(config)
    logger.debug("Config.tom extracted and saved to ../temp/config/config_%s.toml", realname)
    
    logger.info("Starting render process for file: %s", pez_name)
    cmd = [PhiRecorderPath, "--render", f'{os.path.abspath(file_path)}', "--output", os.path.abspath(f"../temp/videos/{pez_name}.mp4"), "--config", os.path.abspath(f"../temp/config/config_{realname}.toml")]
    logger.debug("Running command: %s", ' '.join(cmd))
    subprocess.run(cmd, shell=True, check=True)

def queryname(filename):
    filename = filename.replace('\\', '/')
    filename = filename.split('/')[-1]
    for root, dirs, files in os.walk("../temp/output"):
        for file in files:
            if file == filename:
                data = zipfile.ZipFile(os.path.join(root, file)).read('info.txt').decode('utf-8')
                return data.split('\n')[2][6:-4]+"."+data.split('\n')[5][7:9]


def main(fast=True):
    global video_type, pez_name, realname, file_path
    
    # 读取渲染顺序文件
    render_order_file = "../temp/render_order.txt"
    render_queue = []
    
    if os.path.exists(render_order_file):
        logger.info("Loading render order from %s", render_order_file)
        with open(render_order_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    render_queue.append(line)
        logger.info("Loaded %d items in render queue", len(render_queue))
    else:
        logger.warning("Render order file not found: %s. Using default file traversal.", render_order_file)
    
    # 如果有渲染队列，按照队列顺序渲染
    if render_queue:
        for queue_item in render_queue:
            # queue_item格式: type/song/level 例如: NewSongs/BANGINGSTRIKE.DewPleiades/AT
            parts = queue_item.split('/')
            if len(parts) == 3:
                type_name, song_id, level = parts
                
                # 构建文件路径
                if type_name in ["NewSongs", "DeletedSongs"]:
                    base_path = f"../temp/output/{type_name}/{song_id}"
                else:
                    base_path = f"../temp/output/{type_name}"
                
                # 查找匹配的pez文件
                if os.path.exists(base_path):
                    for file in os.listdir(base_path):
                        if fast and not (file.endswith(('IN-16_9-normal.pez', 'AT-16_9-normal.pez'))):
                            continue
                        
                        # 检查文件是否匹配当前要渲染的歌曲和难度
                        if file.startswith(f"{song_id}-{level}-"):
                            file_path = os.path.join(base_path, file)
                            video_type = type_name
                            pez_name = queryname(file)
                            realname = file
                            
                            logger.info("Rendering file: %s", file_path)
                            try:
                                renderHelper()
                            except Exception as e:
                                logger.warning("Rendering failed for %s: %s. Retrying...", pez_name, e)
                                try:
                                    renderHelper()
                                except Exception as e:
                                    logger.error("Rendering failed again for %s: %s. Skipping this file.", pez_name, e)
                                    continue
                            cmd = ["python", "../Upload/main.py", pez_name, video_type]
                            logger.debug("Running upload command: %s", ' '.join(cmd))
                            subprocess.run(cmd, shell=True, check=True)
                else:
                    logger.warning("Path not found for queue item: %s", queue_item)
    else:
        # 如果没有渲染队列，使用原有的遍历方式
        for root, dirs, files in os.walk("../temp/output"):
            for file in files:
                if fast and not (file.endswith(('IN-16_9-normal.pez', 'AT-16_9-normal.pez'))):
                    continue

                file_path = os.path.join(root, file)
                video_type = file_path.split("\\")[1]
                pez_name = queryname(file_path)
                realname = file_path.replace('\\', '/').split('/')[-1]

                logger.info("Rendering file: %s", file_path)
                try:
                    renderHelper()
                except Exception as e:
                    logger.warning("Rendering failed for %s: %s. Retrying...", pez_name, e)
                    try:
                        renderHelper()
                    except Exception as e:
                        logger.error("Rendering failed again for %s: %s. Skipping this file.", pez_name, e)
                        continue
                cmd = ["python", "../Upload/main.py", pez_name, video_type]
                logger.debug("Running upload command: %s", ' '.join(cmd))
                subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    main(fast=True)