import flet as ft
import os
import cv2
import threading
import time
from datetime import datetime
from recorder import VideoRecorder
from stream_update import update_video_stream
from config import __CAM_CONFIGS, __RECORD_DIR, __STREAM_URL
from control_server import start_control_server
from status_dash_board import status_board

# 生成视频编码格式标准
fourcc = cv2.VideoWriter.fourcc(*"mp4v")

def main(page: ft.Page):
    
    # ========== 0. 深度仪表板 ==========
    status_panel = status_board(page)
    status_board_container = status_panel.get_panel()

    # ========== 1. 基础配置 ==========
    page.title = "树莓派监控"
    page.window_width = 1960
    page.window_height = 1080
    page.padding = 0
    page.theme_mode = "system"

    # ========== 2. 创建视频组件 ==========
    video_image = [
        ft.Image(
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
            width=1440,
            height=960,
        ),
        ft.Image(
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
            width=1920,
            height=540,
        ),
        ft.Image(
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
            width=1440,
            height=960,
        ),
    ]

    # ========== 3. 状态栏列表 ==========
    status_text = [
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
    ]
    
    # ========== 4. 视频播放器列表 ==========
    video_players = []
    video_widgets = []
    
    # 创建视频播放器并更新状态
    for i in range(3):
        player = update_video_stream(
            stream_url=__STREAM_URL[i],
            video_widget=video_image[i],
            status_text=status_text[i],  # 传入状态文本，会自动更新
            page=page,
            cam_config=__CAM_CONFIGS[i]
        )
        video_players.append(player)
        video_widgets.append(player.get_widget())
    
    # 手动更新一次状态（确保显示）
    for i in range(3):
        status_text[i].value = "视频流已连接"
    page.update()
    
    # ========== 5. 录制器（临时用前置摄像头测试）==========
    recorder = None
    
    # 状态回调函数
    def make_status_callback(cam_index):
        def callback(msg):
            status_text[cam_index].value = msg
            page.update()
        return callback
    
    # 启动录制器（使用前置摄像头，索引0）
    def init_recorder():
        nonlocal recorder
        try:
            recorder = VideoRecorder(
                stream_url=__STREAM_URL[1],      # 前置摄像头
                cam_config=__CAM_CONFIGS[1],     # 前置配置
                status_callback=make_status_callback(1)
            )
            recorder.start()
            status_text[1].value = "录制器已启动"
            page.update()
        except Exception as e:
            status_text[1].value = f"录制器启动失败: {str(e)}"
            page.update()
    
    # 在后台线程启动录制器
    threading.Thread(target=init_recorder, daemon=True).start()
    
    # ========== 6. 录制按钮逻辑 ==========
    def toggle_recording(e):
        """控制前置摄像头录制"""
        print("按钮被点击")  # 调试输出
        
        config = __CAM_CONFIGS[0]  # 前置摄像头
        
        print(f"录制状态: {config['is_recording']}")  # 调试输出
        print(f"last_frame存在: {config.get('last_frame') is not None}")  # 调试输出
        
        record_path = os.path.join(__RECORD_DIR, config["name"])
        
        if not config["is_recording"]:
            # 开始录制
            if config.get("last_frame") is None:
                status_text[0].value = "尚未接收到画面，无法录制"
                page.update()
                return
            
            height, width = config["last_frame"].shape[:2]
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            
            # 创建目录
            os.makedirs(record_path, exist_ok=True)
            file_path = os.path.join(record_path, f"video_{timestamp}.mp4")
            
            # 创建 VideoWriter
            config["video_writer"] = cv2.VideoWriter(
                file_path, 
                fourcc, 
                config.get("fps", 30), 
                (width, height)
            )
            config["current_file"] = file_path
            
            if config["video_writer"].isOpened():
                config["is_recording"] = True
                
                # 更新所有按钮
                for btn in record_button:
                    btn.text = "停止录制"
                    btn.bgcolor = ft.colors.RED_500
                
                status_text[0].value = f"正在录制... 保存到: {os.path.basename(file_path)}"
                print(f"开始录制: {file_path}")  # 调试输出
            else:
                status_text[0].value = "录制初始化失败"
                config["video_writer"] = None
                print("录制初始化失败")  # 调试输出
        else:
            # 停止录制
            config["is_recording"] = False
            
            if config["video_writer"]:
                config["video_writer"].release()
                config["video_writer"] = None
            
            # 更新所有按钮
            for btn in record_button:
                btn.text = "开始录制"
                btn.bgcolor = "#39C5BB"
            
            status_text[0].value = "录制完成"
            
            # 显示保存路径
            page.snack_bar = ft.SnackBar(
                ft.Text(f"视频已保存至：{config.get('current_file', record_path)}"),
                duration=3000
            )
            page.snack_bar.open = True
            print(f"停止录制: {config.get('current_file')}")  # 调试输出
        
        page.update()

    # ========== 7. 按钮列表 ==========
    record_button = [
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
    ]

    # ========== 8. 屏幕布局 ==========
    screen1 = ft.Container(
        content=ft.Stack(
            [
                video_widgets[0],
                ft.Container(
                    content=ft.Column(
                        controls=[record_button[0], status_text[0]],
                        alignment=ft.MainAxisAlignment.END,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=10,
                    ),
                    bottom=20,
                    right=20,
                    width=200,
                    height=100,
                ),
            ],
        ),
        expand=True,
        alignment=ft.alignment.center,
        visible=True
    )

    screen2 = ft.Container(
        content=ft.Stack(
            [
                video_widgets[1],
                ft.Container(
                    content=ft.Column(
                        controls=[record_button[1], status_text[1]],
                        alignment=ft.MainAxisAlignment.END,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=10,
                    ),
                    bottom=20,
                    right=20,
                    width=200,
                    height=100,
                ),
            ],
        ),
        expand=True,
        alignment=ft.alignment.center,
        visible=False
    )

    screen3 = ft.Container(
        content=ft.Stack(
            [
                video_widgets[2],
                ft.Container(
                    content=ft.Column(
                        controls=[record_button[2], status_text[2]],
                        alignment=ft.MainAxisAlignment.END,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=10,
                    ),
                    bottom=20,
                    right=20,
                    width=200,
                    height=100,
                ),
            ],
        ),
        expand=True,
        alignment=ft.alignment.center,
        visible=False
    )

    # ========== 9. 页面切换逻辑 ==========
    def switch_screen(screen_num: int):
        screen1.visible = (screen_num == 1)
        screen2.visible = (screen_num == 2)
        screen3.visible = (screen_num == 3)
        page.update()

    # ========== 10. 底部导航栏 ==========
    bottom_nav = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.SCREENSHOT_MONITOR, label="前置摄像头"),
            ft.NavigationDestination(icon=ft.icons.CAMERA_FRONT, label="双目摄像头"),
            ft.NavigationDestination(icon=ft.icons.BORDER_BOTTOM, label="底部摄像头")
        ],
        on_change=lambda e: switch_screen(e.control.selected_index + 1),
        selected_index=0
    )

    # ========== 11. 组装页面 ==========
    screen_stack = ft.Stack([screen1, screen2, screen3], expand=True)
    
    page.add(
        ft.Stack(
            [
                ft.Column([screen_stack, bottom_nav], expand=True, spacing=0),
                ft.Container(content=status_board_container, top=10, right=10)
            ],
            expand=True
        )
    )
    
    # ========== 12. 启动控制服务器（可选）==========
    try:
        threading.Thread(target=start_control_server, args=(status_panel,), daemon=True).start()
        status_panel.set_controller_status("手柄线程已启动\r\n正在连接控制服务器...")
    except Exception as e:
        status_panel.set_controller_status(f"手柄线程启动失败\r\n{e}")

    # ========== 13. 页面关闭时清理资源 ==========
    def on_close(e):
        print("正在清理资源...")
        
        # 停止所有视频播放器
        for player in video_players:
            player.stop()
        
        # 停止录制器
        if recorder:
            recorder.stop()
        
        # 释放 video_writer
        if __CAM_CONFIGS[0].get("video_writer"):
            __CAM_CONFIGS[0]["video_writer"].release()
        
        print("清理完成")
    
    page.on_close = on_close
    
    # 延迟检查录制器状态
    def check_recorder_status():
        time.sleep(2)
        if __CAM_CONFIGS[0].get("last_frame") is not None:
            status_text[0].value = "就绪，可录制"
        else:
            status_text[0].value = "等待画面..."
        page.update()
    
    threading.Thread(target=check_recorder_status, daemon=True).start()

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
    )