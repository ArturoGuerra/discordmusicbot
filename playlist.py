import os
import regex
import discord
class Playlists():
    def __init__(self, app):
        self.app = app
        self.playlists = dict()
        self.youtube_playlist = regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(youtube\.com)((\/watch\?v=[A-z0-9]+   &list=)?(\/playlist\?list=)?)([A-z0-9\=\&]+.*)")
        self.youtube = regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(youtube\.com)(\/watch\?v=(?![A-z0-9]+&list=))([A-z0-9\=\&]+.*)")
        self.playlist_cmp = regex.compile("^([A-z0-9])+\.txt")
        self.playlistdir = "playlists"
    def scan_playlists(self):
        for playlist in os.listdir(self.playlistdir):
            name = playlist.replace('.txt', '')
            if not name in self.playlists:
                self.playlists[name] = list()
            with open(f"./{self.playlistdir}/{playlist}", 'r') as f:
                for line in f:
                    if self.youtube.match(line):
                        self.playlists[name].append(line)
                    elif self.youtube_playlist.match(line):
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
    def load_playlist(self):
        try:
            playlist = self.playlists[self.playlist]
        except (IndexError, ValueError):
            self.app.logger.error("Playlist not found")
            raise ValueError("Playlist not found")
        for song in playlist:
            if self.voiceplayer.yt_url_cmp.match(song):
                self.app.logger.info(f"Loaded:{song}")
                self.voiceplayer.queue.put(song.rstrip())
            elif self.voiceplayer.yt_playlist_cmp.match(song):
                url = song.rstrip()
                urls = self.voiceplayer.playlistparser(url)
                for url in urls:
                    if self.voiceplayer.yt_url_cmp.match(url):
                        self.app.logger.info(f"Loaded: {url}")
                        self.voiceplayer.queue.put(url)
        self.voiceplayer.play()
