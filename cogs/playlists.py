import json
import os

import discord
from discord.ext import commands

import utils
from YTDLSource import YTDLSource
from answers import wrong_format
from utils import create_server_folder, add_song_to_file, print_array_nicely

from dotenv import load_dotenv

load_dotenv()

PLAYLISTS_FOLDER = os.getenv('PLAYLISTS_FOLDER')
PLAYLISTS_FILE_NAME = os.getenv('PLAYLISTS_FILE_NAME')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
SONG_TITLES_KEY = os.getenv('SONG_TITLES_KEY')


def get_playlist_queue(playlist_file_location, playlist_name):
    songs_titles = []
    try:
        if os.path.exists(playlist_file_location):
            with open(playlist_file_location, 'r') as f:
                data = json.loads(f.read())
                print(data, playlist_name, SONG_TITLES_KEY)
                songs_titles = data[playlist_name][SONG_TITLES_KEY]
                print(playlist_file_location, playlist_name, songs_titles, data)
        else:
            print('file didnt exist')
    except json.decoder.JSONDecodeError:
        print('json decode error')
    finally:
        return songs_titles


def get_all_playlists(playlist_file_location):
    playlists = []
    try:
        if os.path.exists(playlist_file_location):
            with open(playlist_file_location, 'r') as f:
                data = json.loads(f.read())
                playlists = data.keys()
                print(playlists)
    except json.decoder.JSONDecodeError:
        print('json decode error')
    finally:
        return playlists

async def print_playlist_queue(ctx, playlist_name):
    server_id = ctx.message.guild.id
    playlist_file_location = utils.get_playlists_file_location(server_id)
    if not playlist_name:
        playlists = get_all_playlists(playlist_file_location)
        if len(playlists) == 0:
            return await ctx.send('**You have not created any playlists yet**'.format())
        result = ''
        for playlist in playlists:
            songs_titles = get_playlist_queue(playlist_file_location, playlist)
            playlist_text = ''
            if len(songs_titles) > 0:
                playlist_text = print_array_nicely(songs_titles)
            else:
                playlist_text = 'Playlist is empty.'
            result += playlist + ':\n' + playlist_text + "\n"
        return await ctx.send('**Your playlists: \n\n{}**'.format(result))
    else:
        songs_titles = get_playlist_queue(playlist_file_location, playlist_name)
        if len(songs_titles) > 0:
            await ctx.send('**Current playlist: \n\n{}**'.format(print_array_nicely(songs_titles)))
        else:
            await ctx.send('**Playlist is empty or not exist **'.format())

class PlaylistCog(commands.Cog, name='Playlist'):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='playlist', aliases=['pl'],
                    help="Playlists commands. Type ` {}help pl` to see more.".format(COMMAND_PREFIX), invoke_without_command=True)
    async def playlist(self, ctx):
        await print_playlist_queue(ctx, None)

    @playlist.command(name='add', aliases=['a'])
    async def add(self, ctx, playlist_name=None, url=None):
        """Add song to playlist"""
        if not playlist_name:
            return await ctx.send(wrong_format.format('playlist'))
        if not url:
            return await ctx.send(wrong_format.format('song url'))
        try:
            server_id = ctx.message.guild.id
            path_to_file = utils.get_playlists_file_location(server_id)
            song_title = await YTDLSource.get_title(url)
            if song_title:
                add_song_to_file(path_to_file, playlist_name, url, song_title)
                return await ctx.send('{} was added to {}'.format(song_title, playlist_name))
            else:
                return await ctx.send('**Current url is not a valid youtube link!**'.format(song_title))
        except Exception as inst:
            print(inst)
            await ctx.send("The bot is not connected to a voice channel.")

    @playlist.command(name='delete', aliases=['d'])
    async def delete(self, ctx, playlist_name=None, song_index=None):
        """Delete song from playlist"""
        if not playlist_name:
            return await ctx.send(wrong_format.format('playlist'))
        if not song_index:
            return await ctx.send(wrong_format.format('song index'))
        try:
            server_id = ctx.message.guild.id
            path_to_file = utils.get_playlists_file_location(server_id)
            delete_result = utils.delete_song_from_file(path_to_file, playlist_name, song_index)
            return await ctx.send(delete_result)

        except Exception as inst:
            print(inst)
            await ctx.send("The bot is not connected to a voice channel.")

    @playlist.command(name='queue', aliases=['q'], help='Command usage: $q q - Get all playlists info; $q q playlist_name - Get uniq playlist info"')
    async def queue(self, ctx, playlist_name=None):
        await print_playlist_queue(ctx, playlist_name)


async def setup(bot):
    await bot.add_cog(PlaylistCog(bot))
