import asyncio
import shutil
from threading import Timer
import discord
from discord.ext import commands, tasks
import os
import yt_dlp as youtube_dl
from discord.utils import get

from utils import delete_all_in_folder_with_delay, delete_file_with_delay, print_array_nicely

# Get the API token from the .env file.
DISCORD_TOKEN = 'MTEwNDUxNTE0NTI2ODQ2MTYzOQ.GDoWFN.1IF_fFp9rxn5MLGjyT38ASkJv0-w5TU8_mChlc'

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$', intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

songs_folder = 'songs'

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'no-overwrites': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'paths': {
        'home': songs_folder
    },
    #     'postprocessors': [{  # Extract audio using ffmpeg
    #         'key': 'FFmpegExtractAudio',
    #         'preferredcodec': 'm4a',
    # }]
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

songs_query = []
songs_query_titles = []
current_song_url = ''
current_song_filename = ''
is_playing = False


def add_song_to_query(song_url):
    if song_url not in songs_query:
        songs_query.append(song_url)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename, data['title']


async def pause_voice_channel(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


def stop_voice_channel(ctx):
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.stop()
    if voice_client.is_playing():
        voice_client.stop()


def is_connected_to_channel(ctx):
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()


async def download_song_from_url(url):
    downloaded_song, title = await YTDLSource.from_url(url, loop=bot.loop)
    global songs_query_titles
    if title not in songs_query_titles:
        songs_query_titles.append(title)
    return downloaded_song, title


async def join_channel(ctx):
    if not is_connected_to_channel(ctx):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        print('bot is already connected to the channel')


async def play_song(voice_channel, song_file, ctx):
    print('start playing, cur file:', song_file)
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=song_file),
                       after=lambda e: asyncio.run_coroutine_threadsafe(
                           after_song_was_played(voice_channel=voice_channel, ctx=ctx), bot.loop))
    voice_channel.is_playing()


async def after_song_was_played(voice_channel, ctx):
    global current_song_url, current_song_filename
    if len(songs_query) > 0:
        current_song_index = songs_query.index(current_song_url)
        next_song_url = ''
        if current_song_index == (len(songs_query) - 1):
            next_song_url = songs_query[0]
        else:
            next_song_url = songs_query[current_song_index + 1]
        next_song, title = await download_song_from_url(next_song_url)
        current_song_url = next_song_url
        current_song_filename = next_song
        await play_song(voice_channel=voice_channel, song_file=next_song, ctx=ctx)


@bot.command(name='p', help='Play the song')
async def play(ctx, url):
    global current_song_url, current_song_filename
    try:
        add_song_to_query(url)
        await join_channel(ctx)
        server = ctx.message.guild
        voice_channel = server.voice_client
        print('qu', bot)
        async with ctx.typing():
            filename, title = await download_song_from_url(url)
            print('new song was downloaded', filename)
            if not voice_channel.is_playing():
                print('starting new playing queue')
                current_song_url = url
                current_song_filename = filename
                await play_song(voice_channel, filename, ctx)
                await ctx.send('**Песня начала проигрываться:** {}'.format(title))
            else:
                await ctx.send('**Песня была поставлена в очередь:** {}'.format(title))
    except Exception as inst:
        print(inst)
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='j', help='Join the voice channel')
async def join(ctx):
    await join_channel(ctx)


@bot.command(name='pause', help='Pause the song')
async def pause(ctx):
    await pause_voice_channel(ctx)


@bot.command(name='s', help='Skip the song')
async def skip(ctx):
    global current_song_url, current_song_filename
    stop_voice_channel(ctx)
    current_song_index = songs_query.index(current_song_url)
    await ctx.send('{} **was deleted from queue**'.format(songs_query_titles[current_song_index]))
    del songs_query[current_song_index]
    del songs_query_titles[current_song_index]
    # delete_file_with_delay(filename=current_song_filename)
    if len(songs_query) > 0:
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            current_song_was_last = current_song_index == len(songs_query)
            next_song_index = 0 if current_song_was_last else current_song_index
            next_song_url = songs_query[next_song_index]
            current_song_url = next_song_url
            filename, title = await download_song_from_url(current_song_url)
            current_song_filename = filename
            if not voice_channel.is_playing():
                await play_song(voice_channel, filename, ctx)
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='q', help='Get songs query')
async def queue(ctx):
    if len(songs_query_titles) > 0:
        await ctx.send('**{}**'.format(print_array_nicely(songs_query_titles)))
    else:
        await ctx.send('**Queue is empty **'.format())


@bot.command(name='clear', help='Clear songs query')
async def clear(ctx):
    global current_song_url, current_song_filename, songs_query, songs_query_titles
    stop_voice_channel(ctx)
    current_song_filename, current_song_url = '', ''
    songs_query, songs_query_titles = [], []
    delete_all_in_folder_with_delay(songs_folder)


@bot.command(name='resume', help='Resume the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")


@bot.command(name='leave', help='Leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected_to_channel():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='stop', help='Stop the song')
async def stop(ctx):
    stop_voice_channel(ctx)


@bot.event
async def on_ready():
    print('Running!')
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if str(channel) == "general":
                await channel.send('Bot Activated..')
        print('Active in {}\n Member Count : {}'.format(guild.name, guild.member_count))


@bot.event
async def on_voice_state_update(member, before, after):
    bot_name_and_discriminator = '{}#{}'.format(bot.user.name, bot.user.discriminator)
    if str(member) == bot_name_and_discriminator:
        if before.channel is not None and after.channel is None:
            print('delete songs dir...')
            delete_all_in_folder_with_delay(songs_folder)


@bot.event
async def on_member_join(member):
    for channel in member.guild.text_channels:
        if str(channel) == "general":
            on_mobile = False
            if member.is_on_mobile() == True:
                on_mobile = True
            await channel.send("О, шпана понаехала...\n On Mobile : {}".format(member.name, on_mobile))


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
