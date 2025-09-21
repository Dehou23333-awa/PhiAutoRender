import json
import os
from UnityPy import Environment
import zipfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run(path):
    logger.info("Starting run function with path: %s", path)
    if not os.path.isdir("info"):
        logger.info("Creating 'info' directory")
        os.mkdir("info")
    with open("typetree.json") as f:
        typetree = json.load(f)
    env = Environment()
    logger.info("Loading APK file: %s", path)
    with zipfile.ZipFile(path) as apk:
        with apk.open("assets/bin/Data/globalgamemanagers.assets") as f:
            env.load_file(f.read(), name="assets/bin/Data/globalgamemanagers.assets")
        with apk.open("assets/bin/Data/level0") as f:
            env.load_file(f.read())
    logger.info("Processing game information")
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        data = obj.read()
        if data.m_Script.get_obj().read().name == "GameInformation":
            GameInformation = obj.read_typetree(typetree["GameInformation"])

    difficulty = []
    table = []

    for key, songs in GameInformation["song"].items():
        if key == "otherSongs":
            continue
        for song in songs:
            if len(song["difficulty"]) == 5:
                song["difficulty"].pop()
            if song["difficulty"][-1] == 0.0:
                song["difficulty"].pop()
                song["charter"].pop()
            for i in range(len(song["difficulty"])):
                song["difficulty"][i] = str(round(song["difficulty"][i], 1))
            song["songsId"] = song["songsId"][:-2]
            difficulty.append([song["songsId"]]+song["difficulty"])
            table.append((song["songsId"], song["songsName"], song["composer"], song["illustrator"], song["previewTime"], song["previewEndTime"], *song["charter"]))

    logger.info("Successfully processed game information")

    # 创建歌曲ID到章节的映射
    song_to_chapter = {}
    for chapter in GameInformation["chapters"]:
        chapter_name = chapter["songInfo"]["banner"]
        for song in chapter["songInfo"]["songs"]:
            song_id = song["songsId"][:-2]  # 去掉后缀
            song_to_chapter[song_id] = chapter_name

    # 合并难度和详细信息到一个 JSON 文件
    difficulty_labels = ["EZ", "HD", "IN", "AT"]
    difficulty_dict = {item[0]: item[1:] for item in difficulty}
    merged_data = {}
    
    for item in table:
        key = item[0]
        levels = difficulty_dict.get(key, [])
        
        # 构建基本歌曲信息
        song_data = {
            "Name": item[1],
            "Composer": item[2],
            "illustrator": item[3],
            "chapter": song_to_chapter.get(key, "Unknown"),
            "previewTime": round(item[4], 2),
            "previewEndTime": round(item[5], 2)
        }
        
        # 直接添加难度信息到根级别
        for i in range(len(levels)):
            song_data[difficulty_labels[i]] = {
                "charter": item[6 + i],
                "difficulty": levels[i]
            }
        
        merged_data[key] = song_data

    logger.info("Run gameInformation completed")
    return merged_data

if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))