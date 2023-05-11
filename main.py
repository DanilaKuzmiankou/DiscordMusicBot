import asyncio
import shutil
from threading import Timer
import discord
from discord.ext import commands, tasks
import os
import yt_dlp as youtube_dl
from discord.utils import get

from YTDLSource import YTDLSource
from utils import delete_all_in_folder_with_delay, delete_file_with_delay, print_array_nicely
from dotenv import load_dotenv

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SONGS_FOLDER = os.getenv('SONGS_FOLDER')

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$', intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''




playlists_folder = 'playlists'

songs_query = []
songs_query_titles = []
current_song_url = ''
current_song_filename = ''
is_playing = False


def add_song_to_query(song_url):
    if song_url not in songs_query:
        songs_query.append(song_url)


async def download_song_from_url(url):
    downloaded_song, title = await YTDLSource.from_url(url, loop=bot.loop)
    global songs_query_titles
    if title not in songs_query_titles:
        songs_query_titles.append(title)
    return downloaded_song, title


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


def create_playlist_file(server_name):
    if not os.path.exists(playlists_folder):
        print('folder:', playlists_folder + '/' + server_name)
        os.makedirs(playlists_folder + '/' + server_name)
        f = open("playlists.txt", "w")
        return f

@bot.group(pass_context=True)
async def First(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid sub command passed 1...')

@First.group(pass_context=True)
async def Second(ctx):
    if ctx.invoked_subcommand is Second:
        await ctx.send('Invalid sub command passed 2...')

@Second.command(pass_context=True)
async def Third(ctx):
    msg = 'Finally got success {0.author.mention}'.format(ctx.message)
    await ctx.send(msg)

@commands.group(invoke_without_command=True, name='playlist')
async def playlist(self, ctx, *args):
    # general functionality, help, or whatever.
    print('hi')
    pass

@playlist.group(name='add', aliases=['a'], help='Play the song')
async def add_to_playlist(ctx, playlist_name, url):
    try:
        print('ctx', ctx, '\nserver:',  ctx.message.guild)
        # playlists_file = create_playlist_file()
    except Exception as inst:
        print(inst)
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='play', aliases=['p'], help='Play the song')
async def play(ctx, url):
    global current_song_url, current_song_filename
    try:
        add_song_to_query(url)
        await join_channel(ctx)
        voice_channel = ctx.message.guild.voice_client
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


@bot.command(name='skip', aliases=['s'], help='Skip the song')
async def skip(ctx):
    global current_song_url, current_song_filename

    current_song_index = songs_query.index(current_song_url)
    await ctx.send('{} **was deleted from queue**'.format(songs_query_titles[current_song_index]))
    del songs_query[current_song_index]
    del songs_query_titles[current_song_index]
    stop_voice_channel(ctx)
    delete_file_with_delay(filename=current_song_filename)
    if len(songs_query) > 0:
        server = ctx.message.guild
        voice_channel = server.voice_client
        current_song_was_last = current_song_index == len(songs_query)
        next_song_index = 0 if current_song_was_last else current_song_index
        next_song_url = songs_query[next_song_index]
        current_song_url = next_song_url
        filename, title = await download_song_from_url(current_song_url)
        current_song_filename = filename
        if not voice_channel.is_playing():
            await play_song(voice_channel, filename, ctx)
    else:
        await ctx.send('**Queue is empty **'.format())


@bot.command(name='queue', aliases=['q'], help='Get songs query')
async def queue(ctx):
    if len(songs_query_titles) > 0:
        await ctx.send('**Current queue: \n\n{}**'.format(print_array_nicely(songs_query_titles)))
    else:
        await ctx.send('**Queue is empty **'.format())


@bot.command(name='clear', help='Clear songs query')
async def clear(ctx):
    global current_song_url, current_song_filename, songs_query, songs_query_titles
    stop_voice_channel(ctx)
    current_song_filename, current_song_url = '', ''
    songs_query, songs_query_titles = [], []
    delete_all_in_folder_with_delay(SONGS_FOLDER)


def is_connected_to_channel(ctx):
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()


@bot.command(name='pause', help='Pause the song')
async def pause(ctx):
    await pause_voice_channel(ctx)


async def pause_voice_channel(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='resume', help='Resume the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")


@bot.command(name='join', aliases=['j'], help='Join the voice channel')
async def join(ctx):
    await join_channel(ctx)


async def join_channel(ctx):
    if not is_connected_to_channel(ctx):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        print('bot is already connected to the channel')


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


def stop_voice_channel(ctx):
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.stop()
    if voice_client.is_playing():
        voice_client.stop()


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
            delete_all_in_folder_with_delay(SONGS_FOLDER)


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
