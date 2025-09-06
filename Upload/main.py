import asyncio
from bilibili_api import sync, video_uploader, Credential
import dotenv
import os
import json
import logging

dotenv.load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SESSDATA = os.getenv("SESSDATA")
BILI_JCT = os.getenv("BILI_JCT")
BUVID3 = os.getenv("BUVID3")

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
        print(data)

    await uploader.start()

def infoHelper(name):
    with open("../Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)["INFO"]
    for key, value in infos.items():
        if (key) == name:
            return f"{value['Name']}"

def description(name, version, t):
    level = name[-2:]
    with open("../Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)
    des = ""
    des += f"Phigros v{version} {t}\n"
    for key, value in infos["INFO"].items():
        if (key) == name[:-3]:
            des += f"名称：{value['Name']}\n曲师：{value['Composer']}\n画师：{value['illustrator']}\n谱师：{value[level]}"
    for key, value in infos["DIFFICULTY"].items():
        if (key) == name[:-3]:
            if level in value:
                des += f"\n难度：{level} Lv.{value[level]}"
    des += "\n\n本视频由 PhiAutoRender 自动生成。如有侵权请联系删除。"
    return des

def run(Video_path, video_type):
    with open("../Chart_info_New.json", encoding="utf8") as f:
        infos = json.load(f)
    version = infos['PhiVersion']
    if video_type == "Changed":
        t = "改谱"
    elif video_type == "NewSongs":
        t = "新歌"
    elif video_type == "NewAT":
        t = "新AT"

    Title = f"【Phigros 谱面演示/v{version}/{t}】" + infoHelper(Video_path[17:-7])
    Description = description(Video_path[17:-4], version, t)
    Cover_path = "咕咕咕没写完"

    logger.info("Title: %s", Title)
    logger.info("Description: %s", Description)
    logger.info("Cover: %s", Cover_path)
    logger.info("Video: %s", Video_path)

    # sync(upload(Title, Description, Cover_path, Video_path))

if __name__ == "__main__":
    video_type = "NewSongs"
    Video_path = "../Render/output/雪降り雪が降っている.AiSSw夜輪ft結月ゆかり-AT.mp4"
    run(Video_path, video_type)