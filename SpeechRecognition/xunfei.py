import wave

import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import pyaudio


STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret


        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理

def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            return code
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            # 文件进行处理，去掉。和.。等
            if result == '。' or result=='.。' or result==' .。' or result==' 。':
                pass
            else:
                t.insert(END, result)
                print("翻译结果: %s。" % (result))

    except Exception as e:
        print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    pass
    # print("### closed ###")


# 收到websocket连接建立的处理，并发送数据的过程
def on_open(ws):
    def run(*args):
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        CHUNK = 520                 # 定义数据流块
        FORMAT = pyaudio.paInt16  # 16bit编码格式
        CHANNELS = 1  # 单声道
        RATE = 16000  # 16000采样频率
        # 进行录音，创建音频流
        p = pyaudio.PyAudio()
        # 检测麦克风是否打开
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"Microphone {i}: {device_info['name']} is available and openable.")
            else:
                print(f"Microphone {i}: {device_info['name']} is not available.")
        # 创建音频流
        stream = p.open(format=FORMAT,  # 音频流wav格式
                        channels=CHANNELS,  # 单声道
                        rate=RATE,  # 采样率16000
                        input=True,
                        frames_per_buffer=CHUNK)

        print("- - - - - - - Start Recording ...- - - - - - - ")

        WAVE_OUTPUT_FILENAME = "output_1.wav"  # 保存的音频文件名
        # 初始化音频文件
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        # 完成之后将数据流进行遍历的方式进行不间断的发送实时的接口
        for i in range(0, int(RATE/CHUNK*60)):
            buf = stream.read(CHUNK)
            # print(buf)
            if not buf:
                status = STATUS_LAST_FRAME
            if status == STATUS_FIRST_FRAME:

                d = {"common": wsParam.CommonArgs,
                     "business": wsParam.BusinessArgs,
                     "data": {"status": 0, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                d = json.dumps(d)
                ws.send(d)
                wf.writeframes(buf)
                status = STATUS_CONTINUE_FRAME
                # 中间帧处理
            elif status == STATUS_CONTINUE_FRAME:
                d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))
                wf.writeframes(buf)

            # 最后一帧处理
            elif status == STATUS_LAST_FRAME:
                d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))
                wf.writeframes(buf)
                time.sleep(1)
                break

        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
        ws.close()
    thread.start_new_thread(run,())


def run():
    global wsParam
    wsParam = Ws_Param(APPID='0452bde7', APIKey='9a298d898c6a217b1100482c76efeeea',
                       APISecret='NGI5Yjg2ZmU3MjBlM2ZiMDA1YjExOTMy')
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=2)

# TODO 记得修改 APPID、APIKey、APISecret
# 创建额外的线程，使其不会阻塞
from tkinter import *
import threading
import tkinter
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    # t.setDaemon(True)
    t.daemon = True
    t.start()
root = Tk()
t = Text(root)
t.pack()

tkinter.Button(root, text='go', command=lambda :thread_it(run,)).pack()
tkinter.Button(root, text='quit', command=root.quit).pack()
root.mainloop()