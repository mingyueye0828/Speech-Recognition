import pyaudio
import websocket
import json
import threading
# 建立WebSocket连接
# url地址，headers请求头
url = "ws://58.34.191.202:30014/asr/v1/ws"
headers = {"Content-Type": "application/json"}
ws = websocket.WebSocketApp(url, headers,
                            on_open=lambda ws: on_open(ws),
                            on_message=lambda ws, msg: on_message(ws, msg),
                            on_error=lambda ws, error: on_error(ws, error),
                            on_close=lambda ws: on_close)

# 定义数据流块，创建音频流，检查麦克风是否打开
CHUNK = 1024                 # 定义数据流块
FORMAT = pyaudio.paInt16  # 16bit编码格式
CHANNELS = 1  # 单声道
RATE = 8000  # 8000采样频率
# 进行录音，创建音频流
p = pyaudio.PyAudio()
# 创建音频流
# stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, input=True, frames_per_buffer=1024)
stream = p.open(format=FORMAT,  # 音频流wav格式
                channels=CHANNELS,  # 单声道
                rate=RATE,  # 采样率16000
                input=True,
                frames_per_buffer=CHUNK)
# # 检测麦克风是否打开
# for i in range(p.get_device_count()):
#     device_info = p.get_device_info_by_index(i)
#     if device_info['maxInputChannels'] > 0:
#         print(f"Microphone {i}: {device_info['name']} is available and openable.")
#     else:
#         print(f"Microphone {i}: {device_info['name']} is not available.")
# print("- - - - - - - Start Recording ...- - - - - - - ")

def send_audio_data(data):
    ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

# 管理线程，进行运行
def transmit_audio_data():
    while True:
        try:
            # 完成之后将数据流进行遍历的方式进行不间断的发送实时的接口
            buffer = stream.read(CHUNK)
            # ws.send(buffer, opcode=websocket.ABNF.OPCODE_BINARY)
            send_audio_data(buffer)
        except KeyboardInterrupt as e:
            print("Error in run:", e)
            buffer = stream.read(0)
            send_audio_data(buffer)
            break

# 创建要发送的数据
class Ws_Param(object):
    # 初始化参数 appId modelId uid auf
    def __init__(self, appId, modelId, uid, auf):
        self.appId = appId
        self.modelId = modelId
        self.uid = uid
        self.auf = auf
        # 其他参数(business)
        self.BusinessArgs = {"callInfo": "null", "callId": "Yes", "callNumber": "Yes", "role": "Yes"}

# 收到websocket连接建立的处理，并发送数据的过程
def on_open(ws):
    print("WebSocket连接已打开")
    wsParam = Ws_Param(appId='2099001', modelId='209901',
                       uid='111111', auf=8000)
    # 将实例属性放入字典中
    ws_param_dict = {
        "appId": wsParam.appId,
        "modelId": wsParam.modelId,
        "uid": wsParam.uid,
        "auf": wsParam.auf,
        "BusinessArgs": wsParam.BusinessArgs
    }
    # 将数据转化为JSON格式
    json_data = json.dumps(ws_param_dict)
    ws.send(json_data)

# 收到websocket消息的处理，进行处理
def on_message(ws, message):
    # print(message)
    response=json.loads(message)
    sentence=response['sentence']
    if (sentence==""):
        return
    print(f"{response['sentence']}")

# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)

# 收到websocket关闭的处理
def on_close(ws):
    print("WebSocket连接已关闭")
    # print("### closed ###")
def connect():
    ws.run_forever()

# 发送请求，是否有所回应
def run():
    t = threading.Thread(target=connect)
    t.start()
    transmit_audio_data()
    # ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=2)

# 开始连接和传输音频数据
if __name__ == "__main__":
    # ws.run_forever() 是在连接上调用的方法，它会使程序在这里一直运行，保持 WebSocket 连接状态。
    # 创建线程，执行connect方法，target指定线程运行的函数，并开启线程
    run()
    # connect_thread = threading.Thread(target=connect)
    # connect_thread.start()
    # transmit_audio_data()

# 关闭麦克风输入流和WebSocket连接
stream.stop_stream()
stream.close()
p.terminate()
