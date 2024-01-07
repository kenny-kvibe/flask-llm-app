import constants as c

import gc
import time
import torch
from datetime import datetime as dt
from threading import Thread
from transformers import pipeline, TextIteratorStreamer
from transformers.generation.stopping_criteria import StoppingCriteria, StoppingCriteriaList
from transformers.models.auto import AutoTokenizer, AutoModelForCausalLM
from typing import TypeAlias


LLM:TypeAlias = 'BaseLLM | TextGenerationLLM'


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
class BaseLLM:
	def __init__(self, name:str, device:str = 'auto'):
		if device == 'auto':
			device = 'cuda' if torch.cuda.is_available() else 'cpu'
		self.device = torch.device(device)
		self.name = name
		self.short_name = name.split('/', 1)[-1]
		self.name_map = {'user': 'You', 'assistant': self.short_name}
		self.gen_prompt = ''
		self.gen_response = ''
		self.is_generating = False
		print(f'> Loading {self.__class__.__name__}: {self.full_name}')
		self.reset_messages()
		self.clear_cache()

	@property
	def full_name(self) -> str:
		return f'{self.name} ({self.device.type})'

	@classmethod
	def clear_cache(cls):
		gc.collect()
		torch.cuda.empty_cache()

	@classmethod
	def date_now(cls) -> str:
		return dt.now().strftime('%d.%m.%Y %H:%M:%S')

	@classmethod
	def create_message(cls, role:str, content:str) -> dict[str, str]:
		return {
			'role': role,
			'content': content.strip(),
			'date': cls.date_now() }

	def add_message(self, role:str, content:str):
		self.messages.append(self.create_message(role, content))

	def reset_messages(self):
		self.messages:list[dict[str, str]] = []

	def list_messages(self) -> list[dict[str, str]]:
		return self.messages[:]

	def print_memory_info(self):
		print(str(torch.cuda.memory_summary(device=self.device, abbreviated=True)))

	def stop_generating(self):
		if self.is_generating is False:
			return
		self.is_generating = False
		if len(self.messages) > 0 and self.messages[-1]['role'] == 'user':
			self.messages.pop()

	def generate(self, prompt_text:str, print_prompt:bool = False):
		sec, gen_wait_sec = 0, 7
		self.is_generating = True
		self.gen_prompt = prompt_text.strip()

		if print_prompt:
			print(f'> Prompt: {self.gen_prompt}\n', end='', flush=True)

		self.add_message('user', self.gen_prompt)

		while self.is_generating and sec < gen_wait_sec:
			time.sleep(1)
			sec += 1

		self.gen_response = f'Done generating, prompt: "{self.gen_prompt}" ({gen_wait_sec} seconds)'
		print('> Response:\n', self.gen_response, '\n', sep='', end='', flush=True)
		if self.is_generating:
			self.add_message('assistant', self.gen_response)
			self.is_generating = False


