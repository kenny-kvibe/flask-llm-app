#pyright: reportUnusedFunction=none
import os
import subprocess as sp
import time
from flask import Flask, Blueprint, render_template, request
from markupsafe import Markup
from waitress import serve
from werkzeug.exceptions import HTTPException
from urllib.parse import urlparse, urlunparse
from typing import Any

import constants as c
import llm_model


def main() -> int:
	if c.Env.DEV_MODE:
		print('-- !! Developer Mode Enabled !! --')
	llm = llm_model.load(True)
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
	return serve(app, host=host, port=port)


def open_in_firefox(host:str, port:int, width:int = -1, height:int = -1):
	try:
		command = [c.BROWSER_BIN_PATH, f'http://{host}:{port}']
		if width > -1:
			command.extend([ '-width', str(width) ])
		if height > -1:
			command.extend([ '-height', str(height) ])
		return sp.run(
			command,
			stdout=sp.PIPE,
			stderr=sp.PIPE,
			shell=True)
	except Exception as exc:
		print(f'{exc.__class__.__name__}: {exc}\n', end='', flush=True)


def init_app_filters(app:Flask):
	# === filter: base_url ==============================
	@app.template_filter('base_url')
	def base_url(url:str):
		urlp = urlparse(url)
		return f'{urlp.scheme}://{urlp.netloc}'

	# === filter: replace_url_port ==============================
	@app.template_filter('replace_url_port')
	def replace_url_port(url:str, port:int):
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

	def json_response(message:Any, code:int = 200, data:dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
		response = { 'message': str(message) }
		if data is not None:
			response.update(data)
		return response, code

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
					return json_response('OK')
				return json_response('ERROR: NO PROMPT TEXT', 400)
			return json_response('ERROR: NO POST DATA', 400)

		return render_template(
			'index.html',
			head_title=c.APP_TITLE)

	# === route: llm_list_msgs ==============================
	@view.route('/llm-list-msgs', methods=['POST'])
	def llm_list_msgs():
		return json_response('OK', 200, {
			'is-generating': llm.is_generating,
			'gen-response': {
				'role': 'assistant',
				'name': llm.name_map['assistant'],
				'text': Markup.escape(llm.gen_response),
				'date': llm.date_now()
			},
			'messages-list': [{
				'role': msg['role'],
				'name': llm.name_map[msg['role']],
				'text': Markup.escape(msg['content']),
				'date': msg['date']
			} for msg in llm.list_messages()]
		})

	# === route: llm_reset_msgs ==============================
	@view.route('/llm-reset-msgs', methods=['POST'])
	def llm_reset_msgs():
		try:
			llm.stop_generating()
			llm.reset_messages()
		except Exception as exc:
			return json_response(exc, 500)
		return json_response('OK', 200)

	# === route: llm_stop_gen ==============================
	@view.route('/llm-stop-gen', methods=['POST'])
	def llm_stop_gen():
		try:
			llm.stop_generating()
		except Exception as exc:
			return json_response(exc, 500)
		return json_response('OK', 200)

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
