import taptap as taptap
import gameInformation as gameInformation, unpack as unpack
from helpers import *

import json
import os
import hashlib
import logging
import time
import shutil
import aria2p

DEBUG = False

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=16800,
        secret="6365tHRnPmb2"
    )
)

def download(url):
    logger.info(f"Downloading from URL: {url}")
    download = aria2.add_uris([url],
    options={"dir": os.path.abspath("../temp"), "out": f"Phigros_{version}.apk"}  # 指定下载目录
    )
    while not download.is_complete:
        download.update()
        logger.info(f"Download progress: {download.progress_string()}")
        time.sleep(1)
    logger.info("Download completed.")

url, md5_apk, version, Phiversion = "","", "", ""

def build_md5_table():
    md5_dict = {}
    logger.info("Building file information table with MD5 hashes")
    for root, dirs, files in os.walk('../temp/chart'):
        folder_name = os.path.basename(root)
        if folder_name == 'chart':
            continue
        if folder_name not in md5_dict:
            md5_dict[folder_name] = {}
        for file in files:
            level = os.path.splitext(file)[0].split('-')[-1].upper()
            if level in ['EZ', 'HD', 'IN', 'AT']:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
                    md5_dict[folder_name][level] = md5

    with open("../temp/info/info.json", "r", encoding='utf-8') as info_file:
        info_data = json.load(info_file)

    with open("../temp/info/difficulty.json", "r", encoding='utf-8') as diff_file:
        diff_data = json.load(diff_file)

    with open('../data/Chart_info_New.json', 'w', encoding='utf-8') as md5_file:
        json.dump({"Version":version,"PhiVersion":Phiversion,"MD5":md5_dict,"INFO":info_data,"DIFFICULTY":diff_data}, md5_file, indent=4, ensure_ascii=False)

    logger.info("MD5 table successfully created")
    return md5_dict


def main():
    global url, md5_apk, version, Phiversion

    # Step 1: 持续检查更新，直到找到新版本
    logger.info("Starting continuous update monitoring...")
    
    while True:
        try:
            # 获取最新版本信息
            url, md5_apk, version, Phiversion = taptap.main()
            
            # 检查是否有更新
            with open('../data/Chart_info.json', 'r', encoding='utf-8') as f:
                old_chart_info = json.load(f)
                logger.info("Checking for updates")
                if old_chart_info["Version"] == version:
                    logger.info("No updates found. Waiting for next check...")
                    time.sleep(5)  # 等待5秒后再次检查
                    continue
                else:
                    logger.info("Updates found! Proceeding with download and processing...")
                    break  # 找到更新，跳出循环
        except Exception as e:
            logger.error(f"Error during update check: {e}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)
            continue

    # 只有有新版本时才下载 APK
    logger.info(f"Downloading new APK version: {version}")
    if not os.path.exists(f"../temp/Phigros_{version}.apk"):
        logger.info("Downloading Phigros_{}.apk".format(version))
        logger.info(f"Downloading from URL: {url}")
        download(url)
        logger.info("Checking MD5...")
        apk_md5 = hashlib.md5(open(f"../temp/Phigros_{version}.apk", 'rb').read()).hexdigest()
        if apk_md5 != md5_apk:
            raise Exception("MD5 mismatch, download failed.")
        else:
            logger.info("MD5 check passed.")
    logger.info("APK is ready.")

    # Step 2 Unpack Apk
    if not os.path.isdir("../temp/info") and not os.path.isdir("../temp/chart"):
        gameInformation.run("../temp/Phigros_{}.apk".format(version))
        unpack.run("../temp/Phigros_{}.apk".format(version))

    # Step 3 Build file information table with md5
    if not DEBUG:
        md5_dict = build_md5_table()
    else:
        with open('../data/Chart_info_New.json', 'r', encoding='utf-8') as md5_file:
            md5_dict = json.load(md5_file)['MD5']

    # Step 4 Compare MD5
    # New songs added. Check if the song has "AT" Level
    New_Songs = {}
    # Existing charts changed.
    Changed_Charts = {}
    # Special: Check if a song that had no "AT" Level was added a "AT" Level
    New_AT_Songs = {}
    # Deleted Songs
    Deleted_Songs = {}
    # Main Logic
    for song, levels in md5_dict.items():
        for level, md5 in levels.items():
            if level == "AT":
                if song in old_chart_info["MD5"] and "AT" not in old_chart_info["MD5"][song]:
                    logger.info("Found new AT level for song: {}".format(song))
                    New_AT_Songs[song] = 1
            if song not in old_chart_info["MD5"] and song not in New_Songs:
                # Check if the song has AT level
                if "AT" in levels:
                    logger.info("Found new AT level for song: {}".format(song))
                    New_Songs[song] = 1
                else:
                    logger.info("Found new song without AT level: {}".format(song))
                    New_Songs[song] = 0
            # Changed songs
            if song in old_chart_info["MD5"] and level in old_chart_info["MD5"][song] and old_chart_info["MD5"][song][level] != md5:
                logger.info("Found changed song: {}, {}".format(song, level))
                if song not in Changed_Charts:
                    Changed_Charts[song] = []
                Changed_Charts[song].append(level)

    # 查看被删除的歌
    for song in old_chart_info["MD5"]:
        if song not in md5_dict:
            logger.info("Found deleted song: {}".format(song))
            Deleted_Songs[song] = 1

    logger.debug("New Songs: {}".format(New_Songs))
    logger.debug("Changed Charts: {}".format(Changed_Charts))
    logger.debug("New AT Songs: {}".format(New_AT_Songs))
    logger.debug("Deleted Songs: {}".format(Deleted_Songs))

    LEVELS = ["EZ", "HD", "IN", "AT"]

    # Step 5: Pack Charts into pez
    if os.path.exists("../temp/output"):
        shutil.rmtree("../temp/output")
    for song in New_Songs:
        for level in range(3 + int(New_Songs[song])):
            PezHelper(song[:-2], LEVELS[level], "NewSongs")
    for song in Changed_Charts:
        for level in Changed_Charts[song]:
            PezHelper(song[:-2], level, "Changed")
    for song in New_AT_Songs:
        PezHelper(song[:-2], "AT", "NewAT")
    for song in Deleted_Songs:
        for level in range(3 + int(Deleted_Songs[song])):
            PezHelper(song[:-2], LEVELS[level], "DeletedSongs")

if __name__ == "__main__":
    main()