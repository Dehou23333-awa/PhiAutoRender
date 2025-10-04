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

def build_md5_table(info_data):
    logger.info("Building file information table with MD5 hashes")
    
    # 遍历文件夹计算MD5
    for root, dirs, files in os.walk('../temp/chart'):
        folder_name = os.path.basename(root)
        if folder_name == 'chart':
            continue
        
        # 提取歌曲ID (去掉最后的.0后缀)
        song_id = folder_name[:-2] if folder_name.endswith('.0') else folder_name
        
        # 如果info_data中不存在这个歌曲，跳过
        if song_id not in info_data:
            logger.warning(f"Song {song_id} found in chart folder but not in info_data")
            continue
        
        # 为每个难度添加MD5字段
        for file in files:
            level = os.path.splitext(file)[0].split('-')[-1].upper()
            if level in ['EZ', 'HD', 'IN', 'AT']:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
                    # 将MD5添加到对应难度的info中
                    if level in info_data[song_id]:
                        info_data[song_id][level]["md5"] = md5

    # 保存合并后的数据
    with open('../data/Chart_info_New.json', 'w', encoding='utf-8') as info_file:
        json.dump({"Version": version, "PhiVersion": Phiversion, "Songs": info_data}, info_file, indent=4, ensure_ascii=False)

    logger.info("MD5 table successfully created and merged into info data")
    return info_data


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
            # Retry download once
            logger.warning("MD5 mismatch, retrying download...")
            download(url)
            apk_md5 = hashlib.md5(open(f"../temp/Phigros_{version}.apk", 'rb').read()).hexdigest()
            if apk_md5 != md5_apk:
                raise Exception("MD5 mismatch after retry, download failed.")
            logger.info("MD5 check passed after retry.")
        else:
            logger.info("MD5 check passed.")
    logger.info("APK is ready.")

    # Step 2 Unpack Apk
    info = gameInformation.run("../temp/Phigros_{}.apk".format(version))
    if not os.path.isdir("../temp/info") and not os.path.isdir("../temp/chart"):
        unpack.run("../temp/Phigros_{}.apk".format(version))

    # Step 3 Build file information table with md5
    if not DEBUG:
        songs_data = build_md5_table(info)
    else:
        with open('../data/Chart_info_New.json', 'r', encoding='utf-8') as info_file:
            songs_data = json.load(info_file)['Songs']

    # Step 4 Compare MD5
    # New songs added. Check if the song has "AT" Level
    New_Songs = {}
    # Existing charts changed.
    Changed_Charts = {}
    # Special: Check if a song that had no "AT" Level was added a "AT" Level
    New_AT_Songs = {}
    
    # 加载旧数据
    old_songs_data = old_chart_info.get("Songs", {})
    
    # Main Logic
    for song, song_info in songs_data.items():
        # 检查是否是新歌曲
        if song not in old_songs_data:
            # 检查是否有AT难度
            has_at = "AT" in song_info and "md5" in song_info["AT"]
            logger.info("Found new song: {} {}".format(song, "with AT level" if has_at else "without AT level"))
            New_Songs[song] = 1 if has_at else 0
            continue
        
        # 检查现有歌曲的变化
        old_song_info = old_songs_data[song]
        for level in ['EZ', 'HD', 'IN', 'AT']:
            # 检查新增的AT难度
            if level == "AT":
                if level in song_info and "md5" in song_info[level]:
                    if level not in old_song_info or "md5" not in old_song_info[level]:
                        logger.info("Found new AT level for song: {}".format(song))
                        New_AT_Songs[song] = 1
                        continue
            
            # 检查MD5变化
            if level in song_info and "md5" in song_info[level]:
                if level in old_song_info and "md5" in old_song_info[level]:
                    if song_info[level]["md5"] != old_song_info[level]["md5"]:
                        logger.info("Found changed chart: {}, {}".format(song, level))
                        if song not in Changed_Charts:
                            Changed_Charts[song] = []
                        Changed_Charts[song].append(level)

    logger.debug("New Songs: {}".format(New_Songs))
    logger.debug("Changed Charts: {}".format(Changed_Charts))
    logger.debug("New AT Songs: {}".format(New_AT_Songs))

    if len(New_Songs) + len(Changed_Charts) + len(New_AT_Songs) > 50:
        logger.warning("Too many changes detected, please check manually.")

    LEVELS = ["EZ", "HD", "IN", "AT"]

    # Step 5: Pack Charts into pez
    if os.path.exists("../temp/output"):
        shutil.rmtree("../temp/output")
    for song in New_Songs:
        for level in range(3 + int(New_Songs[song])):
            PezHelper(song, LEVELS[level], "NewSongs")
    for song in Changed_Charts:
        for level in Changed_Charts[song]:
            PezHelper(song, level, "Changed")
    for song in New_AT_Songs:
        PezHelper(song, "AT", "NewAT")

if __name__ == "__main__":
    main()