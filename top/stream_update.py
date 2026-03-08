import cv2
import requests
import numpy as np
import base64

def update_video_stream(stream_url, video_image, status_text, page, cam_config):
        print("woc!")
        bytes_buffer = b""
        try:
            # 长连接获取视频流
            response = requests.get(stream_url, stream=True, timeout=5)
            if response.status_code != 200:
                status_text.value = f"连接失败：{response.status_code}"
                page.update()
                return
            

            status_text.value = "视频流连接成功" + cam_config["name"]
            page.update()

            for chunk in response.iter_content(chunk_size=1024):

                if not chunk:
                    break

                bytes_buffer += chunk

                # 解析multipart分块
                boundary = b"--frame\r\n"
                if boundary in bytes_buffer:
                    parts = bytes_buffer.split(boundary)
                    bytes_buffer = parts[-1]
                    for part in parts[:-1]:
                        if part:
                            header_end = part.find(b"\r\n\r\n")
                            if header_end != -1:
                                jpeg_data = part[header_end + 4:]
                                frame = cv2.imdecode(
                                    np.frombuffer(jpeg_data, np.uint8), cv2.IMREAD_COLOR
                                )
                                if frame is not None:
                                    _, buffer = cv2.imencode(".jpg", frame)
                                    video_image.src_base64 = base64.b64encode(buffer).decode()
                                    page.update()
                                    # 缓存帧
                                    cam_config["latest_frame"] = frame.copy()

                                    # 录制时写入视频
                                    if cam_config["is_recording"] and cam_config["video_writer"] is not None:
                                        cam_config["video_writer"].write(frame)
        except Exception as e:
            status_text.value = f"连接异常：{str(e)}"
            page.update()
