import dotenv
import os
import psutil
import socket
import sys


ROOT_PATH = os.path.dirname(__file__)

dotenv.load_dotenv(os.path.join(ROOT_PATH, '.env'))

BROWSER_BIN_PATH = os.path.join(
	os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Mozilla Firefox', 'private_browsing.exe')

APP_TITLE = 'Chat AI'

# HF:  https://huggingface.co/HuggingFaceH4/zephyr-7b-beta
LLM_MODEL_NAME = 'HuggingFaceH4/zephyr-7b-beta'


def get_local_ipv4(start_ipv4: str = '192.168.') -> str:
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

	OPEN_BROWSER = True
	DEV_MODE = False
	PORT = 80

	@classmethod
	def get_arg_env_bool(cls, arg_idx: int, env_key: str, default: bool = False) -> bool:
		if 0 < arg_idx < cls.argc:
			return sys.argv[arg_idx].lower() in cls.true_params
		return os.environ.get(env_key, '1' if default else '0').lower() in cls.true_params


class Env:
	OPEN_BROWSER = DefaultEnv.get_arg_env_bool(1, 'OPEN_BROWSER', DefaultEnv.OPEN_BROWSER)
	DEV_MODE     = DefaultEnv.get_arg_env_bool(2, 'DEV_MODE',     DefaultEnv.DEV_MODE)

	HOST = os.environ.get('HOST', '')
	if HOST == '':
		HOST = get_local_ipv4()

	try:
		PORT = int(os.environ.get('PORT', DefaultEnv.PORT))
	except ValueError:
		PORT = DefaultEnv.PORT
