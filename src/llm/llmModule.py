import qi
from zhipu import zhipuEngine
class LLMModule:# 修改后未测试 
    def __init__(self, token, system_prompt):
        # 保存传入的参数
        self.token = token
        self.system_prompt = system_prompt        
        # 初始化 zhipuEngine 暂时使用zhipuengine作为推理测试
        self.dialog_engine = zhipuEngine(token, self.say, system_prompt)


    def _generate(self, text):
        for i in self.dialog_engine._generate(text):
            pass
        # 这里有点多余，完全可以直接通过zhipu来调用，解决方法是把这个LLMModule的类去虚拟化，也就是说作为zhipu的虚基类，但是呢，测试的话就没必要写这个地方了
        # 也就是说测试的阶段直接默认zhipu就是LLMModule即可，LLMModule后续实现再说
        # 还有，使用zhipu的方式可以参考这个函数，那个i就是数据流
        # 还有，baseclass的方法名应该往上传递
        
        
    # def say(self, text):
        # 模拟说话
        # print("TTS 模块说:", text)
        # self.tts_service.say(text)




# if __name__ == "__main__":
#     token = "50395ecf9e295b7051a7e26745c8349b.WNflYUURtakioHQB"
#     system_prompt = "你是一个什么都会的小助手"

#     # 初始化 NLPModule
#     nlp_module = NLPModule(token, system_prompt)

#     # 测试输入
#     test_inputs = [
#         "你能告诉我运动的好处吗？",
#         "你能解释一下人工智能吗？"
#     ]

#     # 循环处理每个测试输入
#     for input_text in test_inputs:
#         print(f"用户输入: {input_text}")
#         response = nlp_module.infer(input_text)
#         print(f"模型生成的回复: {response}")

if __name__ == "__main__":
    session = qi.Session()
    session.connect("tcp://172.20.10.5:9559")  # 连接到 NAOqi 实例

    tts_service = session.service("ALTextToSpeech")


    token = "50395ecf9e295b7051a7e26745c8349b.WNflYUURtakioHQB"
    system_prompt = "你是一个小助手"

    nlp_module = LLMModule(token, system_prompt, tts_service)

    recognized_text = "你好，今天的天气怎么样？"
    response = nlp_module.infer(recognized_text)
    print("模型回复:", response)
    nlp_module.say(response) 