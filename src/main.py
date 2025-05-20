# -*- coding: utf-8 -*-
import qi
import os
import sys
import time
import socket
import json
from asr.asrModule import ASRModule
from llm.zhipu import zhipuEngine
from threading import Thread
import grasp.yolo.grasp_control_yolo as grasp
import dance.tai_chi_chuan as dance 
class AudioProcessor(Thread):
    def __init__(self,asr_module):
        super().__init__()
        self.asr_module=asr_module
        self.transcription= None

    def run(self):
        self.transcription = asr_module.process_audio()


    def get_transcription(self):
        return self.transcription
    
class CustomTTS:
    def __init__(self, tts, max_length=40):
        self.tts = tts
        self.buffer = ""
        self.max_length = max_length

    def add_text(self, text):
        for char in text:
            self.buffer += char
            if char in [".", "!", "?", "。", "，", "！", "？"]:  # 识别中英文标点符号
                self.flush()  # 遇到标点符号就说话
            elif len(self.buffer) >= self.max_length:
                self.flush()  # 缓冲区满了就说话

    def flush(self):
        if self.buffer:
            print(f"机器人说: {self.buffer}")  # 输出到控制台进行调试
            self.tts.say(self.buffer)  # 让机器人说话
            self.buffer = ""  # 清空缓冲区

    def clear_buffer(self):
        """
        清空之前的缓冲区，确保不会说出上次未完成的内容。
        """
        self.buffer = ""

def play_music(session, song_path):
    """播放指定路径的音乐文件"""
    audio_service = session.service("ALAudioPlayer")
    # 调试输出拼接后的路径
    
    try:
        # 播放音乐文件
        audio_service.playFile(song_path)
        print(f"正在播放: {song_path}")
    except Exception as e:
        print("播放音乐时发生错误: ", e)

def stop_music(session):
    """停止所有播放的音乐"""
    audio_service = session.service("ALAudioPlayer")
    try:
        # 停止所有播放的音乐
        audio_service.stopAll()
        print("音乐已停止.")
    except Exception as e:
        print("停止音乐时发生错误: ", e)


def waiting_for_touch(memory):
    print("等待触摸头部...")
    while True:
        headTouchedButtonFlag = memory.getData("FrontTactilTouched")
        if headTouchedButtonFlag == 1.0:
            print("头部已被触摸!")
            break
        time.sleep(0.8)


grasp_state = {
    "location": None,
    "obj": None
}

