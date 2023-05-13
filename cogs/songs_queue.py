import json
import os

import discord
from discord.ext import commands

import utils
from YTDLSource import YTDLSource
from answers import wrong_format
from utils import create_server_folder, print_array_nicely, add_song_to_file
from dotenv import load_dotenv

load_dotenv()

QUEUE_FOLDER = os.getenv('QUEUE_FOLDER')
QUEUE_FULL_FILE_NAME = os.getenv('QUEUE_FULL_FILE_NAME')
QUEUE_FILE_NAME = os.getenv('QUEUE_FILE_NAME')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
SONG_TITLES_KEY = os.getenv('SONG_TITLES_KEY')
SONG_URLS_KEY = os.getenv('SONG_URLS_KEY')

def get_queue_file_location(server_id):
    current_server_folder = create_server_folder(server_id)
    current_queue_folder = current_server_folder + '/' + QUEUE_FOLDER
    if not os.path.exists(current_queue_folder):
        os.makedirs(current_queue_folder)
    queue_file_location = current_queue_folder + '/' + QUEUE_FULL_FILE_NAME
    return queue_file_location


def get_queue(queue_file_location):
    songs_titles = []
    try:
        if os.path.exists(queue_file_location):
            with open(queue_file_location, 'r') as f:
                data = json.loads(f.read())
                songs_titles = data[QUEUE_FILE_NAME][SONG_TITLES_KEY]
        else: print('file not exists')
    except json.decoder.JSONDecodeError:
        print('json decode error')
    finally:
        return songs_titles


class SongsQueueCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='queue', aliases=['q'],
                    help="Queue commands. Type ` {}help q` to see more.".format(COMMAND_PREFIX))
    async def song_queue(self, ctx):
        pass

    @song_queue.command(name='add', aliases=['a'])
    async def add(self, ctx, url=None):
        """Add song to queue"""
        if not url:
            return await ctx.send(wrong_format.format('song url'))
        try:
            server_id = ctx.message.guild.id
            path_to_file = get_queue_file_location(server_id)
            song_title = await YTDLSource.get_title(url)
            print('song title:', song_title)
            add_song_to_file(path_to_file, QUEUE_FILE_NAME, url, song_title)
        except Exception as inst:
            print(inst)
            await ctx.send("The bot is not connected to a voice channel.")

    @song_queue.command(name='queue', aliases=['q'])
    async def current_queue(self, ctx):
        """Get queue"""
        server_id = ctx.message.guild.id
        queue_file_location = get_queue_file_location(server_id)
        songs_titles = get_queue(queue_file_location)
        print(queue_file_location, songs_titles)
        if len(songs_titles) > 0:
            await ctx.send('**Current queue: \n\n{}**'.format(print_array_nicely(songs_titles)))
        else:
            await ctx.send('**Queue is empty**'.format())

    @song_queue.command(name='playlist', aliases=['pl'])
    async def add_playlist_to_queue(self, ctx, playlist_name=None):
        """Add songs from playlist to queue"""
        if not playlist_name:
            return await ctx.send(wrong_format.format('playlist'))
        server_id = ctx.message.guild.id
        playlist_file_location = utils.get_playlists_file_location(server_id)
        queue_file_location = get_queue_file_location(server_id)
        if os.path.exists(playlist_file_location):
            with open(playlist_file_location, 'r') as playlist_file:
                playlist_file_data = json.loads(playlist_file.read())
                playlist_songs_titles = playlist_file_data[playlist_name][SONG_TITLES_KEY]
                playlist_songs_urls = playlist_file_data[playlist_name][SONG_URLS_KEY]
                with open(queue_file_location, 'r') as queue_file:
                    queue_file_data = json.loads(queue_file.read())
                    queue_file_data[SONG_TITLES_KEY] = queue_file_data[SONG_TITLES_KEY] + playlist_songs_titles
                    queue_file_data[SONG_URLS_KEY] = queue_file_data[SONG_URLS_KEY] + playlist_songs_urls
                with open(queue_file_location, 'w+') as queue_file:
                    json.dump(queue_file_data, queue_file)

    # @queue.command(name='play', aliases=['p'], help='Play the song from query')
    # async def play(ctx, url):
    #     global current_song_url, current_song_filename
    #     try:
    #         add_song_to_query(url)
    #         await join_channel(ctx)
    #         voice_channel = ctx.message.guild.voice_client
    #         async with ctx.typing():
    #             filename, title = await download_song_from_url(url)
    #             print('new song was downloaded', filename)
    #             if not voice_channel.is_playing():
    #                 print('starting new playing queue')
    #                 current_song_url = url
    #                 current_song_filename = filename
    #                 await play_song(voice_channel, filename, ctx)
    #                 await ctx.send('**Песня начала проигрываться:** {}'.format(title))
    #             else:
    #                 await ctx.send('**Песня была поставлена в очередь:** {}'.format(title))
    #     except Exception as inst:
    #         print(inst)
    #         await ctx.send("The bot is not connected to a voice channel.")
    #
    # @queue.command(name='skip', aliases=['s'], help='Skip the song from query')
    # async def skip(ctx):
    #     global current_song_url, current_song_filename
    #
    #     current_song_index = songs_query.index(current_song_url)
    #     await ctx.send('{} **was deleted from queue**'.format(songs_query_titles[current_song_index]))
    #     del songs_query[current_song_index]
    #     del songs_query_titles[current_song_index]
    #     stop_voice_channel(ctx)
    #     delete_file_with_delay(filename=current_song_filename)
    #     if len(songs_query) > 0:
    #         server = ctx.message.guild
    #         voice_channel = server.voice_client
    #         current_song_was_last = current_song_index == len(songs_query)
    #         next_song_index = 0 if current_song_was_last else current_song_index
    #         next_song_url = songs_query[next_song_index]
    #         current_song_url = next_song_url
    #         filename, title = await download_song_from_url(current_song_url)
    #         current_song_filename = filename
    #         if not voice_channel.is_playing():
    #             await play_song(voice_channel, filename, ctx)
    #     else:
    #         await ctx.send('**Queue is empty **'.format())
    #
    # @queue.command(name='clear', aliases=['c'], help='Clear songs query')
    # async def clear(ctx):
    #     global current_song_url, current_song_filename, songs_query, songs_query_titles
    #     stop_voice_channel(ctx)
    #     current_song_filename, current_song_url = '', ''
    #     songs_query, songs_query_titles = [], []
    #     delete_all_in_folder_with_delay(SONGS_FOLDER)

async def setup(bot):
    await bot.add_cog(SongsQueueCog(bot))