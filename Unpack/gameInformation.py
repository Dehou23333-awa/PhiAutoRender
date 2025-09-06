import json
import os
from UnityPy import Environment
import zipfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run(path):
    logging.info("Starting run function with path: %s", path)
    if not os.path.isdir("info"):
        logging.info("Creating 'info' directory")
        os.mkdir("info")
    with open("typetree.json") as f:
        typetree = json.load(f)
    env = Environment()
    logging.info("Loading APK file: %s", path)
    with zipfile.ZipFile(path) as apk:
        with apk.open("assets/bin/Data/globalgamemanagers.assets") as f:
            env.load_file(f.read(), name="assets/bin/Data/globalgamemanagers.assets")
        with apk.open("assets/bin/Data/level0") as f:
            env.load_file(f.read())
    logging.info("Processing game information")
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
            table.append((song["songsId"], song["songsName"], song["composer"], song["illustrator"], *song["charter"]))

    logging.info("Successfully processed game information")

    # 导出 difficulty.json 格式（在 difficulty 已经生成后）
    difficulty_labels = ["EZ", "HD", "IN", "AT"]
    difficulty_dict = {}
    for item in difficulty:
        key = item[0]
        levels = item[1:]
        # 仅包含存在的难度
        difficulty_dict[key] = {difficulty_labels[i]: levels[i] for i in range(len(levels))}

    with open("info/difficulty.json", "w", encoding="utf8") as f:
        json.dump(difficulty_dict, f, ensure_ascii=False, indent=4)

    # 转换 info 为嵌套 JSON 格式并导出
    info_nested = {}
    for item in table:
        key = item[0]
        info_nested[key] = {
            "Name": item[1],
            "Composer": item[2],
            "illustrator": item[3],
            "EZ": item[4] if len(item) > 4 else None,
            "HD": item[5] if len(item) > 5 else None,
            "IN": item[6] if len(item) > 6 else None,
            "AT": item[7] if len(item) > 7 else None
        }

    with open("info/info.json", "w", encoding="utf8") as f:
        json.dump(info_nested, f, ensure_ascii=False, indent=4)

    logging.info("Run gameInformation completed")
