import dotenv
import os
import psutil
import socket
import sys
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)


ROOT_PATH = os.path.dirname(__file__)
dotenv.load_dotenv(os.path.join(ROOT_PATH, '.env'))


BROWSER_BIN_PATH   = os.path.join(os.environ['PROGRAMFILES'], 'Mozilla Firefox', 'private_browsing.exe')
TRANSFORMERS_CACHE = os.path.join(os.environ['USERPROFILE'], '.transformers_cache')


APP_TITLE = 'Flask LLM'

# HF:  https://huggingface.co/HuggingFaceH4/zephyr-7b-beta
# HF:  https://huggingface.co/argilla/notus-7b-v1

LLM_MODEL_NAME = 'HuggingFaceH4/zephyr-7b-beta'
# LLM_MODEL_NAME = 'argilla/notus-7b-v1'


def get_local_ipv4(start_ipv4:str = '192.168.') -> str:
	""" Get the first IPv4 address that starts with `start_ipv4` or get `'127.0.0.1'` """
	interfaces = psutil.net_if_addrs()
	for ifs in interfaces.values():
		for addr in ifs:
			if addr.family == socket.AF_INET and addr.address.startswith(start_ipv4):
				return addr.address
	return '127.0.0.1'


class DefaultEnv:
	argc = len(sys.argv)
	true_params = ('1', 'true', 'y', 'yes', True, 1)

	OFFLINE_MODE = False
	OPEN_BROWSER = True
	DEV_MODE = False
	PORT = 80

	@classmethod
	def get_env_int(cls, env_key:str, default:int = 0) -> int:
		try:
			return int(os.environ.get(env_key, default))
		except ValueError:
			return default

	@classmethod
	def get_env_bool(cls, env_key:str, default:bool = False) -> bool:
		return os.environ.get(env_key, '1' if default else '0').lower() in cls.true_params

	@classmethod
	def get_arg_env_bool(cls, arg_idx:int, env_key:str, default:bool = False) -> bool:
		if 0 < arg_idx < cls.argc:
			return sys.argv[arg_idx].lower() in cls.true_params
		return cls.get_env_bool(env_key, default)


class Env:
	OPEN_BROWSER = DefaultEnv.get_arg_env_bool(1, 'OPEN_BROWSER', DefaultEnv.OPEN_BROWSER)
	DEV_MODE     = DefaultEnv.get_arg_env_bool(2, 'DEV_MODE',     DefaultEnv.DEV_MODE)
	OFFLINE_MODE = DefaultEnv.get_env_bool(       'OFFLINE_MODE', DefaultEnv.OFFLINE_MODE)
	PORT         = DefaultEnv.get_env_int(        'PORT',         DefaultEnv.PORT)

	HOST = os.environ.get('HOST', '')
	if HOST == '':
		HOST = get_local_ipv4()


os.environ['HF_DATASETS_OFFLINE'] = '1' if Env.OFFLINE_MODE else '0'
os.environ['TRANSFORMERS_OFFLINE'] = '1' if Env.OFFLINE_MODE else '0'
os.environ['TRANSFORMERS_CACHE'] = TRANSFORMERS_CACHE
os.environ['HF_HOME'] = TRANSFORMERS_CACHE
