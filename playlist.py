import os
import regex
import discord
class Playlists():
    def __init__(self, app):
        self.app = app
        self.playlists = dict()
        self.youtube = regex.compile(r"^(?:http(s)?:\/\/)?(www\.)?(youtube\.com)(/watch\?)[A-z\=\&]+.*")
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
                self.app.logger.info(f"Loaded playlist: {playlist}")
    def reload_playlists(self):
        for i in self.playlists:
            del self.playlists[i]
        self.scan_playlists()
    def clear_playlists(self):
        for i in self.playlists:
            del self.playlists[i]
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
            self.app.logger.info(f"Loaded:{song}")
            self.voiceplayer.queue.put(song.rstrip())
        self.voiceplayer.play()

