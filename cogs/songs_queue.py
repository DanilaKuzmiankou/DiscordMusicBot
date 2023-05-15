import json
import os

import discord
from discord.ext import commands

import bot_state
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
SONG_FILES_KEY = os.getenv('SONG_FILES_KEY')
SONGS_FOLDER = os.getenv('SONGS_FOLDER')


async def clearQueue(ctx):
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    utils.stop_voice_channel(ctx)
    utils.delete_file_with_delay(queue_file_location)
    utils.delete_all_in_folder_with_delay(SONGS_FOLDER)
    await ctx.send('Queue was cleaned')


async def print_current_queue(ctx):
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    songs_titles, songs_urls, songs_files = utils.get_queue(queue_file_location)
    print(queue_file_location, songs_titles)
    if len(songs_titles) > 0:
        await ctx.send('**Current queue: \n\n{}**'.format(print_array_nicely(songs_titles)))
    else:
        await ctx.send('**Queue is empty**'.format())


class SongsQueueCog(commands.Cog, name='Queue'):
    """Server queue control"""

    def __init__(self, bot):
        """Shows all modules of that bot"""
        self.bot = bot

    @commands.group(name='queue', aliases=['q'],
                    invoke_without_command=True)
    async def song_queue(self, ctx):
        """Get current queue"""
        await print_current_queue(ctx)

    @song_queue.command(name='add', aliases=['a'], help='`{}add url` - Add song to queue'.format(COMMAND_PREFIX))
    async def add(self, ctx, url=None):
        if not url:
            return await ctx.send(wrong_format.format('song url'))
        try:
            server_id = ctx.message.guild.id
            path_to_file = utils.get_queue_file_location(server_id)
            filename, song_title = await YTDLSource.from_url(url, loop=self.bot.loop)
            if filename:
                add_song_to_file(path_to_file, QUEUE_FILE_NAME, url, song_title, filename)
                await ctx.send('**{} was added to queue:**'.format(song_title))
            else:
                await ctx.send('**Current url is not a valid youtube link!**'.format(song_title))
            print('song title:', song_title)
        except Exception as inst:
            print(inst)
            await ctx.send("The bot is not connected to a voice channel.")


    @song_queue.command(name='playlist', aliases=['pl'], help='`{}playlist playlist_name` - Add all songs from '
                                                              'playlist to queue'.format(COMMAND_PREFIX))
    async def add_playlist_to_queue(self, ctx, playlist_name=None):
        if not playlist_name:
            return await ctx.send(wrong_format.format('playlist'))
        server_id = ctx.message.guild.id
        playlist_file_location = utils.get_playlists_file_location(server_id)
        queue_file_location = utils.get_queue_file_location(server_id)
        if os.path.exists(playlist_file_location):
            with open(playlist_file_location, 'r') as playlist_file:
                playlist_file_data = json.loads(playlist_file.read())
                if playlist_name not in playlist_file_data:
                    return await ctx.send('**Playlist with this name doesn`t exist!**'.format())
                await ctx.send('**Start adding songs from {} playlist!**'.format(playlist_name))
                async with ctx.typing():
                    playlist_songs_titles = playlist_file_data[playlist_name][SONG_TITLES_KEY]
                    playlist_songs_urls = playlist_file_data[playlist_name][SONG_URLS_KEY]
                    queue_file_data = {QUEUE_FILE_NAME: {SONG_TITLES_KEY: [], SONG_URLS_KEY: [], SONG_FILES_KEY: []}}
                    if os.path.exists(queue_file_location):
                        with open(queue_file_location, 'r') as queue_file:
                            queue_file_data = json.loads(queue_file.read())
                    with open(queue_file_location, 'w+') as queue_file:
                        filenames = []
                        queue_data = queue_file_data[QUEUE_FILE_NAME]
                        queue_data[SONG_TITLES_KEY] = utils.concat_arrays_uniq_values(queue_data[SONG_TITLES_KEY],
                                                                                      playlist_songs_titles)
                        queue_data[SONG_URLS_KEY] = utils.concat_arrays_uniq_values(queue_data[SONG_URLS_KEY],
                                                                                    playlist_songs_urls)
                        queue_data[SONG_FILES_KEY] = filenames
                        queue_file_data[QUEUE_FILE_NAME] = queue_data
                        for song_url in queue_data[SONG_URLS_KEY]:
                            print('downloading song from url:', song_url)
                            filename, song_title = await YTDLSource.from_url(song_url, loop=self.bot.loop)
                            filenames.append(filename)
                        print(queue_file_data)
                        json.dump(queue_file_data, queue_file)
                await ctx.send('**Playlist was added to queue!**'.format())

    @song_queue.command(name='clear', aliases=['c'], help='Clear songs queue')
    async def clear(self, ctx):
        await clearQueue(ctx)


async def setup(bot):
    await bot.add_cog(SongsQueueCog(bot))
