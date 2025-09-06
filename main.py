import subprocess
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

starttime = time.time()

logger.info("Starting Unpack process")
unpack = subprocess.Popen("cd Unpack && python main.py", shell=True)
unpack.wait()
logger.info("Unpack completed, copying output to Render/input")


render = subprocess.Popen("cd Render && python render.py", shell=True)
render.wait()
logger.info("Render process completed")

endtime = time.time()
logger.info("Total time taken: %.2f seconds", endtime - starttime)