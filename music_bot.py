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
inactivity_task = None  

COOKIES_ENV = os.environ.get("YT_COOKIES")
if COOKIES_ENV:
    with open("cookies.txt", "w", encoding="utf-8") as f:
        f.write(COOKIES_ENV)

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'ignoreerrors': True,
    'cookiefile': "cookies.txt" if os.path.isfile("cookies.txt") else None,
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
    global inactivity_task
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue.clear()
        
        if inactivity_task and not inactivity_task.done():
            inactivity_task.cancel()
            inactivity_task = None
        await ctx.send("bye, i cleared ur queue dummy")
    else:
        await ctx.send("im not connected lol")

@bot.command()
async def play(ctx, *, query):
    """Plays or queues audio from a YouTube link, mix, or search query."""
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
        logging.exception("Failed to get video info")
        return

    
    if 'entries' in info:
        playlist_title = info.get('title', 'Untitled Playlist')
        entries = info['entries']
        count = 0
        
        for entry in entries:
            if entry is None:
                continue
            track_url = entry.get('url')
            track_title = entry.get('title', 'Unknown Title')
            if track_url:
                song_queue.append({"url": track_url, "title": track_title})
                count += 1

        if count > 1:
            await ctx.send(f"here ugly i added **{count}** tracks from playlist: **{playlist_title}**")
        elif count == 1:
            await ctx.send(f"here ugly i added track to queue: **{track_title}** (Position {len(song_queue)})")
        else:
            await ctx.send("idk")
    else:
        
        stream_url = info.get("url")
        title = info.get("title", "Unknown Title")
        if stream_url:
            song_queue.append({"url": stream_url, "title": title})
            await ctx.send(f"**Added to queue**: {title} (position {len(song_queue)})")
        else:
            await ctx.send("that link booty.")

    
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    """Plays the next song in the queue or (if empty) schedules inactivity."""
    global inactivity_task

    if not song_queue:
       
        await ctx.send("No songs left in queue.")
        
        inactivity_task = asyncio.create_task(schedule_inactivity_timeout(ctx, 120))
        return

    
    if inactivity_task and not inactivity_task.done():
        inactivity_task.cancel()
        inactivity_task = None

    next_song = song_queue.pop(0)
    url = next_song["url"]
    title = next_song["title"]

    try:
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
    except Exception as e:
        await ctx.send(f"Error creating source for {title}: {e}")
        logging.exception("FFmpeg error")
        
        return await play_next(ctx)

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
        await ctx.send("poopy song, skip!")
    else:
        await ctx.send("bruh r u dum no song is playing!")

async def schedule_inactivity_timeout(ctx, wait_time: int):
    """Wait for `wait_time` seconds, then disconnect if still not playing."""
    try:
        await asyncio.sleep(wait_time)
    except asyncio.CancelledError:
        
        return

    
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await ctx.send("peace")
        await ctx.voice_client.disconnect()
        song_queue.clear()

bot.run(os.environ["DISCORD_TOKEN"])
