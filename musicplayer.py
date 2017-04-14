import json
import time
import regex
import discord
import asyncio
import threading
from queue import Queue

class musicPlayer():
    def __init__(self, volume,  server, app):
        self.app = app
        self.thread = None
        self.player = None
        self.queue = Queue()
        self.server_id = server
        self.skipcount = 0
        self.skippers = list()
        self.lock = threading.Lock()
        self.tts_cmp = regex.compile(r"^audio([A-f0-9])+\.mp3")
        self.default_volume = min(max(float(int(volume))/100, 0.1), 2.0)
        self.yt_seach_cmp = regex.compile(r"^(ytsearch\:)([A-z0-9]+.*)")
        self.yt_url_cmp =  regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(youtube\.com)(\/watch\?v=(?![A-z0-9]+&list=))([A-z0-9\=\&]+.*)")
        self.no_yt_cmp = regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(youtube\.com)((\/watch\?v=[A-z0-9]+&list=)?(\/playlist\?list=)?)([A-z0-9\=\&]+.*)")
    async def music_player(self, server):
        self.lock.acquire()
        self.app.logger.info("Acquired Lock")
        self.app.logger.info(server)
        while True:
            await asyncio.sleep(2)
            if self.app.musicClient.voice_client(server):
                try:
                    if self.player and not self.player.is_done():
                        pass
                    else:
                        if self.queue.qsize() > 0:
                            try:
                                self.app.logger.info(f"Starting voice player....")
                                item = self.queue.get()
                                self.app.logger.info(f"Got player object...")
                                self.app.logger.info(item)
                                player = await self.encode_audio(item, server)
                                self.skipcount = 0
                                self.skippers = list()
                                self.player = player
                                self.player.volume = self.default_volume
                                self.player.start()
                                while not self.player.is_done():
                                    await asyncio.sleep(1)
                                if self.tts_cmp.match(item):
                                    os.remove(item)
                                    self.app.logger.info("MP3 file removed")
                                self.app.logger.info("Stopping voice player...")
                                self.queue.task_done()
                            except (AttributeError, KeyError, IndexError):
                                self.app.logger.error("Player not found")
                                break
                            except Exception as e:
                                self.app.logger.error(f"Error in voice player: {e}")
                                break
                        else:
                            self.app.logger.info("Queue is empty")
                            break
                except AttributeError:
                    self.app.logger.error("Voice Player not found")
                    break
                except Exception as e:
                    self.app.logger.error(f"Voice Player error: {e}")
                    break
            else:
                self.app.logger.info("VoiceClient not found")
                break
        if self.lock.locked():
            self.lock.release()
            self.app.logger.info("Released Lock")
    async def encode_audio(self, item, server):
        self.app.logger.info("Processing audio...")
        try:
            if self.tts_cmp.match(item):
                self.app.logger.info("MP3 file detected")
                player = self.app.musicClient.voice_client(server).create_ffmpeg_player(item)
            elif self.yt_url_cmp.match(item):
                self.app.logger.info("Youtube url detected")
                player = await self.app.musicClient.voice_client(server).create_ytdl_player(item)
            elif self.yt_search_cmp.match(item):
                self.app.logger.info("Youtube search detected")
                player = await self.app.musicClient.voice_client(server).create_ytdl_player(item)
            else:
                self.app.logger.info("None of the above detected")
                player = await self.app.musicClient.voice_client(server).create_ytdl_player(item)
            return player
        except Exception as e:
            self.app.logger.error(f"Encoder error: {e}")
    def playerdecorator(func):
        def player_wrapper(self):
            if self.lock.locked() == False:
                server = discord.utils.get(self.app.client.servers, id=self.server_id)
                if server:
                    self.thread = self.app.client.loop.create_task(self.music_player(server))
            return func(self)
        return player_wrapper
    @playerdecorator
    def play(self):
        self.app.logger.info("Trying to start player...")
    @playerdecorator
    def start(self):
        if (self.lock.locked() == True) and self.player:
            try:
                self.player.start()
            except Exception as e:
                self.app.logger.error("Player start command error: {e}")
    @playerdecorator
    def stop(self):
        if (self.lock.locked() == True) and self.player:
            try:
                self.player.stop()
            except Exception as e:
                self.app.logger.error(f"Player stop command error: {e}")
    @playerdecorator
    def pause(self):
        if (self.lock.locked() == True) and self.player:
            try:
                self.player.pause()
            except Exception as e:
                self.app.logger.error(f"Player pause command error: {e}")
    @playerdecorator
    def resume(self):
        if (self.lock.locked() == True) and self.player:
            try:
                self.player.resume()
            except Exception as e:
                self.app.logger.error(f"Player resume command error: {e}")

class musicClient():
    def __init__(self, app):
        self.app = app
        self.voice_clients = dict()
    async def voice_connect(self, channel, volume=100):
        try:
            if not self.voice_client(channel.server):
                Player = musicPlayer(volume, channel.server.id, self.app)
                voiceClient = await self.app.client.join_voice_channel(channel)
                self.voice_clients[channel.server.id] = Player
                return voiceClient
        except (AttributeError, IndexError, ValueError):
            self.app.logger.error(f"Error connected to voice channel: {channel.name}")
    async def voice_disconnect(self, server):
        try:
            await self.voice_client(server).disconnect()
            del self.voice_clients[server.id]
        except (AttributeError, IndexError):
            self.app.logger.error("Error while disconnecting from voice channel")
    def voice_client(self, server):
        return self.app.client.voice_client_in(server)
