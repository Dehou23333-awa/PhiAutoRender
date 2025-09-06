import asyncio
from bilibili_api import sync, video_uploader, Credential
import dotenv
import os
import json

dotenv.load_dotenv()

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
        print((value["Name"]+"."+value["Composer"]))
        print(name)
        if (value["Name"]+"."+value["Composer"]) == name:
            return f"{value['Name']} - {value['Composer']} (Illustrator: {value['illustrator']})"

def run(Video_path):
    Title = "【Phigros/谱面演示】" + infoHelper(Video_path[17:-7])
    print(Title)

if __name__ == "__main__":
    Video_path = "../Render/output/雪降り ~雪が降っている~.AiSS w 夜輪 ft. 結月ゆかり_AT.mp4"
    run(Video_path)