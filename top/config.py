
import os

__4B_RASPI_IP = '192.168.137.101'
__HTTP_PORT = 5000

"""
顺序：
前置摄像头
双目摄像头
后置摄像头
"""
# 更换成流的url
__STREAM_URL = [
    # "http://192.168.137.100:5000/video_feed0",
    # "http://192.168.137.100:5000/video_feed1",
    # "http://192.168.137.100:5000/video_feed2"
    "http://localhost:8081",
    "http://192.168.137.101:5000/video_feed1",
    "http://192.168.137.101:5000/video_feed2"

]

# 字典

__CAM_CONFIGS = [
    {
        # 是否正在记录 戳
        "is_recording": False,
        # 视频写入流
        "video_writer": None,
        # 名称
        # 子文件夹同name
        "name": "front",
        # 帧率
        "fps": 30.0,
        # 分辨率
        "resolution": (40, 30),

        "is_active": True,

        "last_frame": None,
    },
    {
        "is_recording": False,
        "video_writer": None,
        "name": "two",
        "fps": 30.0,
        "resolution": (40, 30),

        "is_active": True,

        "last_frame": None,
    },
    {
        "is_recording": False,
        "video_writer": None,
        "name": "under",
        "fps": 30.0,
        
        "resolution": (40, 30),
        
        "is_active": True,
        
        "last_frame": None,
    },
]

# 用于存放录像的根目录
__RECORD_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "RaspberryPiRecordings")

# 不同摄像头分文件夹存放
__SON_PATH = ["front", "two", "under"]
