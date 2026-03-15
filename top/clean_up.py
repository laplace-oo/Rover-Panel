import threading
import time
import signal
import sys
import os
import cv2
from config import __CAM_CONFIGS

# 尝试从stream_update导入全局变量
try:
    from stream_update import latest_jpg_list, stream_threads
except ImportError:
    # 如果导入失败，创建默认值
    latest_jpg_list = [None, None, None]
    stream_threads = []

# 停止标志
stop_flag = False


def stop_all_cameras():
    """停止所有摄像头的活动状态"""
    for config in __CAM_CONFIGS:
        config["is_active"] = False
    print("✓ 已停止所有摄像头活动状态")


def release_video_writers():
    """释放所有VideoWriter资源"""
    released = 0
    for config in __CAM_CONFIGS:
        if config["video_writer"] is not None:
            try:
                config["video_writer"].release()
                config["video_writer"] = None
                released += 1
                print(f"✓ 已释放 {config['name']} 的录制资源")
            except Exception as e:
                print(f"✗ 释放 {config['name']} 失败: {e}")
    
    if released == 0:
        print("✓ 没有活动的视频写入器需要释放")
    return released


def clear_frame_buffer():
    """清除帧缓冲区"""
    for i in range(len(latest_jpg_list)):
        latest_jpg_list[i] = None
    print("✓ 已清除帧缓冲区")


def wait_for_threads(timeout=2):
    """等待所有线程结束"""
    if not stream_threads:
        print("✓ 没有活跃的线程")
        return
    
    print(f"等待 {len(stream_threads)} 个线程结束...")
    
    alive_threads = []
    for thread in stream_threads:
        if thread.is_alive():
            alive_threads.append(thread)
    
    if alive_threads:
        for thread in alive_threads:
            thread.join(timeout=timeout)
            if thread.is_alive():
                print(f"⚠ 线程 {thread.name} 未在 {timeout} 秒内结束")
            else:
                print(f"✓ 线程已结束")
    
    # 清空线程列表
    stream_threads.clear()
    print("✓ 已清空线程列表")


def cleanup_and_exit(signum=None, frame=None):
    """清理资源并退出程序"""
    global stop_flag
    
    if stop_flag:
        print("\n正在强制退出...")
        sys.exit(1)
    
    stop_flag = True
    print("\n" + "="*40)
    print("开始清理资源...")
    print("="*40)
    
    # 1. 停止所有摄像头
    stop_all_cameras()
    time.sleep(0.1)  # 给线程一点时间响应
    
    # 2. 释放VideoWriter
    release_video_writers()
    
    # 3. 清除帧缓冲区
    clear_frame_buffer()
    
    # 4. 等待线程结束
    wait_for_threads(timeout=2)
    
    print("="*40)
    print("清理完成，程序退出")
    print("="*40)
    sys.exit(0)


def register_cleanup_handlers():
    """注册清理信号处理器"""
    # 注册Ctrl+C处理
    signal.signal(signal.SIGINT, cleanup_and_exit)
    # 注册终止信号处理
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    print("已注册清理处理器 (Ctrl+C 可安全退出)")


def cleanup_in_main():
    """在主函数中使用的简单清理函数"""
    print("\n正在清理资源...")
    
    # 停止摄像头
    for config in __CAM_CONFIGS:
        config["is_active"] = False
    
    time.sleep(0.2)  # 等待线程响应
    
    # 释放VideoWriter
    for config in __CAM_CONFIGS:
        if config["video_writer"] is not None:
            try:
                config["video_writer"].release()
                config["video_writer"] = None
                print(f"已释放 {config['name']}")
            except:
                pass
    
    print("清理完成")


# 如果直接运行此脚本，执行清理
if __name__ == "__main__":
    cleanup_and_exit()