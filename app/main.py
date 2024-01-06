import llm_model
import web_app


def main() -> int:
	web_app.main(llm_model.load())
	return 0


if __name__ == '__main__':
	raise SystemExit(main())
