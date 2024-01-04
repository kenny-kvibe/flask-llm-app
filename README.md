# Flask LLM App

Flask App with Socket.IO running a Chat Web UI using a LLM (Text Generation: `HuggingFaceH4/zephyr-7b-beta`).

> Install Python package dependencies

```sh
pip install -r requirements.txt
```

> Install `Torch v2.1.1` with `CUDA v12.1` and `xformers v0.0.23`

```sh
python.exe -m pip install -U torch==2.1.1 torchvision torchaudio torchdiffeq torchsde xformers==0.0.23 --index-url https://download.pytorch.org/whl/cu121
```

> Run App

```sh
# Argument1 =>  OPEN_BROWSER  (open the web browser after app init) Default: 1
# Argument2 =>  DEV_MODE      (app development, no LLM gets loaded) Default: 0
python.exe -B main.py
python.exe -B main.py 0 0
```
