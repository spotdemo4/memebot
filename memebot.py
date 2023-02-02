from __future__ import unicode_literals
from ffprobe import FFProbe
from moviepy.editor import *
import yt_dlp
import yt_dlp.utils
import yt_dlp.version
import random
import os
import glob
import discord
from discord import app_commands
import subprocess
import ffmpeg
import re
import config
import json

class Video:
    def __init__(self, url, spoiler, meme, text):
        self.url = url
        self.spoiler = spoiler
        self.meme = meme
        self.text = text

        # Download video
        if spoiler == True:
            genfile = "./memes/SPOILER_" + str(random.randint(0, 1000000))
        else:
            genfile = "./memes/" + str(random.randint(0, 1000000))

        # Test if video file already exists
        for vidfile in glob.glob(genfile + '.*'):
            if spoiler == True:
                genfile = "./memes/SPOILER_" + str(random.randint(0, 1000000))
            else:
                genfile = "./memes/" + str(random.randint(0, 1000000))
        
        # Get rid of text if meme
        if meme:
            self.text = ''

        downloadVid(genfile, url)

        # Get filename
        for vidfile in glob.glob(genfile + '.*'):
            filepath = vidfile
            filename = filepath.split('/')[2]

        # Get extension
        self.fileext = filename.split('.')[1]

        # If not video
        if(self.fileext == "png" or self.fileext == "jpg"):
            raise ValueError("Can only accept video files")

        self.filepath = filepath
        self.filename = filename

    def convert(self, videoformat):
        print("[convert] " + self.filename + " to " + videoformat)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + ".mp4"
        self.filepath = "." + self.filepath.split('.')[1] + ".mp4"
        self.fileext = "mp4"
        video = ffmpeg.output(video, self.filepath, format=videoformat).global_args(
            '-loglevel', 'error')
        ffmpeg.run(video)
        os.remove(oldfilepath)

    def compress(self):
        print("[compress] " + self.filename)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "0." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "0." + self.fileext
        try:
            #ffvideo = ffmpeg.output(video, self.filepath, crf=32, vf='scale=-2:ih/2', format='mp4').global_args('-loglevel', 'error')
            ffvideo = ffmpeg.output(video, self.filepath, crf=30, format='mp4').global_args('-loglevel', 'error')
            ffmpeg.run(ffvideo)
        except ffmpeg.Error as e:
            print("FFmpeg error, retrying...")
            ffvideo = ffmpeg.output(video, self.filepath, crf=30, format='mp4').global_args('-loglevel', 'error')
            ffmpeg.run(ffvideo, overwrite_output=True)
        os.remove(oldfilepath)

    def convertH264(self):
        print("[convert H264] " + self.filename)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "1." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "1." + self.fileext
        video = ffmpeg.output(video, self.filepath, vcodec='libx264', crf=20, format='mp4').global_args('-loglevel', 'error')
        ffmpeg.run(video)
        os.remove(oldfilepath)

    def addCaption(self):
        print("[Adding caption]")
        #Gets video and sets position to bottom center
        video = VideoFileClip(self.filepath).set_position(("center", "bottom"))

        #Creates caption that goes above video
        text = TextClip(getDescription(self.url), fontsize=55, color='white', font='Roboto-Regular', align='center', size=(video.size[0] - 10, None), method='caption').set_position(('center', "top")).set_duration(video.duration)

        #Creates background border
        video = video.on_color(color=(54,57,63), size=(video.size[0], video.size[1] + text.size[1]), pos=(("bottom")))

        result = CompositeVideoClip([video, text])

        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "5." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "5." + self.fileext

        result.write_videofile(self.filepath)
        os.remove(oldfilepath)

    def delete(self):
        print("[deleted] " + self.filename)
        os.remove(self.filepath)

    def upload(self, message = None, interaction = None):
        print("[upload] " + self.filename)

        if message:
            msg = message.channel.send(self.text, file=discord.File(self.filepath))
        
        if interaction:
            msg = interaction.followup.send(self.text, file=discord.File(self.filepath))

        return msg
    
    def uploadRemote(self):
        print("[upload remote] " + self.filename)

        weirdchars = "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"
        url = subprocess.run(["curl", "-F", "file=@" + self.filepath, config.REMOTE_UPLOAD_URL], stdout=subprocess.PIPE).stdout.decode('utf-8')
        formattedUrl = json.loads(url)

        return weirdchars + " https://p.trev.xyz/-" + formattedUrl["id"] + "/" + self.filename

def downloadVid(filename, url):
    yt_dlp.utils.std_headers['User-Agent'] = 'facebookexternalhit/1.1'
    if "instagram.com" in url:
        ydl_opts = {'outtmpl': filename + '.%(ext)s', 'cookiefile': config.COOKIE_FILE}
    elif "tiktok.com" in url and '@' not in url:
        url = subprocess.run(["curl", "-o", "/dev/null", "--silent", url, "-w", "'%{redirect_url}'"], stdout=subprocess.PIPE).stdout.decode('utf-8')[1:-1]
        print("TIKTOK REDIRECT URL: " + url)
        ydl_opts = {'outtmpl': filename + '.%(ext)s'}
    elif "youtu.be" in url or "youtube.com/watch?v=" in url:
        ydl_opts = {'outtmpl': filename + '.%(ext)s', 'format': '[height<=720]'}
    else:
        ydl_opts = {'outtmpl': filename + '.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def getURL(url):
    ydl_opts = {'cookiefile': config.COOKIE_FILE}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("url", None)

def getCodec(filepath):
    metadata = FFProbe(filepath)
    for stream in metadata.streams:
        if stream.is_video():
            return stream.codec_name

def getDescription(url):
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)

    desc = ydl.sanitize_info(info)["description"]
    
    #remove URLs
    desc = re.sub(r'http\S+', '', desc)
    #remove special chars
    desc = desc.replace("amp;", "")
    
    return desc

