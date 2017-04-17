import os
import regex
import asyncio
import discord
class Playlists():
    def __init__(self, app):
        self.app = app
        self.playlists = dict()
        self.youtube = regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(?:youtube\.com)(?:(\/watch\?v=(?!\S+&list=))?(\/watch\?v=\S+&list=)?(\/playlist\?list=)?)(\S+)$")
        self.playlist_cmp = regex.compile("^([A-z0-9])+\.txt")
        self.playlistdir = "playlists"
    def scan_playlists(self):
        for playlist in os.listdir(self.playlistdir):
            name = playlist.replace('.txt', '')
            if not name in self.playlists:
                self.playlists[name] = list()
            with open(f"./{self.playlistdir}/{playlist}", 'r') as f:
                for line in f:
                    match = self.youtube.match(line)
                    if match:
                        self.playlists[name].append(line)
                self.app.logger.info(f"Loaded playlist: {playlist}")
    def clear_playlists(self):
        self.playlists = dict()
    def reload_playlists(self):
        self.clear_playlists()
        self.scan_playlists()
class loadPlaylist():
    def __init__(self, app, voiceplayer, playlist):
        self.app = app
        self.playlists = self.app.musicPlaylists.playlists
        self.playlist = playlist
        self.voiceplayer = voiceplayer
    async def load_playlist(self):
        try:
            playlist = self.playlists[self.playlist]
        except (IndexError, ValueError):
            self.app.logger.error("Playlist not found")
            raise ValueError("Playlist not found")
        for song in playlist:
            url = song.rstrip()
            match = self.voiceplayer.yt_url_cmp.match(song)
            if match:
                if match.group(1):
                    self.app.logger.info(f"Loaded:{url}")
                    self.voiceplayer.queue.put(url)
                elif match.group(2) or match.group(3):
                    urls = await self.voiceplayer.playlistparser(url)
                    for url in urls:
                        if self.voiceplayer.yt_url_cmp.match(url):
                            self.app.logger.info(f"Loaded: {url}")
                            self.voiceplayer.queue.put(url)
        self.voiceplayer.play()
