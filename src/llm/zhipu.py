from zhipuai import ZhipuAI
import re
import time
class zhipuEngine():
	"""
	A dialog engine class based on Zhipu AI API. 
	This class can maintain a conversation history and generate a response based on a given prompt. 
	If punctuation is encountered or the message length is reached, the robot's tts module is called to make the robot speak accordingly as soon as possible.
 	"""
	def __init__(self,token,system_prompt,massage_threshold=10,say_word_threshold=25,max_tokens=64) -> None:
		"""
  		:param token: Zhipu AI API token
        :param system_prompt: user provide
        :param massage_threshold: The maximum length of the conversation history, beyond which old messages are deleted.
        :param say_word_threshold: The maximum number of words per output, exceeding that length will be said directly.
        """
		self.client = ZhipuAI(api_key=token)
		self.massage=[]

		self.massage_threshold=massage_threshold
		self.say_word_threshold=say_word_threshold
		self._append_massage("system",system_prompt)
		self.max_tokens=max_tokens
	def _generate(self,prompt):
		"""
  		Generate a response based on the given prompt.
  		"""
		self.__check_massage()
		self._append_massage("user",prompt)

		response = self.client.chat.completions.create(model="glm-4",messages=self.massage,stream=True,max_tokens=self.max_tokens)
		str_tmp=""

		while True:
			try:
				chunk = next(response)
				delta = chunk.choices[0].delta
				str_tmp+=delta.content
				mycontent = delta.content
				yield mycontent
			except StopIteration:
				break
			except Exception as e:
				print(f"Error: {e}")
				time.sleep(0.1)
				continue
		self._append_massage("assistant",str_tmp)

	def _append_massage(self,role,context):
		"""
  		Adds a new message to the conversation history.
 		"""
		self.massage.append({"role": role, "content": context}) 
	def __check_massage(self):
		"""
      	Check the length of the conversation history and delete old messages.
       	"""
		if len(self.massage)> self.massage_threshold:
			del self.massage[0 : len(self.massage)-self.massage_threshold]
	def get_data(self):
		return self.data

if __name__=="__main__":
	module = zhipuEngine(token="50395ecf9e295b7051a7e26745c8349b.WNflYUURtakioHQB", system_prompt="你是一个小助手")
	for i in module._generate("你好啊"):
		print(i)