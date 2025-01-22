# 1. Start from a lightweight Python 3.11 base
FROM python:3.11-slim

# 2. Install ffmpeg (so 'ffprobe' is available for Discord music)
RUN apt-get update && apt-get install -y ffmpeg

# 3. Create and switch to a working directory
WORKDIR /app

# 4. Copy requirements.txt into the container, then install
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code into the container
COPY . /app

# 6. Finally, run your Python bot
CMD ["python", "music_bot.py"]
