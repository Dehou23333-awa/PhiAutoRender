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

namelist = []


def renderHelper(filename):
    filename = filename.replace('\\', '/')  # Convert backslashes to forward slashes
    realname = filename.split('/')[-1]
    logger.debug("Processing file: %s", filename)
    if not os.path.exists("./temp"):
        os.makedirs("./temp")
    
    logger.debug("Extracting config.tom from %s", filename)
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        config = zip_ref.read('config.toml').decode('utf-8')
    with open(f"./temp/config_{realname}.toml", 'w', encoding='utf-8') as f:
        f.write(config)
    logger.debug("Config.tom extracted and saved to ./temp/config_%s.toml", realname)

    logger.info("Starting render process for file: %s", filename)
    cmd = [PhiRecorderPath, "--render", f'{os.path.abspath(filename)}', "--output", os.path.abspath(f"./output"), "--config", os.path.abspath(f"./temp/config_{realname}.toml")]
    logger.debug("Running command: %s", ' '.join(cmd))
    subprocess.run(cmd, shell=True)

def queryname(filename):
    filename = filename.replace('\\', '/')
    filename = filename.split('/')[-1]
    for root, dirs, files in os.walk("../Unpack/output"):
        for file in files:
            if file == filename:
                data = zipfile.ZipFile(os.path.join(root, file)).read('info.txt').decode('utf-8')
                return data.split('\n')[2][6:-4]+"-"+data.split('\n')[5][7:9]+".mp4"

def renameHelper(filename):
    filename = filename.replace('\\', '/')  # Convert backslashes to forward slashes
    realname = queryname(filename)
    for root, dirs, files in os.walk("./output"):
        for file in files:
            if file not in namelist:
                os.rename(os.path.join(root, file), os.path.join(root, realname))
                namelist.append(realname)

def main(fast=True):
    for root, dirs, files in os.walk("../Unpack/output"):
        for file in files:
            if fast and not (file.endswith(('IN-16_9-normal.pez', 'AT-16_9-normal.pez'))):
                continue
            file_path = os.path.join(root, file)
            logger.info("Rendering file: %s", file_path)
            video_type = file_path.split("\\")[1]
            # renderHelper(file_path)
            renameHelper(file_path)
            # subprocess.run(["python", "../Upload/main.py", file_path, video_type], shell=True)
    shutil.rmtree("./temp")


if __name__ == "__main__":
    main(fast=True)
    # print(queryname("Rebirth.ああああ-IN-16_9-normal.pez"))
    # renderHelper(r"D:\Phigros-DEV\simulation_and_rendering\PhiAutoRender-main\Unpack\output\Phigros_4.5.0_20230901_16_9-normal.pez")