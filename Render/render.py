import subprocess
import logging
import os
import zipfile

PhiRecorderPath = r"C:\Users\Moxiao\AppData\Local\phi-recorder\phi-recorder.exe"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def renderHelper(filename):
    realname = filename.split('/')[-1]
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

def main():
    renderHelper("input/Changed/Rebirth.ああああ-IN-4_3-normal.pez")

if __name__ == "__main__":
    main()