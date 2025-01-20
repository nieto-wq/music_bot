import discord
from discord.ext import commands
import yt_dlp
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

song_queue = []

COOKIES_ENV = os.environ.get("YT_COOKIES")  
if COOKIES_ENV:
    with open("cookies.txt", "w", encoding="utf-8") as f:
        f.write(COOKIES_ENV)

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    "cookiefile": "cookies.txt" if os.path.isfile("cookies.txt") else None,
    'youtube_include_dash_manifest': False
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command()
async def join(ctx):
    """Joins the voice channel the user is in."""
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("You need to be in a voice channel for me to join!")

@bot.command()
async def leave(ctx):
    """Leaves the voice channel if currently in one, and clears the queue."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue.clear()
        await ctx.send("Disconnected and cleared the queue.")
    else:
        await ctx.send("I'm not connected to a voice channel.")

@bot.command()
async def play(ctx, url):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You're not in a voice channel, and I'm not in one!")
            return
            
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            info = ytdl.extract_info(url, download=False)
            stream_url = info["url"]
            title = info.get("title", "Unknown Title")
    except Exception as e:
        await ctx.send(f"Failed to get video info: {e}")
        return

    song_queue.append({"url": stream_url, "title": title})

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"**Added to queue**: {title} (position {len(song_queue)})")

async def play_next(ctx):
    """Plays the next song in the queue, or leaves if the queue is empty."""
    if not song_queue:
        await ctx.send("peace")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        return

    next_song = song_queue.pop(0)
    url = next_song["url"]
    title = next_song["title"]

    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

    def after_playing(error):
        if error:
            print(f"Player error: {error}")
        future = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            future.result()
        except Exception as exc:
            print(f"Error in after_playing: {exc}")

    ctx.voice_client.play(source, after=after_playing)
    await ctx.send(f"**Now playing**: {title}")

@bot.command()
async def skip(ctx):
    """Skips the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipping to the next song...")
    else:
        await ctx.send("No song is currently playing!")


bot.run(os.environ["DISCORD_TOKEN"])
