import flet as ft
import threading
import time
import base64
import requests
import cv2
import numpy as np
from collections import deque

class SmoothVideoPlayer:
    """平滑视频播放器 - 支持画面旋转"""
    
    def __init__(self, snapshot_url, width, height, fps=20, rotate=0):
        self.snapshot_url = snapshot_url
        self.width = width
        self.height = height
        self.fps = fps
        self.rotate = rotate  # 正确接收 rotate 参数
        self.is_running = True
        self.frame_count = 0
        
        self.current_image = ft.Image(
            width=width,
            height=height,
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
        )
        
        self.switcher = ft.AnimatedSwitcher(
            content=self.current_image,
            duration=50,
            switch_in_curve=ft.AnimationCurve.EASE_IN,
            switch_out_curve=ft.AnimationCurve.EASE_OUT,
        )
        
        self.frame_queue = deque(maxlen=2)
        self.session = requests.Session()
        
    def get_widget(self):
        return self.switcher
    
    def start(self):
        threading.Thread(target=self._fetch_loop, daemon=True).start()
        threading.Thread(target=self._update_loop, daemon=True).start()
    
    def _rotate_image(self, image_data):
        """旋转图片"""
        if self.rotate == 0:
            return image_data
        
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return image_data
            
            if self.rotate == 90:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotate == 180:
                img = cv2.rotate(img, cv2.ROTATE_180)
            elif self.rotate == 270:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            _, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return encoded.tobytes()
            
        except Exception as e:
            print(f"旋转失败: {e}")
            return image_data
    
    def _fetch_loop(self):
        """获取图片线程"""
        while self.is_running:
            try:
                url = f"{self.snapshot_url}?t={time.time()}"
                resp = self.session.get(url, timeout=0.5)
                
                if resp.status_code == 200:
                    if self.rotate != 0:
                        rotated_data = self._rotate_image(resp.content)
                        self.frame_queue.append(rotated_data)
                    else:
                        self.frame_queue.append(resp.content)
            except Exception:
                pass
            
            time.sleep(1 / self.fps)
    
    def _update_loop(self):
        """更新UI线程"""
        last_frame = None
        
        while self.is_running:
            if self.frame_queue:
                frame_data = self.frame_queue[-1]
                
                if frame_data != last_frame:
                    last_frame = frame_data
                    self.frame_count += 1
                    
                    b64_str = base64.b64encode(frame_data).decode()
                    
                    new_image = ft.Image(
                        src_base64=b64_str,
                        width=self.width,
                        height=self.height,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=ft.border_radius.all(10),
                    )
                    
                    self.switcher.content = new_image
                    self.switcher.update()
            
            time.sleep(1 / self.fps)
    
    def stop(self):
        self.is_running = False
        self.session.close()


def update_video_stream(stream_url, video_widget, status_text, page, cam_config, rotate=None):
    """
    创建视频播放器
    
    Args:
        stream_url: 流地址
        video_widget: 视频组件
        status_text: 状态文本
        page: 页面对象
        cam_config: 配置（包含 id）
        rotate: 旋转角度，如果为 None 则根据 id 自动判断
    """
    snapshot_url = stream_url.replace('/stream', '/snapshot')
    
    width = video_widget.width if video_widget.width else 800
    height = video_widget.height if video_widget.height else 600
    
    # 自动判断旋转角度
    if rotate is None:
        cam_id = cam_config.get("id", 0)
        if cam_id == 1:  # 前置摄像头 (id=1)
            rotate = 180
        else:
            rotate = 0
    
    # 正确传递 rotate 参数
    player = SmoothVideoPlayer(snapshot_url, width, height, fps=20, rotate=rotate)
    player.start()
    
    if status_text:
        status_text.value = f"视频流连接成功" + (f" (旋转{rotate}°)" if rotate else "")
        page.update()
    
    return player