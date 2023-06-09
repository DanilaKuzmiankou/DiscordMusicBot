import asyncio
import os
import discord
import yt_dlp as youtube_dl
from dotenv import load_dotenv

load_dotenv()

SONGS_FOLDER = os.getenv('SONGS_FOLDER')

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
        'home': SONGS_FOLDER
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



class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    def is_supported(cls, url):
        extractors = youtube_dl.extractor.gen_extractors()
        for e in extractors:
            if e.suitable(url) and e.IE_NAME != 'generic':
                return True
        return False

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        if cls.is_supported(url):
            try:
                loop = loop or asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                if 'entries' in data:
                    # take first item from a playlist
                    data = data['entries'][0]
                filename = data['title'] if stream else ytdl.prepare_filename(data)
                return filename, data['title']
            except Exception as e:
                print('YTDL EXCEPTION:', e)
        else:
            print('Current url is not a valid youtube link!')
            return False, False

    @classmethod
    async def get_title(cls, url):
        if cls.is_supported(url):
            try:
                with ytdl:
                    info_dict = ytdl.extract_info(url, download=False)
                    video_title = info_dict.get('title', None)
            except Exception as inst:
                print('get titile exception', inst)
                raise Exception(inst)
            return video_title
        else:
            print('Current url is not a valid youtube link!')
            return False
