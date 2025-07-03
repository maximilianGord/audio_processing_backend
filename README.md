# Introduction

This is the Backend from a private project I am working on with my friends now. My contribution to this project was the audio processing pipeline, which takes an dialogue audio and creates an transcript of two persons speaking. One can find it in app/audio_processing.I specifies the creation of SQL tables in app/models, in which information about the conversation is stored. Last but not least, I did the integration in the FastAPI Framework which was done together with : 
All this changes can be found in this subfolder that belongs to out project.


### 1. Clone the repository

```bash
git git@github.com:abTuring13/Memora.git
cd Memora
```

### 2. Prepare Database connection
Add your DB Parameters to api/app/core/config.py like this 

    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = "
    POSTGRES_DB: str = ""

### 3. Build & Run the Backend

#### 3.1 Creat and run the enviroment
Go into api
```bash
python -m venv .venv
source .venv/bin/activate  # on Linux/macOS
.venv\Scripts\activate    # on Windows
uv sync
```

#### 3.2 Install whisper and additional dependencies
```bash 
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

You have to install whisper now 

```bash 
uv pip install -U openai-whisper
uv pip install setuptools-rust
```

Run once again
```bash
uv sync
```
### Run the project
Make sure you have an .env file in you api folder with GEMINI_API_KEY and HF_TOKEN

run in you venv : 
```bash
uvicorn app.main:app --reload
```
