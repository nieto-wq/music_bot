FROM python:3.11-slim

# Install ffmpeg (which provides ffprobe)
RUN apt-get update && apt-get install -y ffmpeg

# Create a working directory
WORKDIR /app

# Copy requirements, then install
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . /app

# Start your bot
CMD ["python", "music_bot.py"]
