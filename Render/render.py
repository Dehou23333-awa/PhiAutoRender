import subprocess
import logging
import os
import zipfile
import sys

PhiRecorderPath = r"C:\Users\Moxiao\AppData\Local\phi-recorder\phi-recorder.exe"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

def main(fast=True):
    for root, dirs, files in os.walk("../Unpack/output"):
        for file in files:
            if fast and not (file.endswith(('IN-16_9-normal.pez', 'AT-16_9-normal.pez'))):
                continue
            file_path = os.path.join(root, file)
            logger.info("Rendering file: %s", file_path)
            renderHelper(file_path)


if __name__ == "__main__":
    main(fast=True)
    # renderHelper(r"D:\Phigros-DEV\simulation_and_rendering\PhiAutoRender-main\Unpack\output\Phigros_4.5.0_20230901_16_9-normal.pez")