from ffprobe import FFProbe
from moviepy.editor import *
from b2sdk.v2 import *
import yt_dlp
import yt_dlp.utils
import yt_dlp.version
import random
import os
import glob
import discord
import subprocess
import ffmpeg
import re
import config
import typing
import functools


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
        if (self.fileext == "png" or self.fileext == "jpg"):
            raise ValueError("Can only accept video files")

        self.filepath = filepath
        self.filename = filename

    async def convert(self, videoformat):
        print("[convert] " + self.filename + " to " + videoformat)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + ".mp4"
        self.filepath = "." + self.filepath.split('.')[1] + ".mp4"
        self.fileext = "mp4"

        ffvideo = ffmpeg.output(video, self.filepath, format=videoformat).global_args(
            '-loglevel', 'error')
        await run_blocking(ffmpeg.run, ffvideo)
        os.remove(oldfilepath)

    async def compress(self):
        print("[compress] " + self.filename)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "0." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "0." + self.fileext

        ffvideo = ffmpeg.output(
            video, self.filepath, crf=30, format='mp4').global_args('-loglevel', 'error')
        await run_blocking(ffmpeg.run, ffvideo)
        os.remove(oldfilepath)

    async def convertH264(self):
        print("[convert H264] " + self.filename)
        video = ffmpeg.input(self.filepath)
        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "1." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "1." + self.fileext

        ffvideo = ffmpeg.output(video, self.filepath,
                                vcodec='libx264', format='mp4').global_args('-loglevel', 'error')
        await run_blocking(ffmpeg.run, ffvideo)
        os.remove(oldfilepath)

    async def addCaption(self):
        print("[caption] " + self.filename)
        # Gets video and sets position to bottom center
        video = VideoFileClip(self.filepath).set_position(("center", "bottom"))

        # Creates caption that goes above video
        text = TextClip(getDescription(self.url), fontsize=55, color='white', font='Roboto-Regular', align='center',
                        size=(video.size[0] - 10, None), method='caption').set_position(('center', "top")).set_duration(video.duration)

        # Creates background border
        video = video.on_color(color=(54, 57, 63), size=(
            video.size[0], video.size[1] + text.size[1]), pos=(("bottom")))

        result = CompositeVideoClip([video, text])

        oldfilepath = self.filepath
        self.filename = self.filename.split('.')[0] + "5." + self.fileext
        self.filepath = "." + self.filepath.split('.')[1] + "5." + self.fileext

        await run_blocking(result.write_videofile, self.filepath)
        os.remove(oldfilepath)

    def delete(self):
        print("[deleted] " + self.filename)
        os.remove(self.filepath)

    async def upload(self, message=None, interaction=None):
        print("[upload] " + self.filename)

        if message:
            msg = await message.edit(
                content=self.text, attachments=[discord.File(self.filepath)])

        if interaction:
            msg = await interaction.edit_original_response(
                content=self.text, attachments=[discord.File(self.filepath)])

        return msg

    def uploadRemote(self):
        print("[upload remote] " + self.filename)

        bucket.upload_local_file(self.filepath, self.filename)

        return "https://cdn.trev.xyz/memebot/" + self.filename


def downloadVid(filename, url):
    yt_dlp.utils.std_headers['User-Agent'] = 'facebookexternalhit/1.1'
    if "instagram.com" in url:
        ydl_opts = {'outtmpl': filename +
                    '.%(ext)s', 'cookiefile': config.COOKIE_FILE}
    elif "tiktok.com" in url and '@' not in url:
        url = subprocess.run(["curl", "-o", "/dev/null", "--silent", url, "-w",
                             "'%{redirect_url}'"], stdout=subprocess.PIPE).stdout.decode('utf-8')[1:-1]
        print("[tiktok] Redirect URL: " + url)
        ydl_opts = {'outtmpl': filename + '.%(ext)s'}
    elif "youtu.be" in url or "youtube.com/watch?v=" in url:
        ydl_opts = {'outtmpl': filename +
                    '.%(ext)s', 'format': 'best[height<=1080]'}
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

    # remove URLs
    desc = re.sub(r'http\S+', '', desc)
    # remove special chars
    desc = desc.replace("amp;", "")

    return desc


