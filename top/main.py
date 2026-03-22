import flet as ft
import os
import cv2
import threading
from datetime import datetime
from recorder import VideoRecorder  # 改用新的录制器
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

    # ========== 2. 定义三个屏幕的内容 ==========
    
    # 【关键修改】改用直接URL显示，不再需要base64
    video_image = [
        ft.Image(
            src=__STREAM_URL[0],  # 直接使用URL
            fit=ft.ImageFit.CONTAIN,  # 保持比例，避免模糊
            border_radius=ft.border_radius.all(10),
            width=1440,
            height=960,
            rotate=ft.Rotate(angle=180),
        ),
        ft.Image(
            src=__STREAM_URL[1],
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
            width=1920,
            height=540,
        ),
        ft.Image(
            src=__STREAM_URL[2],
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
            width=1440,
            height=960,
        ),
    ]

    # 状态栏列表
    status_text = [
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ft.Text("等待连接视频流...", color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
    ]
    
    # 更新状态文本的回调函数
    def make_status_callback(cam_index):
        def callback(msg):
            status_text[cam_index].value = msg
            page.update()
        return callback
    
    #只需要双目来录视频
    recorder = VideoRecorder(
        stream_url=__STREAM_URL[1],      # 双目摄像头的流地址
        cam_config=__CAM_CONFIGS[1],     # 双目摄像头的配置
        status_callback=make_status_callback(1)
    )
    recorder.start()
    
    # 录制按钮的逻辑函数
    def toggle_recording(e):
        """只控制双目摄像的录制"""
        config = __CAM_CONFIGS[1]  # 直接取双目配置
        
        # 存放录像的完整路径
        record_path = os.path.join(__RECORD_DIR, config["name"])
        
        # 开始录制
        if not config["is_recording"]:
            # 检查是否有最后一帧
            if config.get("last_frame") is None:
                status_text[1].value = "尚未接收到画面，无法录制"
                page.update()
                return
            
            height, width = config["last_frame"].shape[:2]
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            
            # 创建目录
            os.makedirs(record_path, exist_ok=True)
            
            file_path = os.path.join(record_path, f"video_{timestamp}.mp4")
            
            # 创建VideoWriter
            config["video_writer"] = cv2.VideoWriter(
                file_path, 
                fourcc, 
                config.get("fps", 30), 
                (width, height)
            )
            
            if config["video_writer"].isOpened():
                config["is_recording"] = True
                config["current_file"] = file_path
                record_button[1].text = "停止录制"
                record_button[1].bgcolor = ft.colors.RED_500
                status_text[1].value = "正在录制..."
            else:
                status_text[1].value = "录制初始化失败"
                config["video_writer"] = None
        else:
            # 停止录制
            config["is_recording"] = False
            config["video_writer"].release()
            config["video_writer"] = None
            
            record_button[1].text = "开始录制"
            record_button[1].bgcolor = "#39C5BB"
            status_text[1].value = f"录制完成"
            
            # 显示保存路径
            page.snack_bar = ft.SnackBar(
                ft.Text(f"视频已保存至：{config.get('current_file', record_path)}"),
                duration=3000
            )
            page.snack_bar.open = True
        
        page.update()

    # 按钮列表
    record_button = [
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,  # 直接传函数，不传参数
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,  # 直接传函数，不传参数
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
        ft.ElevatedButton(
            text="开始录制",
            on_click=toggle_recording,  # 直接传函数，不传参数
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ),
    ]

    # ========== 3. 屏幕布局（保持不变） ==========
    screen1 = ft.Container(
        content=ft.Stack(
            [
                video_image[0],
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
                video_image[1],
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
                video_image[2],
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

    # ========== 4. 页面切换逻辑 ==========
    def switch_screen(screen_num: int):
        screen1.visible = (screen_num == 1)
        screen2.visible = (screen_num == 2)
        screen3.visible = (screen_num == 3)
        page.update()

    # ========== 5. 底部导航栏 ==========
    bottom_nav = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.SCREENSHOT_MONITOR, label="前置摄像头"),
            ft.NavigationDestination(icon=ft.icons.CAMERA_FRONT, label="双目摄像头"),
            ft.NavigationDestination(icon=ft.icons.BORDER_BOTTOM, label="底部摄像头")
        ],
        on_change=lambda e: switch_screen(e.control.selected_index + 1),
        selected_index=0
    )

    # ========== 6. 组装页面 ==========
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
    
    # 启动控制服务器
    try:
        threading.Thread(target=start_control_server, args=(status_panel,), daemon=True).start()
        status_panel.set_controller_status("手柄线程已启动\r\n正在连接控制服务器...")
    except Exception as e:
        status_panel.set_controller_status(f"手柄线程启动失败\r\n{e}")

    # 页面关闭时清理资源
    def on_close(e):
        # 只清理双目录制器
        if recorder:
            recorder.stop()
        
        # 只清理双目的 video_writer
        if __CAM_CONFIGS[1].get("video_writer"):
            __CAM_CONFIGS[1]["video_writer"].release()
    
    page.on_close = on_close

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
    )