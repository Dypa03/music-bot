import asyncio
import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("discord_token")

# Permettiamo al bot di poter ricevere tutti i tipi di eventi
intents = discord.Intents().all()
# Istanza del client
client = discord.Client(intents=intents)
# Istanza del bot
bot = commands.Bot(command_prefix="!", intents=intents)


# Downloading the audio file from Youtube

# Surpress any bug report message
# (yt-dlp doesn't use this functionality)

# Format Options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses
}

# Options for processing the downloaded audio
ffmpeg_options = {
  'executable': "./ffmpeg.exe",
  'options': '-vn'
}

# Import yt_dlp instead of youtube_dl
from yt_dlp import YoutubeDL

ytdl = YoutubeDL(ytdl_format_options)

# Wrapper to manage audio downloaded form YT
class YTDLSource(discord.PCMVolumeTransformer):
    """
    init arguments:
    - source: represents the original audio source
    - data: stores information about the downloaded audio
    - volume: ...
    """
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    # Class methods can be called directly without needing an istance of the class
    """
    method arguments:
    - cls: it refers to the class itself
    - url: yt url
    - loop: event loop
    - stream: this arguments decide if download the entire audio file
    """

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # We use the loop to extract information from the YT video
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        # Checks if the downloaded information contains a playlist
        if 'entries' in data:
            #take first item from a playlist
            data = data['entries'][0]

        # We determine the filename
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

# Adding bot commands

# Join command
# Decorator that defines the discord command
@bot.command(name="join", help="Tells the bot to join the voice channel")
async def join(ctx): # ctx is the context of the command invocation(user, channel, message, etc.)
    
    # We check if the user is connected to a voice channel
    if not ctx.message.author.voice:
        # Send error message
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        # Joins the user channel
        channel = ctx.message.author.voice.channel
    await channel.connect()

# Leave command
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    # Retrieve information about the bot current voice connection
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

# Play command
@bot.command(name='play', help='To play song')
async def play(ctx, url):
    try:
        # Check voice channel
        server = ctx.message.guild
        voice_channel = server.voice_client

        # We set the bot to typing state while the download is happening 
        async with ctx.typing():
            # We download the audio
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            # Play the audio
            voice_channel.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=filename))
        await ctx.send("**Now playing:** {}".format(filename))
    except:
        # Error message
        await ctx.send("The bot is not connected to a voice channel.")

# Pause command
@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

# Resume command
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

# Stop command
@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

bot.run(DISCORD_TOKEN)