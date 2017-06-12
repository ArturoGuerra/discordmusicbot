import os
import time
import regex
import aiohttp
import asyncio
import discord
import requests
import threading
from queue import Queue

class musicPlayer():
    def __init__(self, server, app, volume=100):
        self.app = app
        self.player = None
        self.thread = None
        self.skipcount = 0
        self.queue = Queue()
        self.skippers = list()
        self.server_id = server
        self.__lock = threading.Lock()
        self.tts_cmp = regex.compile(r"^audio([A-f0-9])+\.mp3")
        self.default_volume = min(max(float(int(volume))/100, 0.1), 2.0)
        self.yt_search_cmp = regex.compile(r"^(ytsearch:)([A-z0-9]+.*)")
        self.yt_url_cmp =  regex.compile(r"^(?:http(?:s)?:\/\/)?(?:www\.)?(?:youtube\.com)(?:(\/watch\?v=(?!\S+&list=))?(\/watch\?v=\S+&list=)?(\/playlist\?list=)?)(\S+)$")
    async def music_player(self, server):
        if self.__lock.acquire(timeout=2):
            self.app.logger.info("Acquired Lock")
            while self.__lock.locked():
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
        if self.__lock.locked():
            self.__lock.release()
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
                self.app.logger.info("Search item detected")
                player = await self.app.musicClient.voice_client(server).create_ytdl_player(item)
            else:
                self.app.logger.info("None of the above detected")
                player = await self.app.musicClient.voice_client(server).create_ytdl_player(f"ytsearch:{item}")
            return player
        except Exception as e:
            self.app.logger.error(e)
            return e
    async def playlistparser(self, url):
        match = self.yt_url_cmp.match(url)
        if match.group(2):
            url = f"https://www.youtube.com/playlist?list={str(match.group(4))}"
        async with aiohttp.ClientSession(loop=self.app.loop) as session:
            async with session.get(url) as response:
                youtube_result = await response.text()
        recmp = regex.compile(r"watch\?v=\S+?list={}".format(str(match.group(4))))
        urls = recmp.findall(youtube_result)
        urlist = list()
        if urls:
            for url in urls:
                url = str(url)
                url = url[:url.index('&')]
                url = f"https://www.youtube.com/{url}"
                if not url in urlist:
                    urlist.append(url)
        return urlist
    def playerdecorator(func):
        def player_wrapper(self):
            if self.__lock.locked() == False:
                server = discord.utils.get(self.app.client.servers, id=self.server_id)
                if server:
                    self.app.logger.info("Starting Player Thread...")
                    self.thread = self.app.client.loop.create_task(self.music_player(server))
            return func(self)
        return player_wrapper
    @playerdecorator
    def play(self):
        self.app.logger.info("Trying to start voice player...")
    @playerdecorator
    def start(self):
        if (self.__lock.locked() == True) and self.player:
            try:
                self.player.start()
            except AttributeError:
                self.app.logger.error("Error starting player")
    @playerdecorator
    def stop(self):
        if (self.__lock.locked() == True) and self.player:
            try:
                self.player.stop()
            except AttributeError:
                self.app.logger.error("Error stopping player")
    @playerdecorator
    def pause(self):
        if (self.__lock.locked() == True) and self.player:
            try:
                self.player.pause()
            except AttributeError:
                self.app.logger.error("Error pausing player")
    @playerdecorator
    def resume(self):
        if (self.__lock.locked() == True) and self.player:
            try:
                self.player.resume()
            except AttributeError:
                self.app.logger.error("Error resuming player")

class musicClient():
    def __init__(self, app):
        self.voice_players = dict()
        self.voice_clients = dict()
        self.app = app
    def voice_client(self, server):
        try:
            return self.voice_clients[server.id]
        except KeyError:
            return None
    async def voice_connect(self, channel):
        app = self.app
        Player = musicPlayer(channel.server.id, app)
        try:
            if not self.voice_client(channel.server):
                voiceClient = await self.app.client.join_voice_channel(channel)
                self.voice_players[channel.server.id] = Player
                self.voice_clients[channel.server.id] = voiceClient
                return voiceClient
        except Exception as e:
            self.app.logger.error(e)
    async def voice_disconnect(self, server):
        try:
            for i in list(self.voice_players[server.id].queue.queue):
                p = self.voice_players[server.id].queue.get()
            try:
                await self.voice_client(server).disconnect()
            except: pass
            del self.voice_players[server.id]
            del self.voice_clients[server.id]
        except Exception as e:
            self.app.logger.error(f"musicPlayer error: {e}")
