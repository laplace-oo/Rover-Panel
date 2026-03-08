import requests

class serial_depth_reader:
    # 初始化
    def __init__(self, page=None, panel=None, raspi_ip='192.168.137.101', port=5000):
        # 保存页面引用
        self.page = page
        # 保存深度面板引用
        self.panel = panel
        # 树莓派服务器地址
        self.server_url = f"http://{raspi_ip}:{port}"
        # 网络会话（保持连接池）
        self.session = requests.Session()
        # 读取状态标志（兼容原接口）
        self.reading = False
        # 连接状态
        self.connected = False
        print(f"服务器: {self.server_url}")