import asyncio
import json
import shutil
from threading import Timer
import discord
from discord.ext import commands, tasks
import os
import yt_dlp as youtube_dl
from discord.utils import get

import utils
from YTDLSource import YTDLSource
from cogs.songs_queue import clearQueue
from utils import delete_all_in_folder_with_delay
from dotenv import load_dotenv

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SONGS_FOLDER = os.getenv('SONGS_FOLDER')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
QUEUE_FILE_NAME = os.getenv('QUEUE_FILE_NAME')

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

is_playing = False
initial_extensions = ['cogs.songs_queue', 'cogs.playlists']

current_playing_file = ''
stopped = False

@bot.command(name='play', aliases=['p'], help='Play the song from query')
async def play(ctx, song_url=None):
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    if song_url:
        filename, song_title = await YTDLSource.from_url(song_url, loop=bot.loop)
        if filename:
            utils.add_song_to_file(queue_file_location, QUEUE_FILE_NAME, song_url, song_title, filename)
            await ctx.send('**{} was added to queue:**'.format(song_title))
        else:
            await ctx.send('**Current url is not a valid youtube link!**'.format(song_title))
        print('song title:', song_title)

    songs_titles, songs_urls, songs_files = utils.get_queue(queue_file_location)
    if len(songs_files) > 0:
        join_channel_result = await join_channel(ctx)
        voice_channel = ctx.message.guild.voice_client
        if not voice_channel.is_playing():
            print('starting new playing queue', songs_titles)
            await play_song(ctx, voice_channel, songs_files[0])
            await ctx.send('**Now playing:** {}'.format(songs_titles[0]))
    else:
        return await ctx.send('**There is no songs in queue:**'.format())


@bot.command(name='skip', aliases=['s'], help='Skip the song')
async def skip(ctx):
    global current_playing_file
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    songs_titles, songs_urls, songs_files = utils.get_queue(queue_file_location)
    current_song_index = songs_files.index(current_playing_file)

    stop_voice_channel(ctx)

    song_title = songs_titles[current_song_index]
    utils.delete_song_from_file(queue_file_location, QUEUE_FILE_NAME, current_song_index+1)
    await ctx.send('{} **was deleted from queue**'.format(song_title))
    print(songs_titles, songs_urls, songs_files, 'q')

    if len(songs_files)-1 > 0:
        voice_channel = ctx.message.guild.voice_client
        next_song_file = ''
        if current_song_index == (len(songs_files) - 1):
            next_song_file = songs_files[0]
        else:
            next_song_file = songs_files[current_song_index + 1]

        await play_song(ctx, voice_channel, next_song_file)
    else:
        await ctx.send('**Queue is empty **'.format())


async def play_song(ctx, voice_channel, song_file):
    print('start playing, cur file:', song_file)
    global stopped, current_playing_file
    stopped = False
    current_playing_file = song_file
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=song_file),
                       after=lambda e: asyncio.run_coroutine_threadsafe(
                           after_song_was_played(ctx, voice_channel, song_file), bot.loop))
    voice_channel.is_playing()


async def after_song_was_played(ctx, voice_channel, song_file):
    if stopped:
        return
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    songs_titles, songs_urls, songs_files = utils.get_queue(queue_file_location)
    print(songs_titles, songs_urls, songs_files, 'q')
    if len(songs_files) > 0:
        next_song_file = ''
        current_song_index = songs_files.index(song_file)
        if current_song_index == (len(songs_files) - 1):
            next_song_file = songs_files[0]
        else:
            next_song_file = songs_files[current_song_index + 1]
        await play_song(ctx, voice_channel, next_song_file)


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
        voice = ctx.message.author.voice
        print(voice)
        if voice:
            channel = voice.channel
            await channel.connect()
            return True
        else:
            return False
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
    global stopped
    stopped = True
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
            print('delete songs dir...', before)
            delete_all_in_folder_with_delay(SONGS_FOLDER)
            # ctx = await bot.get_context(member)
            # await clearQueue(ctx)



@bot.event
async def on_member_join(member):
    for channel in member.guild.text_channels:
        if str(channel) == "general":
            on_mobile = False
            if member.is_on_mobile():
                on_mobile = True
            await channel.send("О, шпана понаехала...\n On Mobile : {}".format(member.name, on_mobile))


async def load_extensions():
    for extension in initial_extensions:
        await bot.load_extension(extension)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN, reconnect=True)
