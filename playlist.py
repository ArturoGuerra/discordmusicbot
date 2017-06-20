import os
import regex
import asyncio
import discord

class loadPlaylist():
    def __init__(self, app, voiceplayer, playlist):
        self.app = app
        self.playlist = playlist
        self.voiceplayer = voiceplayer
    async def load_playlist(self, autoplay=True):
        for song in self.playlist:
            url = song.link.rstrip()
            match = self.voiceplayer.yt_url_cmp.match(url)
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
        if autoplay:
            self.voiceplayer.play()