# 解析用户指令并执行相应功能
def execute_command(asr_result, config, session, custom_tts, nlp_module):
    # 跳舞
    for keyword in config["dance"]["keywords"]:
        if keyword in asr_result:
            try:
                dance.start_dance_and_music(session)  # 尝试启动跳舞和播放音乐
            except Exception as e:
                print(f"跳舞过程中发生错误: {e}")  # 打印错误信息以便调试
                custom_tts.add_text("抱歉，我在跳舞时遇到了一点问题。")  # 向用户反馈错误
            return  # 成功处理后，结束函数

    
    # 检查用户是否提到了播放音乐
    for keyword in config["music"]["keywords"]:
        if keyword in asr_result:
            found_song = False  # 用于追踪是否找到匹配的歌曲
            # 找到用户想播放的歌曲
            for song, path in config["music"]["tracks"].items():
                if song in asr_result:
                    song_path = os.path.join("/home/nao/", path)  # 拼接完整路径
                    print(f"播放音乐: {song}")
                    play_music(session, song_path)  # 播放音乐
                    found_song = True  # 标记为已找到歌曲
                    break
            
            # 如果没有找到对应的歌曲，执行提示
            if not found_song:
                print("要播放的歌曲未在曲库中.")
                custom_tts.add_text("诶呀，这首歌我不会唱呀，让我再学习学习。")
            break  # 找到关键词后退出整个检查循环

    # # 等待用户按下回车键，手动停止音乐
    # input("按 'Enter' 键停止音乐...")
    # stop_music(session)
    
    # 抓取物品
    for keyword in config["grasp"]["keywords"]:
        if keyword in asr_result:
            # 从全局状态中获取已经保存的参数
            location = grasp_state["location"]
            obj = grasp_state["obj"]

            # 检查位置
            if not location:
                for loc_keyword, loc_value in config["grasp"]["locations"].items():
                    if loc_keyword in asr_result:
                        location = loc_value
                        grasp_state["location"] = location  # 保存位置
                        break

            # 检查物品
            if not obj:
                for obj_keyword, obj_value in config["grasp"]["objects"].items():
                    if obj_keyword in asr_result:
                        obj = obj_value
                        grasp_state["obj"] = obj  # 保存物品
                        break

            # 如果只得到位置，询问物品
            if location and not obj:
                custom_tts.add_text(f"你想让我抓取{location}的什么呢？")
                return  # 等待用户输入新的物品信息

            # 如果只得到物品，询问位置
            if obj and not location:
                custom_tts.add_text(f"你想让我抓取桌子上还是地上的{obj}呢？")
                return  # 等待用户输入新的位置信息

            # 如果同时得到位置和物品，执行抓取
            if location and obj:
                print(f"执行抓取动作: {location}, {obj}")
                custom_tts.add_text(f"好的，现在我要抓取{location}的 {obj}啦！")
                grasp.main(session, location=location, obj=obj)

                # 重置 TTS 服务，确保正常
                tts = session.service("ALTextToSpeech")
                tts.setLanguage("Chinese")
                custom_tts.clear_buffer()

                # 重置状态以处理下一次抓取请求
                grasp_state["location"] = None
                grasp_state["obj"] = None
                return
    
    # 默认对话
    for response in nlp_module._generate(asr_result):
        custom_tts.add_text(response)

if __name__ == "__main__":
    # 初始化 qi.Session 并连接到 NAOqi 实例
    session = qi.Session()
    try:
        session.connect("tcp://172.20.10.9:9559")

        print("成功连接到 NAO 机器人")
    except RuntimeError as e:
        print(f"无法连接到 NAO 机器人: {e}")
        sys.exit(1)
    SERVER_PORT = 12345

    # 创建TCP套接字并连接服务器
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((session.url().replace("tcp://", "").split(":")[0], SERVER_PORT))
        print("已连接到服务器")
    except socket.error as e:
        print(f"无法连接到服务器: {e}")
        exit(1)

    # 初始化各模块
    base_dir = os.path.dirname(os.path.abspath(__file__))
    asr_module = ASRModule(param_path=os.path.join(base_dir, "../asr/FastASR/models/paddlespeech_stream/"), client_socket=client_socket)
    nlp_module = zhipuEngine(token="50395ecf9e295b7051a7e26745c8349b.WNflYUURtakioHQB", system_prompt=" ")


    memory = session.service("ALMemory")
    tts = session.service("ALTextToSpeech")
    tts.setLanguage("Chinese")
    custom_tts = CustomTTS(tts, max_length=40)

    waiting_for_touch(memory)
    
    # 加载指令映射 JSON 文件
    with open(os.path.join(base_dir, "state.json"), 'r', encoding='utf-8') as f:
        state_config = json.load(f)

    waiting_for_touch(memory)

    while True:
        custom_tts.clear_buffer()

        # 使用 AudioProcessor 启动 ASR 处理线程
        audio_processor = AudioProcessor(asr_module)
        audio_processor.start()  # 启动 ASR 线程
        audio_processor.join()  # 等待 ASR 处理完成

        # 获取 ASR 结果
        asr_result = audio_processor.get_transcription()
        if not asr_result:
            print("未能获取有效的 ASR 结果")
            continue

        print(f"ASR 结果: {asr_result}")

        # 根据 ASR 结果解析并执行对应的功能
        execute_command(asr_result, state_config, session, custom_tts, nlp_module)

        time.sleep(1)

        if "再见" in asr_result or "拜拜" in asr_result:
            print("结束程序")
            break