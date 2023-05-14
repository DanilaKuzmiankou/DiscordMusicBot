import json
import os
import shutil
from threading import Timer

from dotenv import load_dotenv

import bot_state

load_dotenv()

SERVERS_FOLDER = os.getenv('SERVERS_FOLDER')
SONG_URLS_KEY = os.getenv('SONG_URLS_KEY')
SONG_TITLES_KEY = os.getenv('SONG_TITLES_KEY')
SONG_FILES_KEY = os.getenv('SONG_FILES_KEY')
PLAYLISTS_FOLDER = os.getenv('PLAYLISTS_FOLDER')
PLAYLISTS_FILE_NAME = os.getenv('PLAYLISTS_FILE_NAME')
QUEUE_FILE_NAME = os.getenv('QUEUE_FILE_NAME')
QUEUE_FULL_FILE_NAME = os.getenv('QUEUE_FULL_FILE_NAME')
QUEUE_FOLDER = os.getenv('QUEUE_FOLDER')


def delete_all_in_folder_with_delay(folder, delay=2.0):
    Timer(delay, delete_all_in_folder, [folder]).start()


def delete_all_in_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(root, d)


def delete_file_with_delay(filename, delay=2.0):
    Timer(delay, delete_file, [filename]).start()


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def print_array_nicely(array):
    result_string = ''
    for index, item in enumerate(array, start=1):
        result_string += '{}: {}\n'.format(index, item)
    return result_string


def create_server_folder(server_id):
    current_server_folder = SERVERS_FOLDER + '/' + str(server_id)
    if not os.path.exists(current_server_folder):
        os.makedirs(current_server_folder)
    return current_server_folder


def create_song_dictionary(song_dictionary, song_url, song_title, song_filename):
    if SONG_URLS_KEY not in song_dictionary:
        song_dictionary[SONG_URLS_KEY] = []
    if SONG_TITLES_KEY not in song_dictionary:
        song_dictionary[SONG_TITLES_KEY] = []
    if song_url not in song_dictionary[SONG_URLS_KEY]:
        song_dictionary[SONG_URLS_KEY].append(song_url)
        song_dictionary[SONG_TITLES_KEY].append(song_title)
        if song_filename:
            song_dictionary[SONG_FILES_KEY].append(song_filename)
    return song_dictionary


def add_song_to_file(path_to_file, playlist_name, song_url, song_title, song_filename=None):
    data = {playlist_name: {SONG_URLS_KEY: [song_url], SONG_TITLES_KEY: [song_title]}}
    print('s', song_filename)
    if song_filename:
        data[playlist_name][SONG_FILES_KEY] = [song_filename]
        print('add', data, SONG_FILES_KEY)
    try:
        if os.path.exists(path_to_file):
            with open(path_to_file, 'r') as f:
                data = json.loads(f.read())
                if playlist_name not in data:
                    data[playlist_name] = {}
                data[playlist_name] = create_song_dictionary(data[playlist_name], song_url, song_title, song_filename)
    except json.decoder.JSONDecodeError:
        print('json decode error')
    finally:
        with open(path_to_file, 'w+') as f:
            json.dump(data, f)


def delete_song_from_playlist(playlist, song_index):
    del playlist[SONG_TITLES_KEY][song_index - 1]
    del playlist[SONG_URLS_KEY][song_index - 1]
    if SONG_FILES_KEY in playlist:
        del playlist[SONG_FILES_KEY][song_index - 1]


def delete_song_from_file(path_to_file, playlist_name, song_index):
    try:
        song_index = int(song_index)
        if os.path.exists(path_to_file):
            with open(path_to_file, 'r') as f:
                data = json.loads(f.read())
                if playlist_name not in data:
                    return 'There is no playlist with current name'
                if len(data[playlist_name][SONG_TITLES_KEY]) < song_index:
                    return 'There is no song with current index in this playlist'
                song_title = data[playlist_name][SONG_TITLES_KEY][song_index-1]
                delete_song_from_playlist(data[playlist_name], song_index)
            with open(path_to_file, 'w+') as f:
                json.dump(data, f)
            return '{} was deleted from {}'.format(song_title, playlist_name)
    except json.decoder.JSONDecodeError:
        print('json decode error')
    except ValueError:
        return 'Wrong index format. Index is number of song, which you wanna delete. You can check song indexes with ' \
               '$pl q `playlist_name`'


def get_playlists_file_location(server_id):
    current_server_folder = create_server_folder(server_id)
    current_playlists_folder = current_server_folder + '/' + PLAYLISTS_FOLDER
    if not os.path.exists(current_playlists_folder):
        os.makedirs(current_playlists_folder)
    try:
        playlists_file_location = current_playlists_folder + '/' + PLAYLISTS_FILE_NAME
        return playlists_file_location
    except Exception as file_open_exception:
        print('file open exception:', file_open_exception)


def get_queue_file_location(server_id):
    current_server_folder = create_server_folder(server_id)
    current_queue_folder = current_server_folder + '/' + QUEUE_FOLDER
    if not os.path.exists(current_queue_folder):
        os.makedirs(current_queue_folder)
    queue_file_location = current_queue_folder + '/' + QUEUE_FULL_FILE_NAME
    return queue_file_location


def get_queue(queue_file_location):
    songs_titles = []
    songs_urls = []
    songs_files = []
    try:
        if os.path.exists(queue_file_location):
            with open(queue_file_location, 'r') as f:
                data = json.loads(f.read())
                songs_titles = data[QUEUE_FILE_NAME][SONG_TITLES_KEY]
                songs_urls = data[QUEUE_FILE_NAME][SONG_URLS_KEY]
                songs_files = data[QUEUE_FILE_NAME][SONG_FILES_KEY]
        else:
            print('file not exists')
    except json.decoder.JSONDecodeError:
        print('json decode error')
    finally:
        return songs_titles, songs_urls, songs_files

def concat_arrays_uniq_values(array1, array2):
    return list(dict.fromkeys(array1 + array2))


def stop_voice_channel(ctx):
    bot_state.is_stopped = True
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    voice_channel = server.voice_client
    if voice_client and voice_client.is_playing():
        voice_channel.stop()
        voice_client.stop()