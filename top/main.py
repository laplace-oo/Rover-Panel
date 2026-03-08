import flet as ft
import os
import cv2
import threading
from datetime import datetime
from sgbm import get_depth as gd
from stream_update import update_video_stream as uvs
from config import __CAM_CONFIGS, __RECORD_DIR, __STREAM_URL
from control_server import start_control_server
from status_dash_board import status_board

# 生成视频编码格式标准（4-Character Code），使用mp4v编码
fourcc = cv2.VideoWriter.fourcc(*"mp4v")

two_eyes_button = None

def main(page: ft.Page):
    
    # ========== 0. 深度仪表板 ==========
    # 创建深度仪表板对象
    status_panel = status_board(page)
    # 获取仪表板的容器对象
    status_board_container = status_panel.get_panel()

    # ========== 1. 基础配置 ==========
    page.title = "树莓派监控"
    page.window_width = 1960  # 窗口宽度
    page.window_height = 1080  # 窗口高度
    page.padding = 0  # 去掉默认内边距
    page.theme_mode = "system"

    # ========== 2. 定义三个屏幕的内容 ==========

    # 流的显示组件列表
    video_image = [
        ft.Image(fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10), width=1440, height=960),
        ft.Image(fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10), width=1920, height=540),
        ft.Image(fit=ft.ImageFit.COVER, border_radius=ft.border_radius.all(10), width=1440, height=960),
    ]

    # 状态栏列表
    status_text = [
        ft.Text("等待连接视频流...",color=ft.colors.GREY_600,text_align=ft.TextAlign.CENTER,),
        ft.Text("等待连接视频流...",color=ft.colors.GREY_600,text_align=ft.TextAlign.CENTER,),
        ft.Text("等待连接视频流...",color=ft.colors.GREY_600,text_align=ft.TextAlign.CENTER,),
    ]

    # 录制按钮的逻辑函数
    
    def toggle_recording(e, cam_index: int):

        config = __CAM_CONFIGS[cam_index]

        # 生成一个包含当前年月日时分秒的时间戳字符串
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        # 存放录像的完整路径
        record_path = os.path.join(__RECORD_DIR, config["name"], f"video_{str(cam_index)}_{timestamp}.mp4")
        print(record_path)

        # 开始录制
        if not config["is_recording"]:

            # 检测用于存放录像的文件夹是否存在，不存在就创建一个
            os.makedirs(os.path.dirname(record_path), exist_ok=True)

            # 写入视频流（完整存放路径，编码格式标准，帧率，分辨率）
            config["video_writer"] = cv2.VideoWriter(record_path, fourcc, config["fps"], config["resolution"])

            # 检测录像状态
            if config["video_writer"].isOpened():
                # 正在录制
                # 更改记录标签
                config["is_recording"] = True
                # 进行一系列的更改。例如按钮文本，按钮颜色，状态栏文本。
                record_button[cam_index].text = "停止录制"
                record_button[cam_index].bgcolor = ft.colors.RED_500
                status_text[cam_index].value = "开始录制"
            else:
                # 录制失败了，写入视频用的写入流始化失败。
                status_text[cam_index].value = "录制初始化失败"
        else:
            # 停止录制
            # 更改记录标签。
            config["is_recording"] = False

            # 释放掉写入视频流
            config["video_writer"].release()
            # 释放后再初始化一次，用来等待下次写入。
            config["video_writer"] = None
            
            # 同样进行一系列更改，例如文本按钮，颜色，状态栏文本，
            record_button[cam_index].text = "开始录制"
            record_button[cam_index].bgcolor = "#39C5BB"
            status_text[cam_index].value = "录制完成"
            
            # 底部弹窗。别问我为什么不做一个打开文件夹的按钮，我尝试了但是失败了
            page.snack_bar = ft.SnackBar(
                ft.Text(f"视频已保存至：{record_path}"),
                action="关闭",
                # action="67" 
                # 设置弹窗自动关闭时间（毫秒），不用手动点关闭
                duration=3000
            )
            page.snack_bar.open = True
        page.update()

    # 按钮列表
    record_button = [
        # 屏幕1：主摄像头按钮
        ft.ElevatedButton(
            text="开始录制",
            # 主要是这里，传入的数字不同
            on_click=lambda e,idx = 0: toggle_recording(e, idx),
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),),
        ),
        # 屏幕2：双目摄像头按钮
        ft.ElevatedButton(
            text="开始录制",
            on_click=lambda e,idx = 1: toggle_recording(e, idx),
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),),
        ),
        # 屏幕3：下置摄像头按钮
        ft.ElevatedButton(
            text="开始录制",
            on_click=lambda e,idx = 2: toggle_recording(e, idx),
            bgcolor="#39C5BB",
            color=ft.colors.WHITE,
            width=200,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),),
        ),
    ]

    # 测距按钮的逻辑函数
    def toggle_depth(e):
        config = __CAM_CONFIGS[1]
        if not config["switch"]:

            config["switch"] = True
            two_eyes_button.text = "停止测距"
            two_eyes_button.bgcolor = ft.colors.RED_500
            config["thread"] = threading.Thread(target=gd, args=(config,),daemon=True)
            config["thread"].start()

        else:

            config["switch"] = False
            two_eyes_button.text = "开始测距"
            two_eyes_button.bgcolor = ft.colors.PURPLE


        page.update()
        
    # 双目显示测距按钮
    two_eyes_button = ft.ElevatedButton(
        text="开始测距",
        on_click=lambda e:toggle_depth(e),
        bgcolor = ft.colors.PURPLE,
        color=ft.colors.WHITE,
        width=200,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),),
    )

    # 屏幕1：主摄像头
    screen1 = ft.Container(
        content=ft.Row(
            [
                video_image[0],
                ft.Column(
                    [
                        record_button[0],
                        status_text[0],
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        ),
        expand=True,  # 占满父容器
        alignment=ft.alignment.center,
        visible=True  # 默认显示第一个屏幕
    )

    # 屏幕2：双目摄像头
    screen2 = ft.Container(
        content=ft.Column(
            [
                video_image[1],
                ft.Row(
                    [record_button[1]],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                status_text[1],
                ft.Row(
                    [two_eyes_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        expand=True,  # 占满父容器
        alignment=ft.alignment.center,
        visible=False
    )

    # 屏幕3：底部摄像头
    screen3 = ft.Container(
        content=ft.Row(
            [
                video_image[2],
                ft.Column(
                    [
                        record_button[2],
                        status_text[2],
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        ),
        expand=True,  # 占满父容器
        alignment=ft.alignment.center,
        visible=False
    )

    # ========== 3. 页面切换逻辑 ==========
    def switch_screen(screen_num: int):

        # 隐藏所有屏幕
        screen1.visible = False
        screen2.visible = False
        screen3.visible = False
        
        # 显示目标屏幕
        if screen_num == 1:
            screen1.visible = True
            status_panel.set_camera_json(1)
        elif screen_num == 2:
            screen2.visible = True
            status_panel.set_camera_json(2)
        elif screen_num == 3:
            screen3.visible = True
            status_panel.set_camera_json(3)

        
        # 更新页面（必须）
        page.update()

    # ========== 4. 底部导航栏（切换入口） ==========
    bottom_nav = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(
                icon=ft.icons.SCREENSHOT_MONITOR,
                label="前置摄像头",
                selected_icon=ft.icons.SCREENSHOT_MONITOR
            ),
            ft.NavigationDestination(
                icon=ft.icons.CAMERA_FRONT,
                label="双目摄像头",
                selected_icon=ft.icons.CAMERA_FRONT
            ),
            ft.NavigationDestination(
                icon=ft.icons.BORDER_BOTTOM,
                label="底部摄像头",
                selected_icon=ft.icons.BORDER_BOTTOM
            )
        ],

        # 索引从0开始，+1对应屏幕号
        #当用户点击导航栏的不同选项时，自动调用 switch_screen() 函数，并传递对应的屏幕编号。
        #on_change是 ft.NavigationBar 的事件回调属性，当选中项改变时触发。
        on_change=lambda e: switch_screen(e.control.selected_index + 1),

        # 默认选中第一个
        selected_index=0
    )

    # ========== 5. 组装页面结构 ==========
    # 用Stack存放所有屏幕（叠加显示，通过visible控制显隐）
    screen_stack = ft.Stack(
        [screen1, screen2, screen3],
        expand=True  # 占满除导航栏外的空间
    )

    # 多视频线程启动函数
    def start_uvs(cam_index: int):
        uvs(
            stream_url=__STREAM_URL[cam_index],
            video_image=video_image[cam_index],
            status_text=status_text[cam_index],
            page=page,
            cam_config=__CAM_CONFIGS[cam_index]
        )

    # 启动视频流线程
    threading.Thread(target=start_uvs, args=(0,), daemon=True).start()
    threading.Thread(target=start_uvs, args=(1,), daemon=True).start()
    threading.Thread(target=start_uvs, args=(2,), daemon=True).start()

    
    page.add(
        ft.Stack(
            [
                ft.Column([screen_stack, bottom_nav], expand=True, spacing=0),
                ft.Container(
                    content=status_board_container,
                    top=10,
                    right=10,
                )
            ],
            expand=True
        )
    )
    
    try:
        threading.Thread(target=start_control_server(status_panel), daemon=True).start()
        status_panel.set_controller_status("手柄线程已启动\r\n正在连接控制服务器...")
    except Exception as e:
        status_panel.set_controller_status("手柄线程启动失败\r\n{e}")


# python=3.7.1
if __name__ == "__main__":
    
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,  # 桌面应用
        # view=ft.WEB_BROWSER,       # 网页应用
        # port=8550,
    )
    


