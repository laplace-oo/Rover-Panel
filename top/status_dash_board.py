import flet as ft
import time
from depth_http_decoder import serial_depth_reader
from datetime import datetime
import threading
import requests

class status_board:
    def __init__(self, page: ft.Page):

        # 添加展开状态标志
        self.is_expanded = True
        # 仪表板尺寸
        self.width = 200
        self.height = 240
        # 创建串口读取器
        self.reader = serial_depth_reader(
            page=page,
            panel=self,
            raspi_ip='192.168.137.101',  # 改成你的树莓派IP
            port=5000  # HTTP服务器端口
        )
        # 深度历史数据列表
        self.depthHistory = []
        # 历史数据最大存储数量
        self.maxHistory = 100
        # 页面引用
        self.page = page
        # 连接状态指示灯
        self.connectionLed = ft.Container(
            width=12, height=12, border_radius=6,
            bgcolor=ft.colors.RED,
            animate=ft.animation.Animation(300, ft.AnimationCurve.BOUNCE_OUT)
        )
        # 深度文本
        self.depthText = ft.Text("深度:", size=12)
        # 深度数值文本
        self.depth_value = 0.0
        self.depthValueText = ft.Text("--.--", size=12, color=ft.colors.GREY)
        # 深度单位文本
        self.depthUnitText = ft.Text("m", size=12)
        # 深度状态文本
        self.depthStatusText = ft.Text("深度正常", size=12)
        # 最后更新时间文本
        self.lastUpdateTimeText = ft.Text("最后更新: --:--:--", size=12)
        # 深度趋势指示器
        self.trendIndicator = ft.Icon(ft.icons.ARROW_UPWARD, size=12, color=ft.colors.GREY)
        # 趋势描述文本
        self.trendText = ft.Text("趋势: --", size=12)
        # 添加迷你模式按钮
        self.mini_button = ft.IconButton(
            icon=ft.icons.COMPRESS,
            icon_size=24,
            on_click=self.toggle_mini_mode,
            tooltip="切换模式",
        )
        #手柄状态文本
        self.controllerStatusText = ft.Text("手柄未启动", size=12)
        # 读取线程
        self.thread = None

        # pid是否开启文本
        self.pidText = ft.Text("pid??", size=12)
        # 机械爪编号
        self.handNumber = ft.Text("hand??", size=12)
        #快慢档
        self.speedMode = ft.Text("speed??", size=12)

        # UI面板容器
        self.panel = ft.Container(
            width=self.width,
            height=self.height,
            padding=8,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=15,
            border=ft.border.all(1, ft.colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.colors.with_opacity(0.2, ft.colors.BLACK),
                offset=ft.Offset(0, 3)
            ),
            content=ft.Column(
                spacing=1,
                controls=[
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                            self.connectionLed,
                            self.depthText,
                            self.depthValueText,
                            self.depthUnitText,
                            self.mini_button,
                            ],
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.trendIndicator,
                                self.trendText,
                            ],
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.lastUpdateTimeText,
                            ]
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.depthStatusText,
                            ]
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.controllerStatusText,
                            ]
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.pidText,
                            ]
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.handNumber,
                            ]
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        padding=2,
                        content=ft.Row(
                            controls=[
                                self.speedMode,
                            ]
                        ),
                        alignment=ft.alignment.center
                    )
                ]
            )
        )
        self.connect()

    def set_camera_json(self, num: int):
        if num == 1:
            self.camera_json = {
                "camera1": "True",
                "camera2": "False",
                "camera3": "False",
            }
        elif num == 2:
            self.camera_json = {
                "camera1": "False",
                "camera2": "True",
                "camera3": "False",
            }
        elif num == 3:
            self.camera_json = {
                "camera1": "False",
                "camera2": "False",
                "camera3": "True",
            }
        self.reader.session.post(
            f"{self.reader.server_url}/api/set_camera",
            json=self.camera_json
        )

    def set_controller_status(self, status):
        """更新手柄状态文本"""
        self.controllerStatusText.value = status
        if self.page:
            self.page.update()

    def set_pidText(self, pid_text):
        self.pidText = 'pid：{pid_text}'
        if self.page:
            self.page.update()

    def set_handNumber(self, hand_num: int):
        self.handNumber = '机械爪编号：{hand_num}'
        if self.page:
            self.page.update()
    
    def set_speedMode(self, speed_mode):
        self.speedMode = '速度模式：{speed_mode}'
        if self.page:
            self.page.update()
        

    def get_panel(self):
        """获取仪表板的容器对象"""
        return self.panel
    
    def connect(self):
        """
        连接到树莓派HTTP服务器
        返回: (成功标志, 消息)
        """
        print("connecting1")
        try:
            # 测试连接 - 访问状态接口
            print("connecting2")
            response = self.reader.session.get(
                f"{self.reader.server_url}/api/depth_status",
                timeout=3
            )

            print("connect3")
            if response.status_code == 200: # HTTP 200表示成功
                print("connect4")
                self.reader.connected = True # 标记为已连接
                self.reader.reading = True  # 设置读取状态

                self.connectionLed.bgcolor = ft.colors.GREEN  # 更新连接状态指示灯
                print("connect5")
                # 启动读取线程
                self.start_reading()

                print(f"尝试连接到树莓派服务器 {self.reader.server_url}...")
                print(f"已连接到树莓派 {self.reader.server_url}")

                return True, "连接成功"
            else:
                return False, f"服务器返回错误: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, f"无法连接到树莓派 {self.reader.server_url}"
        except requests.exceptions.Timeout:
            return False, "连接超时"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


    def start_reading(self):
        """创建一个后台线程"""
        # 如果线程已存在且正在运行，直接返回
        if self.thread and self.thread.is_alive():
            return

        self.thread = threading.Thread(target=self._read_loop, daemon=True) # daemon=True 表示守护线程，主程序退出时自动结束
        self.thread.start()
        print("网络轮询线程已启动")

    def _read_loop(self):
        """
        读取循环 - 定时HTTP请求获取深度数据
        完全模拟原串口读取的行为
        """
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.reader.reading and self.reader.connected:
            try:
                print("正在轮询深度数据...")
                # 1. 发送HTTP请求获取深度数据
                response = self.reader.session.get(
                    f"{self.reader.server_url}/api/depth_status",
                    timeout=1
                )

                if response.status_code == 200:
                    response = response.json()

                    # 2. 解析数据（兼容原接口的解析方式）
                    if response['depth'] is not None:
                        # 模拟串口数据格式，再用原来的_pxiarse_data解析
                        # 但这里可以直接用，更高效
                        old_value = self.depth_value
                        # self.depthValueText.value = f"{response['depth']:.2f}"
                        self._on_depth_updated(response['depth'])
                        self.lastUpdateTimeText.value = f"最后更新: {response['timestamp']}"

                        # 重置错误计数
                        consecutive_errors = 0

                        # 3. 如果有页面引用，通知GUI更新（完全兼容原代码）
                        if self.page:
                            self.page.update()

                        # 只在数值变化时打印（减少输出）
                        if abs(self.depth_value - old_value) > 0.001:
                            print(f"📊 深度: {self.depth_value:.2f} m")

                # 控制轮询频率（1s）
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                consecutive_errors += 1
                print(f"⚠️ 网络错误 ({consecutive_errors}/{max_consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    print("❌ 连续错误过多，标记为断开连接")
                    self.connected = False
                    break

                # 出错时等待更长时间
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ 读取错误: {e}")
                time.sleep(1)


    # ============回调方法============

    def _on_depth_updated(self, depth):
        """深度数据更新回调"""
        self.depthValueText.value = f"{depth:.2f}"
        self.depth_value = depth  # 更新当前深度值

        if depth < 5:
            color = ft.colors.GREEN
            status = "安全深度"
        elif depth < 10:
            color = ft.colors.AMBER
            status = "警告深度"
        elif depth < 20:
            color = ft.colors.ORANGE
            status = "危险深度"
        else:
            color = ft.colors.RED
            status = "极限深度"

        self.depthValueText.color = color
        self.depthStatusText.value = status
        self.depthStatusText.color = color

        now = datetime.now()
        self.lastUpdateTimeText.value = f"最后更新: {now.strftime('%H:%M:%S')}"
        self._update_trend(depth)
        if self.page:
            self.page.update()

    def _update_trend(self, current_depth):
        """更新深度趋势"""
        if len(self.depthHistory) > 1:
            prev_depth = self.depthHistory[-1]
            if current_depth > prev_depth:
                self.trendIndicator.icon = ft.icons.ARROW_DOWNWARD
                self.trendIndicator.color = ft.colors.RED
                self.trendText.value = f"趋势: 下潜 {abs(current_depth - prev_depth):.2f}m"
            elif current_depth < prev_depth:
                self.trendIndicator.icon = ft.icons.ARROW_UPWARD
                self.trendIndicator.color = ft.colors.GREEN
                self.trendText.value = f"趋势: 上浮 {abs(current_depth - prev_depth):.2f}m"
            else:
                self.trendIndicator.icon = ft.icons.REMOVE
                self.trendIndicator.color = ft.colors.GREY
                self.trendText.value = "趋势: 稳定"

        self.depthHistory.append(current_depth)
        if len(self.depthHistory) > self.maxHistory:
            self.depthHistory.pop(0)
        if self.page:
            self.page.update()

    def toggle_mini_mode(self, e):
        """切换迷你模式"""
        if self.is_expanded:
            # 切换到迷你模式
            self.panel.width = 200
            self.panel.height = 60
            self.mini_button.icon = ft.icons.EXPAND
            self.panel.content.controls[1].visible = False
            self.panel.content.controls[2].visible = False
            self.panel.content.controls[3].visible = False
        else:
            # 恢复到完整模式
            self.panel.width = 200
            self.panel.height = 240
            self.mini_button.icon = ft.icons.COMPRESS
            self.panel.content.controls[1].visible = True
            self.panel.content.controls[2].visible = True
            self.panel.content.controls[3].visible = True
        
        self.is_expanded = not self.is_expanded
        self.page.update()
