import gc
import os
import time
from typing import Any, Generator
import torch
from datetime import datetime as dt
from threading import Thread
from transformers import pipeline, TextIteratorStreamer  #, ConversationalPipeline
from transformers.generation.stopping_criteria import StoppingCriteria, StoppingCriteriaList
from transformers.models.auto import AutoTokenizer, AutoModelForCausalLM

import constants as c


os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.environ['USERPROFILE'], '.transformers_cache')


# ====================================================================
class StopCriteria (StoppingCriteria):
	def __str__(self) -> str:
		return self.__class__.__name__

	def __repr__(self) -> str:
		return str(self)

	def print_stopped(self):
		print(f'> Stopped by: {self}')


# ====================================================================
class VariableStopCriteria (StopCriteria):
	def __init__(self):
		self.is_done = False

	def __call__(self, input_ids:torch.LongTensor, scores:torch.FloatTensor, **kwargs) -> bool:
		if self.is_done:
			self.print_stopped()
		return self.is_done

	def stop(self):
		self.is_done = True

	def reset(self):
		self.is_done = False


# ====================================================================
# class TextGenerationPipeline(ConversationalPipeline):
# 	def postprocess(self, model_outputs, clean_up_tokenization_spaces:bool = False):
# 		return super(self.__class__, self).postprocess(model_outputs, clean_up_tokenization_spaces)


# ====================================================================
class BaseLLM:
	def __init__(self, name:str):
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self.name = name
		self.short_name = name.split('/', 1)[-1]
		self.name_map = {'user': 'You', 'assistant': self.short_name}
		self.is_generating = False
		print(f'> Loading {self.__class__.__name__}: {self.full_name}')
		self.reset_messages()
		self.clear_cache()

	@property
	def full_name(self) -> str:
		return f'{self.name} ({self.device.type})'

	@classmethod
	def date_now(cls) -> str:
		return dt.now().strftime('%d.%m.%Y %H:%M:%S')

	@classmethod
	def create_message(cls, role:str, content:str) -> dict[str, str]:
		return {
			'role': role,
			'content': content,
			'date': cls.date_now() }

	def add_message(self, role:str, content:str):
		self.messages.append(self.create_message(role, content))

	def print_memory_info(self):
		print(str(torch.cuda.memory_summary(device=self.device, abbreviated=True)))

	def clear_cache(self):
		gc.collect()
		torch.cuda.empty_cache()

	def reset_messages(self):
		self.messages = []

	def list_messages(self) -> list[dict[str, str]]:
		return self.messages[:]

	def stop_generating(self):
		if self.is_generating is False:
			return
		self.is_generating = False
		if len(self.messages) > 0 and self.messages[-1]['role'] == 'user':
			self.messages.pop()

	def generate(self, prompt_text:str) -> str:
		sec, gen_wait_sec = 0, 7
		self.is_generating = True
		self.add_message('user', prompt_text)
		while self.is_generating and sec < gen_wait_sec:
			time.sleep(1)
			sec += 1
		response = f'Done generating, prompt: "{prompt_text}" ({gen_wait_sec} seconds)'
		if self.is_generating:
			self.add_message('assistant', response)
			self.is_generating = False
			return response
		return ''


