import asyncio
import json
import shutil
from threading import Timer
import discord
from discord.ext import commands, tasks
import os
import yt_dlp as youtube_dl
from discord.utils import get

from YTDLSource import YTDLSource
from utils import delete_all_in_folder_with_delay
from dotenv import load_dotenv

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SONGS_FOLDER = os.getenv('SONGS_FOLDER')
COMMAND_PREFIX = '$'

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

is_playing = False


async def download_song_from_url(url):
    yield
    # downloaded_song, title = await YTDLSource.from_url(url, loop=bot.loop)
    # global songs_query_titles
    # if title not in songs_query_titles:
    #     songs_query_titles.append(title)
    # return downloaded_song, title


async def play_song(voice_channel, song_file, ctx):
    print('start playing, cur file:', song_file)
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=song_file),
                       after=lambda e: asyncio.run_coroutine_threadsafe(
                           after_song_was_played(voice_channel=voice_channel, ctx=ctx), bot.loop))
    voice_channel.is_playing()


async def after_song_was_played(voice_channel, ctx):
    print('11')


# global current_song_url, current_song_filename
# if len(songs_query) > 0:
#     current_song_index = songs_query.index(current_song_url)
#     next_song_url = ''
#     if current_song_index == (len(songs_query) - 1):
#         next_song_url = songs_query[0]
#     else:
#         next_song_url = songs_query[current_song_index + 1]
#     next_song, title = await download_song_from_url(next_song_url)
#     current_song_url = next_song_url
#     current_song_filename = next_song
#     await play_song(voice_channel=voice_channel, song_file=next_song, ctx=ctx)


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
    await load_extensions()
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
            if member.is_on_mobile():
                on_mobile = True
            await channel.send("О, шпана понаехала...\n On Mobile : {}".format(member.name, on_mobile))


initial_extensions = ['cogs.songs_queue', 'cogs.playlists']


async def load_extensions():
    for extension in initial_extensions:
        await bot.load_extension(extension)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN, reconnect=True)