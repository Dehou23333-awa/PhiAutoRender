import subprocess
import logging
import os
import zipfile
import shutil
import zipfile

PhiRecorderPath = r"C:\Users\Moxiao\AppData\Local\phi-recorder\phi-recorder.exe"

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
    cmd = [PhiRecorderPath, "--render", f'{os.path.abspath(file_path)}', "--output", os.path.abspath(f"../temp/videos/{pez_name}"), "--config", os.path.abspath(f"../temp/config/config_{realname}.toml")]
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
    for root, dirs, files in os.walk("../temp/output"):
        for file in files:
            if fast and not (file.endswith(('IN-16_9-normal.pez', 'AT-16_9-normal.pez'))):
                continue

            file_path = os.path.join(root, file)
            video_type = file_path.split("\\")[1]
            pez_name = queryname(file_path)
            realname = file_path.replace('\\', '/').split('/')[-1]

            if os.path.exists(f"../temp/videos/{pez_name}"):
                logger.info("Video for %s already exists, skipping rendering.", pez_name)
                continue

            logger.info("Rendering file: %s", file_path)
            renderHelper()
            cmd = ["python", "../Upload/main.py", pez_name, video_type]
            logger.debug("Running upload command: %s", ' '.join(cmd))
            subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    main(fast=True)