async def processMessage(message, caption=False):
    # Get URL
    url = re.search("(?P<url>https?://[^\\s]+)", message.content).group("url")
    text = message.content.replace(url, "").replace(
        "!dl", "").replace("!caption", "").strip()

    if message.type == discord.MessageType.reply:
        new_message = await message.reference.resolved.reply(content=getLoadingEmoji() + " downloading")
    else:
        new_message = await message.channel.send(
            content=getLoadingEmoji() + " downloading")

    # Download Video
    try:
        # Check if edgy/spoiler
        if 'edgy' in message.content.lower() or 'spoiler' in message.content.lower() or message.channel.id == config.SPOILER_CHANNEL_ID:
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
        await new_message.edit(content=getErrorEmoji() + " error: " + str(ex))
        await new_message.delete(delay=30)
        return

    # Makes sure the video ext is mp4
    if (video.fileext != "mp4"):
        await new_message.edit(content=getLoadingEmoji() + " converting to mp4")
        await video.convert("mp4")

    # Make sure the video codec isnt hevc
    codec = getCodec(video.filepath)
    if codec == "hevc":
        await new_message.edit(content=getLoadingEmoji() + " converting to H264")
        await video.convertH264()

    # Makes sure video is correct size
    if (os.path.getsize(video.filepath) > 25000000):
        await new_message.edit(content=getLoadingEmoji() + " compressing")
        await video.compress()

    # Adds caption if true
    if (caption == True):
        await new_message.edit(content=getLoadingEmoji() + " captioning")
        await video.addCaption()

    print("Downloaded " + video.filename + " to " + video.filepath)
    msg = ''

    # Uploads file
    try:
        await new_message.edit(content=getLoadingEmoji() + " uploading to Discord")
        msg = await video.upload(message=new_message)

    # If file too big
    except discord.errors.HTTPException as ex:
        await new_message.edit(content=getLoadingEmoji() + " uploading to TrevCDN")
        msg = await new_message.edit(content=video.uploadRemote())
        video.delete()
    except Exception as ex:
        await new_message.edit(content=getErrorEmoji() + " error: " + str(ex))
        await new_message.delete(delay=30)
        video.delete()

    # if message exists
    if msg != '':

        # Delete original message
        try:
            await message.delete()
        except Exception:
            await print("[error] Could not delete message")

        # reacts to upload with emoji
        authorid = str(message.author.id)
        for user in config.USER_EMOJIS:
            if (authorid == user[0]):
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

        # Download
        await interaction.edit_original_response(content=getLoadingEmoji() + " downloading")
        video = Video(url, spoiler, meme, text)
    except Exception as ex:
        await interaction.edit_original_response(content=getErrorEmoji() + " error: " + str(ex))
        return

    # Makes sure the video ext is mp4
    if (video.fileext != "mp4"):
        await interaction.edit_original_response(content=getLoadingEmoji() + " converting to mp4")
        await video.convert("mp4")

    # Make sure the video codec isnt hevc
    codec = getCodec(video.filepath)
    if codec == "hevc":
        await interaction.edit_original_response(content=getLoadingEmoji() + " converting to H264")
        await video.convertH264()

    # Makes sure video is correct size
    if (os.path.getsize(video.filepath) > 25000000):
        await interaction.edit_original_response(content=getLoadingEmoji() + " compressing")
        await video.compress()

    # Adds caption if true
    if (caption == True):
        await interaction.edit_original_response(content=getLoadingEmoji() + " captioning")
        await video.addCaption()

    print("Downloaded " + video.filename + " to " + video.filepath)

    # Uploads file
    try:
        await interaction.edit_original_response(content=getLoadingEmoji() + " uploading to Discord")
        await video.upload(interaction=interaction)

    # If file too big
    except discord.errors.HTTPException as ex:
        await interaction.edit_original_response(content=getLoadingEmoji() + " uploading to TrevCDN")
        await interaction.edit_original_response(content=video.uploadRemote())
        video.delete()
    except Exception as ex:
        await interaction.edit_original_response(content=getErrorEmoji() + " error: " + str(ex))
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


async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    """Runs a blocking function in a non-blocking way"""
    func = functools.partial(
        blocking_func, *args, **kwargs)  # `run_in_executor` doesn't support kwargs, `functools.partial` does
    return await client.loop.run_in_executor(None, func)


def getLoadingEmoji():
    emojis = ["<a:bongocat1:499924216490229763>", "<a:frog:1096343749669441636>", "<a:happy:1096343853650432000>", "<a:monke:1096343761891622922>", "<a:headbob:1096343753582710784>", "<a:partycat:1096343758326464532>",
              "<a:partyparrot:432359954838454272>", "<a:partypepe:1096343751091294219>", "<a:pepecat:1096343763854565376>", "<a:ooyaa:1096343757005271080>", "<a:amogus:1096346345473839144>"]
    return random.choice(emojis)


def getErrorEmoji():
    emojis = ["<a:siren:1096340555207807006>",
              "<a:walter:1096343754790670336>", "<a:bruh:1096343752450265179>"]
    return random.choice(emojis)


print("yt_dlp version: " + yt_dlp.version.__version__)

# Discord API
intents = discord.Intents.default()
intents.emojis_and_stickers = True
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Backblaze API
info = InMemoryAccountInfo()
b2 = B2Api(info)
b2.authorize_account("production", config.KEY_ID, config.APPLICATION_KEY)
bucket = b2.get_bucket_by_name(config.BUCKET_NAME)


@tree.command(name="embed", description="embed video from URL", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_embed(interaction, url: str, spoiler: bool = False):
    await interaction.response.defer(thinking=True)
    await processInteraction(interaction, url, spoiler)


@tree.command(name="caption", description="embed video from URL and add caption", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_caption(interaction, url: str, spoiler: bool = False):
    await interaction.response.defer(thinking=True)
    await processInteraction(interaction, url, spoiler, caption=True)


@tree.command(name="embednodl", description="embed video URL without download", guild=discord.Object(id=config.GUILD_ID))
async def on_slash_embedtest(interaction, url: str):
    await interaction.response.defer(thinking=True)
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

    if (str(payload.emoji) == '🥞'):
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
