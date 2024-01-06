# [Flask LLM App](https://github.com/kenny-kvibe/flask-llm-app)

Flask App running a Chat Web UI with a LLM (Text Generation: `HuggingFaceH4/zephyr-7b-beta`).

The App will auto-open in Firefox (you can change it in `app/constants.py`).

-----

> Install Python package dependencies

```sh
pip install -r requirements.txt
```

-----

> Install `Torch == 2.1.2` with `CUDA == 12.1` and `xformers ~= 0.0.23`

```sh
python.exe -m pip install -U "torch==2.1.2" torchvision torchaudio torchdiffeq torchsde "xformers~=0.0.23" --index-url https://download.pytorch.org/whl/cu121
```

-----

> Run App (CLI, WebUI)

```sh
# Argument1 =>  OPEN_BROWSER  (open the web browser after app init) Default: "1"
# Argument2 =>  DEV_MODE      (app development, no LLM gets loaded) Default: "0"
# Argument `-B` =>  don't write byte-code in "__pycache__" folders
cd app
python.exe -B cli_app.py
python.exe -B web_app.py
```
