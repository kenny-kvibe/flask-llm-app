# Flask LLM App

Flask App running a Chat Web UI using a LLM (Text Generation: `HuggingFaceH4/zephyr-7b-beta`).

The App will auto-open in Firefox (you can change it in `app/constants.py`)

-----

> Install Python package dependencies

```sh
pip install -r requirements.txt
```

-----

> Install `Torch v2.1.1` with `CUDA v12.1` and `xformers v0.0.23`

```sh
python.exe -m pip install -U torch==2.1.1 torchvision torchaudio torchdiffeq torchsde xformers==0.0.23 --index-url https://download.pytorch.org/whl/cu121
```

-----

> Run App

```sh
# Usage: "main.py Arg1 Arg2"
# Argument1 =>  OPEN_BROWSER  (open the web browser after app init) Default: "1"
# Argument2 =>  DEV_MODE      (app development, no LLM gets loaded) Default: "0"
# Argument `-B` =>  don't write byte-code in "__pycache__" folders
python.exe -B main.py
python.exe -B main.py 0
python.exe -B main.py 1 1
```
