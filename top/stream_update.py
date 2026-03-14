import cv2
import requests
import numpy as np
import base64
import time

# 最简单的硬件加速配置
cv2.setNumThreads(4)  # 启用多线程
cv2.setUseOptimized(True)  # 启用OpenCV优化


def update_video_stream(stream_url, video_image, status_text, page, cam_config):
    print("视频流启动!")
    bytes_buffer = b""
    try:
        response = requests.get(stream_url, stream=True, timeout=5)
        if response.status_code != 200:
            status_text.value = f"连接失败：{response.status_code}"
            page.update()
            return
        else:
            status_text.value = "视频流连接成功" + cam_config["name"]
            page.update()

        for chunk in response.iter_content(chunk_size=8192):  # 增大chunk减少循环
            if not cam_config.get('is_active', True):
                break
            if not chunk:
                break

            bytes_buffer += chunk

            a = bytes_buffer.find(b'\xff\xd8')
            b = bytes_buffer.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg_data = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:]

                # 唯一改动：使用IMREAD_UNCHANGED加速解码
                frame = cv2.imdecode(
                    np.frombuffer(jpg_data, np.uint8), 
                    cv2.IMREAD_UNCHANGED  # 比IMREAD_COLOR更快
                )

                if frame is not None:

                    if cam_config["is_recording"] and cam_config["video_writer"]:
                        cam_config["video_writer"].write(frame)

                    video_image.src_base64 = base64.b64encode(jpg_data).decode()
                    video_image.update()
                            
    except Exception as e:
        status_text.value = f"连接异常：{str(e)}"
        page.update()