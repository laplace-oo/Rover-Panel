import cv2
import requests
import numpy as np
import base64
import time

def update_video_stream(stream_url, video_image, status_text, page, cam_config):
    print("视频流启动!")
    bytes_buffer = b""
    boundary = b"--frame\r\n"
    
    # ⭐ 新增：帧率控制
    last_update_time = 0
    update_interval = 1/30  # 30fps显示限制
    
    try:
        # 长连接获取视频流
        response = requests.get(stream_url, stream=True, timeout=5)
        if response.status_code != 200:
            status_text.value = f"连接失败：{response.status_code}"
            page.update()
            return

        status_text.value = "视频流连接成功" + cam_config["name"]
        page.update()

        for chunk in response.iter_content(chunk_size=4096):  # 增大chunk减少循环
            if not chunk:
                break

            bytes_buffer += chunk

            # 解析multipart分块
            if boundary in bytes_buffer:
                parts = bytes_buffer.split(boundary)
                bytes_buffer = parts[-1]  # 保留不完整部分
                
                for part in parts[:-1]:  # 处理所有完整帧
                    if part:
                        header_end = part.find(b"\r\n\r\n")
                        if header_end != -1:
                            # ⭐ 关键优化1：直接使用原始JPEG数据
                            jpeg_data = part[header_end + 4:]
                            
                            # ⭐ 关键优化2：只解码需要处理的帧
                            # 录制需要解码成OpenCV格式
                            if cam_config["is_recording"] and cam_config["video_writer"] is not None:
                                frame = cv2.imdecode(
                                    np.frombuffer(jpeg_data, np.uint8), 
                                    cv2.IMREAD_COLOR
                                )
                                if frame is not None:
                                    cam_config["video_writer"].write(frame)
                                    cam_config["latest_frame"] = frame  # 直接赋值，不用copy()
                            
                            # ⭐ 关键优化3：显示直接用JPEG转Base64，避免编解码
                            current_time = time.time()
                            if current_time - last_update_time > update_interval:
                                # 直接使用原始JPEG转Base64
                                video_image.src_base64 = base64.b64encode(jpeg_data).decode()
                                page.update()
                                last_update_time = current_time
                            
    except Exception as e:
        status_text.value = f"连接异常：{str(e)}"
        page.update()