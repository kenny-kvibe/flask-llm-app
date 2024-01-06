#pyright: reportUnusedFunction=none
import os
import subprocess as sp
import time
from flask import Flask, Blueprint, render_template, request
from markupsafe import Markup
from waitress import serve
from werkzeug.exceptions import HTTPException
from urllib.parse import urlparse, urlunparse

import constants as c
import llm_model


def main() -> int:
	if c.Env.DEV_MODE:
		print('-- !! Developer Mode Enabled !! --')
	llm = llm_model.load()
	app = create_app(llm)
	run_app(app, c.Env.HOST, c.Env.PORT)
	return 0


def create_app(llm:llm_model.LLM) -> Flask:
	app = Flask(__name__)
	app.config['SECRET_KEY'] = os.urandom(32).hex()
	init_app_filters(app)
	init_app_routes(app, llm)
	return app


def run_app(app:Flask, host:str, port:int):
	if c.Env.OPEN_BROWSER:
		os.environ['OPEN_BROWSER'] = ''
		open_in_firefox(host, port, 1000, 1000)
		time.sleep(0.3)

	if c.Env.DEV_MODE:
		return app.run(
			host=host,
			port=port,
			debug=True,
			load_dotenv=False,
			use_debugger=True,
			use_reloader=True)

	print(f'Serving on http://{host}:{port} ...\n', end='', flush=True)
	serve(app, host=host, port=port)


def open_in_firefox(host:str, port:int, width:int = -1, height:int = -1):
	try:
		command = [c.BROWSER_BIN_PATH, f'http://{host}:{port}']
		if width > -1:
			command.extend([ '-width', str(width) ])
		if height > -1:
			command.extend([ '-height', str(height) ])
		sp.run(command,
			stdout=sp.PIPE,
			stderr=sp.PIPE,
			shell=True)
	except Exception as e:
		print(f'{e.__class__.__name__}: {e}\n', end='', flush=True)


def init_app_filters(app:Flask):
	# === filter: base_url ==============================
	@app.template_filter('base_url')
	def base_url(url: str):
		urlp = urlparse(url)
		return f'{urlp.scheme}://{urlp.netloc}'

	# === filter: replace_url_port ==============================
	@app.template_filter('replace_url_port')
	def replace_url_port(url: str, port: int):
		urlp = urlparse(url)
		netloc = urlp.netloc.split(':')[0]
		if port not in (80, 443):
			netloc += f':{port}'
		return urlunparse(urlp._replace(netloc=netloc))


def init_app_routes(app:Flask, llm:llm_model.LLM):
	view = Blueprint(
		'view',
		app.import_name,
		static_folder='static',
		template_folder='templates',
		url_prefix='/')

	# === route: index ==============================
	@view.route('/', methods=['GET', 'POST'])
	def index():
		if request.method == 'POST' and request.is_json:
			data = request.get_json(silent=True)
			if data:
				input_text = data.get('prompt', '').strip()
				if input_text:
					print(f'> [POST]\n', end='', flush=True)
					print(f'> Generating: {llm.full_name}')
					llm.generate(input_text, True)
					return { 'message': 'OK' }, 200
				return { 'message': 'ERROR: NO PROMPT TEXT', 'error': True }, 400
			return { 'message': 'ERROR: NO POST DATA', 'error': True }, 400

		return render_template(
			'index.html',
			head_title=c.APP_TITLE)

	# === route: llm_list_msgs ==============================
	@view.route('/llm-list-msgs', methods=['POST'])
	def llm_list_msgs():
		return {
			'message': 'OK',
			'prompt': llm.gen_prompt,
			'response': llm.gen_response,
			'messages-list': [{
				'name': llm.name_map[msg['role']],
				'date': msg['date'],
				'text': Markup.escape(msg['content'])
			} for msg in llm.list_messages()],
			'is-generating': llm.is_generating
		}, 200

	# === route: llm_reset_msgs ==============================
	@view.route('/llm-reset-msgs', methods=['POST'])
	def llm_reset_msgs():
		try:
			llm.stop_generating()
			llm.reset_messages()
		except Exception as e:
			return { 'message': str(e), 'error': True }, 500
		return { 'message': 'OK' }, 200

	# === route: llm_stop_gen ==============================
	@view.route('/llm-stop-gen', methods=['POST'])
	def llm_stop_gen():
		try:
			llm.stop_generating()
		except Exception as e:
			return { 'message': str(e), 'error': True }, 500
		return { 'message': 'OK' }, 200

	# === route: error_handler ==============================
	@app.errorhandler(HTTPException)
	def error_handler(error):
		return render_template(
			'error.html',
			head_title=f'{c.APP_TITLE} - Error: {error.code}',
			error=error)

	app.register_blueprint(view)


if __name__ == '__main__':
	raise SystemExit(main())
