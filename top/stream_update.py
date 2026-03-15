import cv2
import requests
import numpy as np
import time
import threading
import psutil
import os


# OpenCV优化
cv2.setNumThreads(4)
cv2.setUseOptimized(True)

# 全局变量，每个摄像头独立
latest_jpg_list = [None, None, None]
stream_threads = []

def set_thread_affinity_psutil(thread_name, core_id):
    """使用psutil设置CPU亲和性（跨平台）"""
    try:
        proc = psutil.Process()
        # 获取当前CPU亲和性
        current_affinity = proc.cpu_affinity()
        print(f"{thread_name} 当前可用核心: {current_affinity}")
        
        # 设置到指定核心
        proc.cpu_affinity([core_id])
        print(f"{thread_name} 已绑定到核心 {core_id}")
        
        # 验证
        new_affinity = proc.cpu_affinity()
        print(f"{thread_name} 绑定后可用核心: {new_affinity}")
    except Exception as e:
        print(f"设置CPU亲和性失败: {e}")

def mjpeg_stream_thread(stream_url, cam_index, cam_config):
    """网络接收线程 - 绑定到核心0"""
    # 绑定到核心0（低负载）
    set_thread_affinity_psutil("网络线程", 0)

    bytes_buffer = bytearray()

    try:
        response = requests.get(stream_url, stream=True, timeout=5)
        
        if response.status_code != 200:
            print(f"摄像头{cam_config['name']}连接失败：{response.status_code}")
            return

        for chunk in response.iter_content(chunk_size=4096):
            if not cam_config.get("is_active", True):
                break

            if not chunk:
                continue

            bytes_buffer.extend(chunk)

            # 查找JPEG起始和结束标记
            a = bytes_buffer.find(b"\xff\xd8")  # JPEG开始
            b = bytes_buffer.find(b"\xff\xd9")  # JPEG结束

            if a != -1 and b != -1 and b > a:
                jpg = bytes(bytes_buffer[a:b + 2])
                del bytes_buffer[:b + 2]
                
                # 保存最新帧
                latest_jpg_list[cam_index] = jpg

    except Exception as e:
        print(f"摄像头{cam_config['name']}异常：{str(e)}")


def update_video_stream(stream_url, video_image, status_text, page, cam_config):
    """视频处理线程 - 绑定到核心1（或更高）"""
    # 获取摄像头索引
    cam_index = 0 if cam_config["name"] == "front" else 1 if cam_config["name"] == "two" else 2
    
    # 绑定到核心1（计算负载）
    set_thread_affinity_psutil(f"处理线程-{cam_config['name']}", 1 + cam_index)
    
    print(f"摄像头{cam_config['name']}视频流处理线程启动")

    # 启动网络接收线程
    thread = threading.Thread(
        target=mjpeg_stream_thread,
        args=(stream_url, cam_index, cam_config),
        daemon=True
    )
    thread.start()
    stream_threads.append(thread)

    while cam_config.get("is_active", True):
        latest_jpg = latest_jpg_list[cam_index]
        
        if latest_jpg is None:
            time.sleep(0.001)
            continue

        # 录制时才解码
        if cam_config.get("is_recording", False) and cam_config.get("video_writer"):
            frame = cv2.imdecode(
                np.frombuffer(latest_jpg, np.uint8),
                cv2.IMREAD_COLOR
            )
            if frame is not None:
                cam_config["video_writer"].write(frame)
        
        # 不加帧率限制，让CPU尽量快地处理
        # 但加个小sleep避免CPU占用过高
        time.sleep(0.001)
     # 线程结束时释放资源
    if cam_config["video_writer"] is not None:
        cam_config["video_writer"].release()
        cam_config["video_writer"] = None   
    print(f"摄像头{cam_config['name']}视频流处理线程结束")