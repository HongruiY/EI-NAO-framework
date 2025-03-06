import qi
import sys
import threading

def play_music(session):
    """播放音乐文件"""
    audio_service = session.service("ALAudioPlayer")
    
    try:
        filepath = "/home/nao/Taiji.mp3"
        # 播放音乐文件
        audio_service.playFile(filepath)
        print("音乐正在播放... 按 'Enter' 键停止音乐.")
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

def manual_stop(session):
    """等待用户按下回车键手动停止音乐"""
    input("按 'Enter' 键停止音乐...")
    stop_music(session)

if __name__ == "__main__":
    # 初始化 qi.Session 并连接到 NAOqi 实例
    session = qi.Session()
    try:
        session.connect("tcp://172.20.10.5:9559")  # 请根据你的 IP 地址替换
        print("成功连接到 NAO 机器人")
    except RuntimeError as e:
        print(f"无法连接到 NAO 机器人: {e}")
        sys.exit(1)
    
    # 创建一个线程来播放音乐
    music_thread = threading.Thread(target=play_music, args=(session,))
    music_thread.start()

    # 等待用户按下回车键，手动停止音乐
    manual_stop(session)

    # 等待音乐播放线程结束
    music_thread.join()

