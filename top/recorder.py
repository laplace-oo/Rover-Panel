import cv2
import numpy as np
import threading
import time
from datetime import datetime
import os

class VideoRecorder:
    def __init__(self, stream_url, cam_config, status_callback=None):
        self.stream_url = stream_url
        self.cam_config = cam_config
        self.status_callback = status_callback
        self.is_running = True
        self.cap = None  # 只连接一次
        
    def start(self):
        """启动录制线程"""
        self.cap = cv2.VideoCapture(self.stream_url)
        if not self.cap.isOpened():
            if self.status_callback:
                self.status_callback("无法打开视频流")
            return
        
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
    
    def _record_loop(self):
        while self.is_running and self.cam_config.get('is_active', True):
            ret, frame = self.cap.read()
            
            if not ret:
                time.sleep(0.01)
                continue
            
            # 更新最后一帧
            self.cam_config['last_frame'] = frame
            
            # 如果需要录制
            if self.cam_config.get('is_recording', False):
                if self.cam_config.get('video_writer'):
                    self.cam_config['video_writer'].write(frame)
    
    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()