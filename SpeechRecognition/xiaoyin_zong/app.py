
import pyaudio
import websocket
import json
import threading
from flask import Flask, render_template

from websocket import create_connection
app = Flask(__name__)
# 创建WebSocket连接
ws = None

# 存储实时转换的文本
realtime_text = ""
text_lock = threading.Lock()  # 用于保证线程安全的锁

@app.route('/')
def index():
    global realtime_text
    return render_template('index.html', realtime_text=realtime_text)

@app.route('/start')
def start_transcription():
    global ws, stream, p
    global realtime_text
    # 定义WebSocket服务器的地址
    WEBSOCKET_SERVER_URL = "ws://58.34.191.202:30014/asr/v1/ws"

    # ... 初始化 p 和 stream ...
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, input=True, frames_per_buffer=1024)

    # 创建 WebSocket 连接
    ws = create_connection(WEBSOCKET_SERVER_URL)

    # 在发送音频数据之前发送JSON数据
    json_data = {"uid": "111111", "appId": "2099001", "engineId": "209901", "auf": "8000"}
    ws.send(json.dumps(json_data))
    print(ws.recv())

    def send_audio():
        while True:
            try:
                # 读取音频数据
                audio_data = stream.read(1024)
                # 发送音频数据到WebSocket服务器,使用二进制
                ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
                # print(ws.recv())
            except ConnectionAbortedError as e:
                print(f"Connection aborted error: {e}")
            except KeyboardInterrupt:
                # 用户按下Ctrl+C键，停止程序
                ws.send(stream.read(0))
                break

    # 启动一个线程来接收 WebSocket 消息
    def receive_messages():
        global realtime_text
        while True:
            message = ws.recv()
            # print("1111111")
            print(message)
            response = json.loads(message)
            # print("22222222")
            sentence = response['sentence']
            # print("333333333")
            if sentence != "":
                with text_lock:
                    realtime_text = sentence
                print(f"Realtime Text: {sentence}")

    # 启动两个线程，分别进行发送音频和接收消息
    threading.Thread(target=send_audio).start()
    threading.Thread(target=receive_messages).start()

    return "Started"


@app.route('/stop')
def stop_transcription():
    global ws, stream, p
    # 关闭 WebSocket 连接
    if ws:

        # 关闭麦克风输入流和WebSocket连接
        stream.stop_stream()
        stream.close()
        p.terminate()
    return "Stopped"


if __name__ == '__main__':
    app.run(debug=True)