# ====================================================================
class TextGenerationLLM (BaseLLM):
	def __init__(self, name:str):
		self.system_prompt = (
			'Always Remember: '
			'You\'re a technical AI chatbot assistant, a senior programmer and you know a lot about Python. '
			'You respond short and straight to the point and answer truthfully. '
			'You respond using up to 80 words maximum!')

		super(self.__class__, self).__init__(name)

		self.stop_crit_var = VariableStopCriteria()
		self.gen_response = ''

		self.pipeline_cfg:dict = dict(
			device_map=self.device,
			framework='pt',
			# pipeline_class=TextGenerationPipeline,
			return_full_text=False,
			torch_dtype=torch.bfloat16,
			trust_remote_code=False)

		self.pipe_cfg:dict = dict(
			batch_size=8,
			do_sample=True,
			# max_length=1024,
			max_new_tokens=512,
			num_return_sequences=1,
			stopping_criteria=StoppingCriteriaList([self.stop_crit_var]),
			temperature=0.95,
			top_k=50,
			top_p=1.0,
			use_cache=True)

		self.tokenizer_cfg:dict = dict(
			add_generation_prompt=True,
			return_tensors='pt',
			tokenize=False)

		self.streamer_cfg:dict = dict(
			skip_prompt=True,
			timeout=None)

		with torch.no_grad():
			self.pipe = pipeline(
				task='text-generation',
				model=self.name,
				**self.pipeline_cfg)

			with self.pipe.device_placement():
				if self.pipe.model is None:
					self.pipe.model = AutoModelForCausalLM.from_pretrained(self.name, **self.pipeline_cfg)

				if self.pipe.tokenizer is None:
					self.pipe.tokenizer = AutoTokenizer.from_pretrained(self.name, device_map=self.pipeline_cfg['device_map'])

				self.streamer = TextIteratorStreamer(self.pipe.tokenizer, **self.streamer_cfg)  #type:ignore
				self.pipe_cfg['streamer'] = self.streamer

	def reset_messages(self):
		self.messages = [self.create_message('system', self.system_prompt)]

	def stop_generating(self):
		if self.is_generating is False:
			return
		self.is_generating = False
		self.stop_crit_var.stop()
		if len(self.messages) > 1 and self.messages[-1]['role'] == 'user':
			self.messages.pop()

	def list_messages(self) -> list[dict[str, str]]:
		return self.messages[1:]

	def chat_template_msgs(self) -> list[dict[str, str]]:
		return [{
			key: value
			for key, value in msg.items()
			if key in ('role', 'content')
		} for msg in self.messages]

	def add_stream_msg(self):
		if self.gen_response:
			if self.is_generating:
				self.add_message('assistant', self.gen_response)
				self.is_generating = False

	def generate_stream(self, inputs:str|list[int]) -> Generator[str, Any, Any]:
		thread = Thread(target=self.pipe, args=[inputs], kwargs=self.pipe_cfg)
		thread.start()
		self.gen_response = ''
		for text_out in self.streamer:
			text = str(text_out)
			self.gen_response += text
			yield text

	def generate(self, prompt_text:str) -> str:
		# TextIteratorStreamer:  https://huggingface.co/docs/transformers/main/en/internal/generation_utils#transformers.TextIteratorStreamer.example
		# gen. utils:            https://huggingface.co/docs/transformers/main/en/internal/generation_utils
		# gen. strategy:         https://huggingface.co/docs/transformers/generation_strategies
		# chat template:         https://huggingface.co/docs/transformers/main/en/chat_templating
		# pipelines:             https://huggingface.co/docs/transformers/main_classes/pipelines

		prompt_text = prompt_text.strip()
		if not prompt_text:
			return ''

		self.is_generating = True
		print(f'> Generating response: {self.full_name}')
		self.add_message('user', prompt_text)
		self.stop_crit_var.reset()

		with torch.no_grad():
			with self.pipe.device_placement():
				inputs = self.pipe.tokenizer.apply_chat_template(self.chat_template_msgs(), **self.tokenizer_cfg)  #type:ignore
				outputs = self.pipe(inputs, **self.pipe_cfg)  #type:ignore
				# thread = Thread(target=self.pipe, args=[inputs], kwargs=self.pipe_cfg)
				# thread.start()
				# response = ''
				# for text_out in self.streamer:
				# 	response += text_out
				# 	print(text_out, end='')
				# print(end='\n', flush=True)
		# if response:
		# 	if self.is_generating:
		# 		self.add_message('assistant', response)
		# 		self.is_generating = False
		# 		return response
		if outputs:
			response = str(outputs[0]['generated_text']).strip()  #type:ignore
			if self.is_generating:
				self.add_message('assistant', response)
				self.is_generating = False
				return response
		return ''


# ====================================================================
def load_model() -> BaseLLM:
	if c.Env.DEV_MODE:
		return BaseLLM('Testing-LLM')
	return TextGenerationLLM(c.LLM_MODEL_NAME)


if __name__ == '__main__':
	llm = TextGenerationLLM(c.LLM_MODEL_NAME)

	prompt = 'Hello, what is the Sun?'
	print(f'> Prompt: {prompt}')
	print(f'> Response: {llm.generate(prompt)}')

	prompt = 'What about the Moon, Mars and other planets?'
	print(f'> Prompt: {prompt}')
	print(f'> Response: {llm.generate(prompt)}')
	raise SystemExit(0)