async def sendError(author, error):
    print(error)
    if(author.id == config.ADMIN_ID):
        await author.send(error)

async def processMessage(message, caption=False):
    # Get URL
    url = re.search("(?P<url>https?://[^\\s]+)", message.content).group("url")
    text = message.content.replace(url, "").replace("!dl", "").replace("!caption", "").strip()

    # Download Video
    try:
        # Check if edgy/spoiler
        if 'edgy' in message.content.lower() or message.channel.id == 658455491118235648 or 'spoiler' in message.content.lower():
            spoiler = True
        else:
            spoiler = False

        # Check if meme
        if message.channel.id == config.MEME_CHANNEL_ID:
            meme = True
        else:
            meme = False

        video = Video(url, spoiler, meme, text)
    except Exception as ex:
        await sendError(message.author, "[ERROR] Download error: " + str(ex))
        return

    # Makes sure the video ext is mp4
    if(video.fileext != "mp4"):
        video.convert("mp4")

    # Make sure the video codec isnt hevc
    codec = getCodec(video.filepath)
    if codec == "hevc":
        video.convertH264()

    # Makes sure video is correct size
    if(os.path.getsize(video.filepath) > 8000000):
        video.compress()

    #Adds caption if true
    if(caption == True):
        video.addCaption()

    print("Downloaded " + video.filename + " to " + video.filepath)
    msg = ''

    # Uploads file
    try:
        msg = await video.upload(message=message)

    # If file too big
    except discord.errors.HTTPException as ex:
        msg = await message.channel.send(video.uploadRemote())
        video.delete()
    except Exception as ex:
        await sendError(message.author, "[ERROR] Upload error: " + str(ex))
        video.delete()

    # if message exists
    if msg != '':
        
        # Delete original message
        try:
            await message.delete()
        except Exception:
            await sendError(message.author, "[ERROR] Could not delete message.")

        # reacts to upload with emoji
        authorid = str(message.author.id)
        for user in config.USER_EMOJIS:
            if(authorid == user[0]):
                emoji = await msg.guild.fetch_emoji(user[1])
                await msg.add_reaction(emoji)

async def processInteraction(interaction, url, spoiler, caption=False):
    # Get URL
    url = re.search("(?P<url>https?://[^\\s]+)", url).group("url")

    # Download Video
    try:
        # Check if meme
        if interaction.channel_id == config.MEME_CHANNEL_ID:
            meme = True
        else:
            meme = False

        # Don't embed
        text = "<" + url + ">"
        video = Video(url, spoiler, meme, text)
    except Exception as ex:
        interaction.response.send_message("Error: " + str(ex), ephemeral=True)
        return
    
    # Makes sure the video ext is mp4
    if(video.fileext != "mp4"):
        video.convert("mp4")

    # Make sure the video codec isnt hevc
    codec = getCodec(video.filepath)
    if codec == "hevc":
        video.convertH264()

    # Makes sure video is correct size
    if(os.path.getsize(video.filepath) > 8000000):
        video.compress()

    #Adds caption if true
    if(caption == True):
        video.addCaption()
    
    print("Downloaded " + video.filename + " to " + video.filepath)

    # Uploads file
    try:
        await video.upload(interaction=interaction)

    # If file too big
    except discord.errors.HTTPException as ex:
        await interaction.followup.send(video.uploadRemote())
        video.delete()
    except Exception as ex:
        await interaction.followup.send("ERROR upload error: " + str(ex), ephemeral=True)
        video.delete()

async def processEmbed(interaction, url):
    # Get URL
    url = re.search("(?P<url>https?://[^\\s]+)", url).group("url")

    video_url = getURL(url)
    print(video_url)
    weirdchars = "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"

    try:
        await interaction.followup.send(weirdchars + video_url)
    except Exception as ex:
        await interaction.followup.send("ERROR: " + str(ex), ephemeral=True)

print("yt_dlp version: " + yt_dlp.version.__version__)
intents = discord.Intents.default()
intents.emojis_and_stickers = True
intents.messages = True
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@tree.command(name = "embed", description = "embed video from URL", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_embed(interaction, url: str, spoiler: bool = False):
    await interaction.response.defer(thinking = True)
    await processInteraction(interaction, url, spoiler)

@tree.command(name = "caption", description = "embed video from URL and add caption", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_caption(interaction, url: str, spoiler: bool = False):
    await interaction.response.defer(thinking = True)
    await processInteraction(interaction, url, spoiler, caption = True)

@tree.command(name = "embednodl", description = "embed video URL without download", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_embedtest(interaction, url: str):
    await interaction.response.defer(thinking = True)
    await processEmbed(interaction, url)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.GUILD_ID))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_raw_reaction_add(payload):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = client.get_user(payload.user_id)
    if not user:
        user = await client.fetch_user(payload.user_id)

    if(str(payload.emoji) == '🥞'):
        print("Processing message: " + message.content)
        await processMessage(message)

@client.event
async def on_message(message):
    global lastmedia

    # don't respond to ourselves
    if message.author == client.user:
        return
    elif "!getprofilepic" in message.content:
        await message.author.send(message.author.avatar_url)
    elif "youtube.com/watch?v=" in message.content or "youtu.be/" in message.content:
        if message.channel.id == config.MEME_CHANNEL_ID or "!dl" in message.content:
            await processMessage(message)
    elif any(ele in message.content for ele in config.FILTERS):
        await processMessage(message)

client.run(config.DISCORD_API_KEY)
print("Success")