# ====================================================================
class TextGenerationLLM (BaseLLM):
	def __init__(self, name:str, device:str = 'auto', init_text_streamer:bool = True):
		self.system_prompt = (
			'Always Remember: '
			'You\'re a technical AI assistant, a senior programmer and you know a lot about Python. '
			'You respond in a very short answer, straight to the point and answer truthfully, '
			'do not explain yourself just simply give a short answer.')

		super(self.__class__, self).__init__(name, device)

		self.stop_crit_var = VariableStopCriteria()

		self.pipeline_cfg:dict = dict(
			device_map=self.device,
			framework='pt',
			return_full_text=False,
			torch_dtype=torch.bfloat16,
			trust_remote_code=False)

		self.pipe_cfg:dict = dict(
			# batch_size=8,
			do_sample=True,
			# max_length=1024,
			max_new_tokens=512,
			num_return_sequences=1,
			stopping_criteria=StoppingCriteriaList([self.stop_crit_var]),
			temperature=0.9,
			top_k=50,
			top_p=1.0,
			use_cache=True)

		self.tokenizer_cfg:dict = dict(
			add_generation_prompt=True,
			return_tensors='pt',
			tokenize=False)

		self.text_iter_cfg:dict = dict(
			clean_up_tokenization_spaces=None,
			skip_prompt=True,
			skip_special_tokens=True,
			timeout=None)

		with torch.no_grad():
			self.pipe_thread = None
			self.pipe = pipeline(
				task='text-generation',
				model=self.name,
				**self.pipeline_cfg)

			with self.pipe.device_placement():
				if self.pipe.model is None:
					self.pipe.model = AutoModelForCausalLM.from_pretrained(self.name, **self.pipeline_cfg)

				if self.pipe.tokenizer is None:
					self.pipe.tokenizer = AutoTokenizer.from_pretrained(self.name, device_map=self.device)

				if init_text_streamer:
					self.text_iter_streamer = TextIteratorStreamer(self.pipe.tokenizer, **self.text_iter_cfg)  #type:ignore
					self.pipe_cfg['streamer'] = self.text_iter_streamer
				else:
					self.text_iter_streamer = None

	def reset_messages(self):
		self.messages = [self.create_message('system', self.system_prompt)]

	def join_pipe_thread(self):
		if self.pipe_thread is not None:
			while self.pipe_thread.is_alive():
				self.pipe_thread.join(0)
				time.sleep(0.01)
			self.pipe_thread = None

	def stop_generating(self):
		if self.is_generating is False:
			return
		self.is_generating = False
		self.stop_crit_var.stop()
		if self.text_iter_streamer is not None:
			self.join_pipe_thread()
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

	def generate(self, prompt_text:str, print_prompt:bool = False):
		# TextIteratorStreamer:  https://huggingface.co/docs/transformers/main/en/internal/generation_utils#transformers.TextIteratorStreamer.example
		# gen. utils:            https://huggingface.co/docs/transformers/main/en/internal/generation_utils
		# gen. strategy:         https://huggingface.co/docs/transformers/generation_strategies
		# chat template:         https://huggingface.co/docs/transformers/main/en/chat_templating
		# pipelines:             https://huggingface.co/docs/transformers/main_classes/pipelines

		self.gen_prompt = prompt_text.strip()
		self.gen_response = ''
		if not self.gen_prompt:
			return print('> Error: Prompt text is empty!')

		if self.pipe.tokenizer is None:
			return print('> Error: No tokenizer loaded!')

		self.is_generating = True

		if print_prompt:
			print(f'> Prompt: {self.gen_prompt}\n', end='', flush=True)

		self.add_message('user', self.gen_prompt)
		self.stop_crit_var.reset()

		with torch.no_grad():
			with self.pipe.device_placement():
				inputs = self.pipe.tokenizer.apply_chat_template(self.chat_template_msgs(), **self.tokenizer_cfg)
				if self.text_iter_streamer is None:
					outputs = self.pipe(inputs, **self.pipe_cfg)  #type:ignore
					if outputs:
						self.gen_response = str(outputs[0]['generated_text']).strip()  #type:ignore
					print(f'> Response:\n{self.gen_response}\n> Done.\n', end='', flush=True)
				else:
					self.pipe_thread = Thread(target=self.pipe, args=[inputs], kwargs=self.pipe_cfg)
					self.pipe_thread.start()
					print('> Response:\n', end='', flush=True)
					for text_out in self.text_iter_streamer:
						self.gen_response += text_out
						print(text_out, end='', flush=True)
					print('\n> Done.\n', end='', flush=True)

		if self.gen_response and self.is_generating:
			self.add_message('assistant', self.gen_response)
			if self.text_iter_streamer is not None:
				self.join_pipe_thread()
			self.is_generating = False


# ====================================================================
def load(text_streamer:bool = True) -> LLM:
	if c.Env.DEV_MODE:
		return BaseLLM('Testing-LLM')
	return TextGenerationLLM(c.LLM_MODEL_NAME, 'cuda', text_streamer)


if __name__ == '__main__':
	llm = TextGenerationLLM(c.LLM_MODEL_NAME, init_text_streamer=False)
	llm.generate('Hello, explain in a short answer, what is an apple tree?', True)
	llm.generate('What about strawberries?', True)
	raise SystemExit(0)
