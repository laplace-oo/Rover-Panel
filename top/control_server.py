import socket
import threading
from re_control import remote_control, control_Length
import sys
import time
global Receive_M
def receive_messages(client_socket):
    while True:
        try:
            # 接收消息
            recv_data = client_socket.recv(1024).decode("UTF-8")
            if not recv_data:  # 检测服务器是否关闭连接
                print("服务器已关闭连接，程序将退出。")
                break
            print(f"服务端回复的消息是：{recv_data}")

        except Exception as e:
            print(f"接收消息时出现错误: {e}")
            
            break

def send_messages(client_socket):
    while True:
        try:
            TX = remote_control()
            TX_str = hex(TX[0])[2:].rjust(2, '0')
            for i in range(1, control_Length):
                TX_str += hex(TX[i])[2:].rjust(2, '0')
                data_to_send = bytes.fromhex(TX_str)  # 很重要
            client_socket.send(data_to_send)
            print(data_to_send)
            time.sleep(0.01)  # 控制发送频率，避免过快发送导致问题
        except Exception as e:
            print(f"发送消息时出现错误: {e}")
            sys.exit()

def start_control_server(status_board):
    Rover_client = None
    try:
        # 创建 socket 对象
        Rover_client = socket.socket()
        # 连接到服务器
        Rover_client.connect(("192.168.137.101", 8888))

#        status_board.set_controller_status("手柄已连接到服务器。")

        # 创建线程来处理接收消息
        receive_thread = threading.Thread(target=receive_messages, args=(Rover_client,))
        receive_thread.start()
        
        # 创建线程来处理发送消息
        send_thread = threading.Thread(target=send_messages, args=(Rover_client,))
        send_thread.start()

 #       status_board.set_controller_status("控制服务器线程已启动\r\n正在发送和接收消息...")

        # 等待接收线程结束
        receive_thread.join()
        
        # 等待发送线程结束
        send_thread.join()
    
    except Exception as e:

 #       status_board.set_controller_status(f"连接服务器时出现错误: {e}")
        print(f"连接服务器时出现错误: {e}")
    finally:
        # 关闭连接
        if Rover_client:
            Rover_client.close()
if __name__ == "__main__":
    start_control_server(None)