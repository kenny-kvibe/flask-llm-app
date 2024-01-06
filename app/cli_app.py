import constants as c
import llm_model


def main() -> int:
	if c.Env.DEV_MODE:
		print('-- !! Developer Mode Enabled !! --')

	llm = llm_model.load()
	prompt = ''
	try:
		while (prompt := input('> Prompt: ')):
			llm.generate(prompt, False)
	except KeyboardInterrupt:
		print('> Interrupted: Ctrl-C\n', end='', flush=True)

	llm.stop_generating()
	print('> Exiting ...\n', end='', flush=True)
	return 0


if __name__ == '__main__':
	raise SystemExit(main())
