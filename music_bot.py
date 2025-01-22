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
        await ctx.send("lmao pea brain dimwit join a vc")

@bot.command()
async def leave(ctx):
    """Leaves the voice channel if currently in one, and clears the queue."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue.clear()
        await ctx.send("im out, and i cleared ur queue dummy")
    else:
        await ctx.send("i aint connected lol")

@bot.command()
async def play(ctx, *, query):
    
     if not (query.startswith("http://") or 
            query.startswith("https://") or 
            query.startswith("www.") or 
            "youtube.com" in query or 
            "youtu.be" in query):
        query = f"ytsearch1:{query}"
        
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("join a voice channel brah")
            return
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            info = ytdl.extract_info(query, download=False)
    except Exception as e:
        await ctx.send(f"Failed to get video info: {e}")
        return
    if 'entries' in info:
        playlist_title = info.get('title', 'Untitled Playlist')
        entries = info['entries']
        count = 0

        for entry in entries:
            if entry is None:
                continue
            track_url = entry['url']
            track_title = entry.get('title', 'Unknown Title')
            song_queue.append({"url": track_url, "title": track_title})
            count += 1

        await ctx.send(f"holy guacamole! added **{count}** tracks from playlist: **{playlist_title}**")

    else:
        stream_url = info["url"]
        title = info.get("title", "Unknown Title")
        song_queue.append({"url": stream_url, "title": title})
        await ctx.send(f"**Added to queue**: {title} (position {len(song_queue)})")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

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
        await ctx.send("L bumps, skip!")
    else:
        await ctx.send("bruh is u dum no song playing!")


bot.run(os.environ["DISCORD_TOKEN"])
