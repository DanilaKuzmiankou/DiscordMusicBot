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
SONG_FILES_KEY = os.getenv('SONG_FILES_KEY')
SONGS_FOLDER = os.getenv('SONGS_FOLDER')


async def clearQueue(ctx):
    server_id = ctx.message.guild.id
    queue_file_location = utils.get_queue_file_location(server_id)
    utils.delete_file_with_delay(queue_file_location)
    utils.delete_all_in_folder_with_delay(SONGS_FOLDER)
    await ctx.send('Queue was cleaned')

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

    @song_queue.command(name='queue', aliases=['q'])
    async def current_queue(self, ctx):
        """Get queue"""
        server_id = ctx.message.guild.id
        queue_file_location = utils.get_queue_file_location(server_id)
        songs_titles, songs_urls, songs_files = utils.get_queue(queue_file_location)
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
        queue_file_location = utils.get_queue_file_location(server_id)
        if os.path.exists(playlist_file_location):
            with open(playlist_file_location, 'r') as playlist_file:
                playlist_file_data = json.loads(playlist_file.read())
                if playlist_name not in playlist_file_data:
                    return await ctx.send('**Playlist with this name doesn`t exist!**'.format())
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

    @song_queue.command(name='clear', aliases=['c'], help='Clear songs query')
    async def clear(self, ctx):
        await clearQueue(ctx)


async def setup(bot):
    await bot.add_cog(SongsQueueCog(bot))
