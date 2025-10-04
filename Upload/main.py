import asyncio
from bilibili_api import sync, video_uploader, Credential
import dotenv
import os
import json
import logging
import Cover
import sys
from mutagen.oggvorbis import OggVorbis

dotenv.load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SESSDATA = os.getenv("SESSDATA")
BILI_JCT = os.getenv("BILI_JCT")
BUVID3 = os.getenv("BUVID3")

version = ""
t = ""
level = ""
songname = ""
pez_name = ""
video_type = ""

async def upload(Title, Description, Cover_path, Video_path):
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    vu_meta = video_uploader.VideoMeta(
        tid=136,
        title=Title,
        tags=["音乐游戏", "谱面", "Phigros", "AUTOPLAY", "谱面演示", "锁屏练习"],
        desc=Description,
        cover=Cover_path,
        no_reprint=True,
    )
    await vu_meta.verify(credential=credential) # 本地预检 meta 信息，出错则抛出异常
    page = video_uploader.VideoUploaderPage(
        path=Video_path,
        title=Title,
        description=Description,
    )
    uploader = video_uploader.VideoUploader(
        [page], vu_meta, credential, line=video_uploader.Lines.QN
    )

    @uploader.on("__ALL__")
    async def ev(data):
        logger.debug(f"Event: {data}")

    await uploader.start()

def infoHelper(name):
    name = name[:-3]
    with open("../data/Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)["Songs"]
    for key, value in infos.items():
        if (key) == name:
            return f"{value['Name']}"
        
def anylizeHelper(name):
    with open(f"../temp/chart/{name}.0/{level}.json", encoding="utf8") as f:
        chart = json.load(f)["judgeLineList"]
    des = "谱面信息："
    # BPM最小~最大
    bpm_list = []
    tap = 0
    hold = 0
    flick = 0
    drag = 0
    for line in chart:
        bpm_list.append(line["bpm"])
        for note in line["notesAbove"]:
            if note["type"] == 1:
                tap += 1
            elif note["type"] == 2:
                drag += 1
            elif note["type"] == 3:
                hold += 1
            elif note["type"] == 4:
                flick += 1
        for note in line["notesBelow"]:
            if note["type"] == 1:
                tap += 1
            elif note["type"] == 2:
                drag += 1
            elif note["type"] == 3:
                hold += 1
            elif note["type"] == 4:
                flick += 1
    if min(bpm_list) == max(bpm_list):
        des += f"\nBPM：{round(min(bpm_list))}"
    else:
        des += f"\nBPM：{round(min(bpm_list))}~{round(max(bpm_list))}"
    des += f"\n物量：{tap + hold + flick + drag}"
    des += f"\nTap: {tap}  Drag: {drag}  Hold: {hold}  Flick: {flick}"
    des += f"\n判定线总数：{len(chart)}"

    return des

def getsongtime(name):
    audio = OggVorbis(f"../temp/music/{name}.ogg")
    return round(audio.info.length, 2)

def videopath(name):
    for root, dirs, files in os.walk(f"../temp/videos/{name}"):
        for file in files:
            if file.endswith(".mp4"):
                return os.path.abspath(f"../temp/videos/{name}/{file}")

def description(name):
    global level, t, version
    with open("../data/Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)
    des = ""
    des += f"Phigros v{version} {t}\n"
    for key, value in infos["Songs"].items():
        if (key) == name[:-3]:
            des += f"名称：{value['Name']}\n曲师：{value['Composer']}\n画师：{value['illustrator']}\n谱师：{value[level]['charter']}"
            if level in value:
                des += f"\n难度：{level} Lv.{value[level]['difficulty']}"
    des += f"\n曲目时长：{getsongtime(name[:-3])}s\n\n"
    des += anylizeHelper(name[:-3])
    des += "\n\n定数、物量、Note数、判定线数、曲目时长、BPM等由程序获取\n本视频由 PhiAutoRender 自动生成。如有侵权请联系删除。\n渲染：Phi-Recorder By HLMC离开"
    return des

def illustrationHelper(name):
    return f"../temp/illustration/{name}.png"

def run():
    global pez_name, video_type
    global version, t, level, songname
    songname = infoHelper(pez_name)
    with open("../data/Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)
    version = infos['PhiVersion']
    if video_type == "Changed":
        t = "改谱"
    elif video_type == "NewSongs":
        t = "新歌"
    elif video_type == "NewAT":
        t = "新AT"
    level = pez_name[-2:]
    print(level, pez_name, songname, version, t)

    Title = f"【Phigros 谱面演示/v{version}/{t}】" + songname + " " + level

    Description = description(pez_name)

    # 不重复生成图片
    ill_path = illustrationHelper(pez_name[:-3])
    Cover_Path = f"../temp/Covers/cover_{pez_name}.png"
    try:
        Cover.run_pillow(ill_path, Cover_Path, songname)
    except FileExistsError:
        pass

    # print(Title, Description, Cover_path)

    logger.info("Title: %s", Title)
    logger.info("Description: %s", Description)
    logger.info("Cover: %s", Cover_Path)
    video_path = videopath(pez_name)

    logger.info("Video: %s", video_path)

    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            sync(upload(Title, Description, Cover_Path, video_path))
            logger.info("Upload successful!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Upload failed (attempt {attempt + 1}/{max_retries}): %s", e)
                logger.info("Retrying...")
            else:
                logger.error(f"Upload failed after {max_retries} attempts: %s", e)
                raise

if __name__ == "__main__":
    if len(sys.argv) > 2:
        pez_name = sys.argv[1]
        video_type = sys.argv[2]
    if not os.path.exists("../temp/Covers"):
        os.makedirs("../temp/Covers")
    run()