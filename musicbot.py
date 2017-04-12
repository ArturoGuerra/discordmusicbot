#!/usr/bin/env python3.6
import sys
import uuid
import json
import regex
import config
import random
import getpass
import asyncio
import discord
import logging
import playlist
import commands
import musicplayer
import threading
import datetime as dt

class MusicApplication():
    color_blue = 0x1EA1F1
    color_red = 0xCD160B
    def __init__(self):
        self.client = discord.Client()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('discord')
        self.loadPlaylist = playlist.loadPlaylist
        self.musicPlaylists = playlist.Playlists(self)
        self.musicPlayer = musicplayer.musicPlayer
        self.musicClient = musicplayer.musicClient(self)
        self.app_lock = threading.Lock()
        self.config = config.Config(self)
        self.channels = config.Channels(self).channels
    def voice_client(self, server):
        return self.client.voice_client_server(server)
    def voiceplayer(self, server):
        try:
            return self.musicClient.voice_clients[server]
        except KeyError:
            raise KeyError("Voice Player not found")
    def make_embed(self, field_list, title="", desc="", title_url="", author_url=None, inline=True, footer=None, thumb=None, footer_url=None, color=color_blue, icon_url=None, set_image=None):
        embed = discord.Embed(title=title, url=title_url, description=desc, colour=color)
        if not author_url:
            author_url = f"https://discordapp.com/oauth2/authorize?client_id={app.client.user.id}&scope=bot&permissions=2146958463"
        if set_image:
            embed.set_image(url=set_image)
        if not icon_url:
            embed.set_author(name=self.client.user.name, url=author_url, icon_url=self.client.user.avatar_url)
        else:
            embed.set_author(name=self.client.user.name, url=author_url, icon_url=icon_url)
        if not footer:
            footer = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if field_list:
            for field in field_list:
                embed.add_field(name=field[0],value=field[1], inline=inline)
        if thumb:
            embed.set_thumbnail(url=thumb)
        if footer:
            if footer_url:
                embed.set_footer(text=footer, icon_url=footer_url)
            else:
                embed.set_footer(text=footer)
        return embed


app = MusicApplication()
def main():
    app.client.run(app.config.token())

@app.client.event
async def on_ready():
    app.logger.info("MadarWusic is online")
    app.musicPlaylists.scan_playlists()
    for server in app.channels:
        server_obj = discord.utils.get(app.client.servers, id=server)
        channel = discord.utils.get(server_obj.channels, id=app.channels[server])
        try:
            await app.musicClient.voice_connect(channel)
        except Exception as e:
            app.logger.error(e)
@app.client.event
async def on_message(message):
    recmp = regex.compile(r"^\{}[A-z0-9]+.*".format(app.config.prefix()))
    if recmp.match(message.content):
        splitmsg = message.content.split(' ')
        cmd = splitmsg[0].strip(app.config.prefix())
        args = splitmsg[1:]
        if cmd == "selectplaylist":
            await commands.on_select_playlist(message, app, args, cmd)
        elif cmd == "play":
            await commands.on_youtube_play(message, app, args, cmd)
        elif cmd == "volume":
            await commands.on_volume(message, app, args, cmd)
        elif cmd == "join":
            await commands.on_voice_connect(message, app, args, cmd)
        elif cmd == "leave":
            await commands.on_voice_disconnect(message, app, args, cmd)
        elif cmd == "pause":
            await commands.on_voice_pause(message, app, args, cmd)
        elif cmd == "resume":
            await commands.on_voice_resume(message, app, args, cmd)
        elif cmd == "skip":
            await commands.on_voice_skip(message, app, args, cmd)
        elif cmd == "playing":
            await commands.on_voice_playing(message, app, args, cmd)
        elif cmd == "setdefaultchannel":
            await commands.on_voice_set_default_channel(message, app, args, cmd)
        elif cmd == "listplaylists":
            await commands.on_list_playlists(message, app, args, cmd)
        elif cmd == "startqueue":
            await commands.on_voice_startqueue(message, app, args, cmd)
        elif cmd == "clearqueue":
            await commands.on_voice_clearqueue(message. app, args, cmd)
        elif cmd == "stop":
            await commands.on_voice_stop(message, app, args, cmd)
@app.client.event
async def on_server_join(server):
    pass

@app.client.event
async def on_server_leave(server):
    pass

if __name__ == "__main__":
    app.logger.info("Started as script...")
    main()
