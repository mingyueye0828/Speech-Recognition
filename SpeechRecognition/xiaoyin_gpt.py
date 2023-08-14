# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 15:40:57 2023

@author: ZhiyuanZhang
"""

import pyaudio
import websocket
import json
import threading

# 定义WebSocket服务器的地址
WEBSOCKET_SERVER_URL = "ws://58.34.191.202:30014/asr/v1/ws"

# 创建WebSocket连接和麦克风输入流
ws = websocket.WebSocketApp(WEBSOCKET_SERVER_URL,
                            on_open=lambda ws: on_open(ws),
                            on_message=lambda ws, msg: on_message(ws, msg),
                            on_close=lambda ws: on_close(ws))

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, input=True, frames_per_buffer=1024)

# 打开WebSocket连接
def on_open(ws):
    print("WebSocket连接已打开")

    # 在发送音频数据之前发送JSON数据
    json_data = {"uid": "111111","appId":"2099001","engineId":"209901","auf":"8000"}
    ws.send(json.dumps(json_data))

# 接收WebSocket消息
def on_message(ws, message):
    #print(f"收到消息：{message}")
    response=json.loads(message)
    sentence=response['sentence']
    if (sentence==""):
        return
    print(f"{response['sentence']}")

# 发送音频数据到WebSocket服务器
def send_audio_data(data):
    ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

# 关闭WebSocket连接
def on_close(ws):
    print("WebSocket连接已关闭")

# 连接到WebSocket服务器
def connect():
    ws.run_forever()

# 持续从麦克风读取音频数据并发送到WebSocket服务器
def transmit_audio_data():
    while True:
        try:
            # 读取音频数据
            audio_data = stream.read(1024)

            # 发送音频数据到WebSocket服务器
            send_audio_data(audio_data)
        except KeyboardInterrupt:
            # 用户按下Ctrl+C键，停止程序
            send_audio_data(stream.read(0))
            break

# 开始连接和传输音频数据
if __name__ == "__main__":
    connect_thread = threading.Thread(target=connect)
    connect_thread.start()
    transmit_audio_data()

# 关闭麦克风输入流和WebSocket连接
stream.stop_stream()
stream.close()
p.terminate()