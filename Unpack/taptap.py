import hashlib
from http.client import HTTPSConnection
import json
import random
import string
import time
import urllib.parse
import uuid
import hashlib
import logging

sample = string.ascii_lowercase + string.digits

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def taptap(appid):
    logger.info("Starting taptap function with appid: %d", appid)
    uid = uuid.uuid4()
    logger.debug("Generated UID: %s", uid)
    X_UA = "V=1&PN=TapTap&VN=2.40.1-rel.100000&VN_CODE=240011000&LOC=CN&LANG=zh_CN&CH=default&UID=%s&NT=1&SR=1080x2030&DEB=Xiaomi&DEM=Redmi+Note+5&OSV=9" % uid

    conn = HTTPSConnection("api.taptapdada.com")
    conn.request(
        "GET",
        "/app/v2/detail-by-id/%d?X-UA=%s" % (appid, urllib.parse.quote(X_UA)),
        headers={"User-Agent": "okhttp/3.12.1"}
    )
    r = json.load(conn.getresponse())
    version = r["data"]["download"]['apk']["version_code"]
    apkid = r["data"]["download"]["apk_id"]
    md5_apk = r["data"]["download"]['apk']["md5"]

    nonce = "".join(random.sample(sample, 5))
    t = int(time.time())
    param = "abi=arm64-v8a,armeabi&id=%d&node=%s&nonce=%s&sandbox=1&screen_densities=xhdpi&time=%s" % (apkid, uid, nonce, t)
    byte = "X-UA=%s&%sPeCkE6Fu0B10Vm9BKfPfANwCUAn5POcs" % (X_UA, param)
    md5 = hashlib.md5(byte.encode()).hexdigest()
    body = "%s&sign=%s" % (param, md5)

    conn.request(
        "POST",
        "/apk/v1/detail?X-UA=" + urllib.parse.quote(X_UA),
        body=body.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "okhttp/3.12.1"}
    )
    r = json.load(conn.getresponse())
    url = r['data']['apk']['download']
    logger.info("Successfully fetched download URL and MD5")
    # 只返回信息，不下载
    return url, md5_apk, version

# Phigros app id = 165287
def main():
    logger.info("Starting main function")
    url, md5_apk, version = taptap(165287)
    # 只返回信息，不下载
    return url, md5_apk, version

if __name__ == "__main__":
    main()