import constants as c
import llm_model
import web_app


def main() -> int:
	if c.Env.DEV_MODE:
		print('> Developer Mode Enabled!')
	llm = llm_model.load_model()
	app = web_app.create_web_app(llm)
	web_app.run_web_app(app, c.Env.HOST, c.Env.PORT)
	return 0


if __name__ == '__main__':
	raise SystemExit(main())
