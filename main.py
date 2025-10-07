import subprocess
import logging
import time
import os
import dotenv

dotenv.load_dotenv()

def cleanup():
    """清理之前的输出文件和临时文件"""
    subprocess.run("rd /s /q temp", shell=True)

def setup():
    """初始化"""
    raise FileNotFoundError("Please create a .env file based on .env.example and fill in the required fields.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

starttime = time.time()

if not os.path.exists(".env"):
    setup()

logger.info("Starting Cleanup of previous outputs")
cleanup()
logger.info("Cleanup completed")

logger.info("Starting Unpack process")
unpack = subprocess.Popen("cd Unpack && python main.py", shell=True)
unpack.wait()
logger.info("Unpack completed.")


render = subprocess.Popen("cd Render && python render.py", shell=True)
render.wait()
logger.info("Render process completed")

def update_chart_info():
    logger.info("Updating chart information")
    os.remove("data/Chart_info.json")
    os.rename("data/Chart_info_New.json", "data/Chart_info.json")
    logger.info("Chart information updated")

update_chart_info()

endtime = time.time()
logger.info("Total time taken: %.2f seconds", endtime - starttime)