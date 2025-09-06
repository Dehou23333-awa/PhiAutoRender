import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
import os
from queue import Queue
import sys
import threading
import time
from UnityPy import Environment
from UnityPy.classes import AudioClip
from UnityPy.enums import ClassIDType
from zipfile import ZipFile
from fsb5 import FSB5
from fsb5 import vorbis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ByteReader:
    """
    用于按特定格式读取字节数据的辅助类。
    """
    def __init__(self, data):
        self.data = data
        self.position = 0

    def readInt(self):
        self.position += 4
        return self.data[self.position - 4] ^ self.data[self.position - 3] << 8 ^ self.data[self.position - 2] << 16


# 用于异步文件I/O的队列
queue_in = Queue()


def io():
    logging.info("Starting I/O thread")
    """
    在单独的线程中处理文件写入操作，避免I/O阻塞。
    """
    while True:
        item = queue_in.get()
        if item is None:
            logging.info("I/O thread received termination signal")
            break
        else:
            path, resource = item
            if isinstance(resource, BytesIO):
                with resource:
                    with open(path, "wb") as f:
                        f.write(resource.getbuffer())
            else:
                with open(path, "wb") as f:
                    f.write(resource)


def save_image(path, image):
    """
    将图像数据放入BytesIO并提交到I/O队列。
    """
    bytesIO = BytesIO()
    image.save(bytesIO, "png")
    queue_in.put((path, bytesIO))


def save_music(path, music: AudioClip):
    """
    从AudioClip中提取音频数据，重建为.ogg文件并提交到I/O队列。
    """
    fsb = FSB5(music.m_AudioData)
    # 假设总是处理第一个样本
    rebuilt_sample = fsb.rebuild_sample(fsb.samples[0])
    queue_in.put((path, rebuilt_sample))


# 定义需要从Unity资源文件中过滤的对象类型
# 原始代码中的TextAsset, Sprite, AudioClip是必须的
classes = (ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip)


def save(key, entry, pool):
    """
    分析资源键（key），判断资源类型并提交给相应的保存函数。
    此函数已重构，仅保留处理谱面、音乐和高清曲绘的逻辑。
    """
    # 过滤并读取对象，此逻辑未作更改
    obj = entry.get_filtered_objects(classes)
    obj = next(obj).read()

    # 检查是否为谱面文件
    if key[-14:-7] == "/Chart_" and key[-5:] == ".json":
        chart_id = key[:-14]
        p = os.path.join("chart", chart_id)
        if not os.path.exists(p):
            # 在主线程中创建目录是安全的
            os.makedirs(p, exist_ok=True)
        chart_path = os.path.join("chart", chart_id, f"{key[-7:-5]}.json")
        queue_in.put((chart_path, obj.script))

    # 检查是否为高清曲绘
    elif key[-19:-3] == ".0/Illustration.":
        song_id = key[:-19]
        illustration_path = os.path.join("illustration", f"{song_id}.png")
        pool.submit(save_image, illustration_path, obj.image)

    # 检查是否为音乐文件
    elif key[-12:] == ".0/music.wav":
        song_id = key[:-12]
        music_path = os.path.join("music", f"{song_id}.ogg")
        pool.submit(save_music, music_path, obj)


def run(path):
    logging.info("Starting unpack process for: %s", path)
    """
    主解包流程函数。
    负责读取APK，解析catalog.json，并分派任务进行解包。
    """
    # 创建输出目录
    os.makedirs("music", exist_ok=True)
    os.makedirs("chart", exist_ok=True)
    os.makedirs("illustration", exist_ok=True)
    logging.info("Output directories created")

    logging.info("Parsing catalog.json")
    with ZipFile(path) as apk:
        with apk.open("assets/aa/catalog.json") as f:
            data = json.load(f)

    key = base64.b64decode(data["m_KeyDataString"])
    bucket = base64.b64decode(data["m_BucketDataString"])
    entry = base64.b64decode(data["m_EntryDataString"])

    table = []
    reader = ByteReader(bucket)
    for x in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        if key_type == 0:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode()
        elif key_type == 1:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode("utf16")
        elif key_type == 4:
            key_value = key[key_position]
        else:
            raise BaseException(f"Unknown key type at position {key_position}: {key_type}")
        
        entry_value_final = -1
        for i in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_data_raw = entry[4 + 28 * entry_position : 4 + 28 * entry_position + 28]
            entry_value_final = entry_data_raw[8] ^ entry_data_raw[9] << 8
        table.append([key_value, entry_value_final])

    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]

    for i in range(len(table) - 1, -1, -1):
        # 简化了过滤条件，因为不再关心avatar
        if type(table[i][0]) == int or table[i][0].startswith("Assets/Tracks/#") or not table[i][0].startswith("Assets/Tracks/"):
            del table[i]
        elif table[i][0].startswith("Assets/Tracks/"):
            table[i][0] = table[i][0][14:]
    # --- catalog.json解析逻辑结束 ---

    # 启动文件I/O线程
    io_thread = threading.Thread(target=io)
    io_thread.start()

    ti = time.time()

    # 使用线程池处理CPU密集型任务（图像和音频转换）
    with ThreadPoolExecutor(max_workers=6) as pool:
        logging.info("Starting asset processing")
        # 原始代码中的完整解包逻辑，移除了与UPDATE配置相关的if/else分支
        with ZipFile(path) as apk:
            for key, bundle_hash in table:
                # 读取Unity资源包
                asset_data = apk.read(f"assets/aa/Android/{bundle_hash}")
                env = Environment()
                env.load_file(asset_data, name=key)
                
                # 遍历资源包内的文件并进行保存
                for internal_key, internal_entry in env.files.items():
                    save(internal_key, internal_entry, pool)

    # 所有任务已提交，向I/O队列发送结束信号
    queue_in.put(None)
    # 等待I/O线程完成所有文件写入
    io_thread.join()
    logging.info("All assets processed successfully")
    logging.info("Unpack process completed")