import os
import regex
import discord
class Playlists():
    def __init__(self, app):
        self.app = app
        self.playlists = dict()
        self.youtube = regex.compile(r"^(?:http(s)?:\/\/)?(www\.)?(youtube\.com)(/watch\?)[A-z\=\&]+.*")
        self.playlist_cmp = regex.compile("^([A-z0-9])+\.txt")
    def scan_playlists(self):
        for playlist in os.listdir("playlists"):
            if not playlist in self.playlists:
                self.playlists[playlist] = list()
            with open(playlist, 'r') as f:
                for line in f:
                    if self.youtube.match(line):
                        self.playlists[playlist].append(line)
                self.app.logger.info(f"Loaded playlist: {playlist}")
    def delete_playlist(self, name):
        pass
        #TODO
class loadPlaylist():
    def __init__(self, app, voiceplayer, playlist):
        self.app = app
        self.playlists = self.app.musicPlaylists
        self.playlist = playlist
        self.voiceplayer = voiceplayer
    def load_playlist(self):
        try:
            playlist = self.playlists[self.playlist]
        except (IndexError, ValueError):
            self.app.logger.error("Playlist not found")
        for song in playlist:
            self.app.logger.info(f"Loaded: {song}")
            voiceplayer.queue.put(song)
        voiceplayer.play()

