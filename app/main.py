import constants as c
import llm_model
import web_app


def main() -> int:
	if c.Env.DEV_MODE:
		print('> Developer Mode Enabled!')
	web_app.main(llm_model.load_model())
	return 0


if __name__ == '__main__':
	raise SystemExit(main())
