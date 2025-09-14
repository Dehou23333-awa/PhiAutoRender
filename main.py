import subprocess
import logging
import time

def cleanup():
    """清理之前的输出文件和临时文件"""
    subprocess.run("rd /s /q Render\\output", shell=True)
    subprocess.run("rd /s /q Render\\temp", shell=True)
    subprocess.run("rd /s /q Upload\\Covers", shell=True)
    subprocess.run("rd /s /q Upload\\Covers", shell=True)
    subprocess.run("rd /s /q Unpack\\output", shell=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

starttime = time.time()

logger.info("Starting Cleanup of previous outputs")
cleanup()
logger.info("Cleanup completed")

logger.info("Starting Unpack process")
unpack = subprocess.Popen("cd Unpack && python main.py", shell=True)
unpack.wait()
logger.info("Unpack completed, copying output to Render/input")


# render = subprocess.Popen("cd Render && python render.py", shell=True)
# render.wait()
# logger.info("Render process completed")

# endtime = time.time()
# logger.info("Total time taken: %.2f seconds", endtime - starttime)