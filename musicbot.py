#!/usr/bin/env python3.6
import sys
import uuid
import json
import regex
import config
import random
import uvloop
import getpass
import asyncio
import discord
import logging
import playlist
import commands
import argparse
import threading
import musicplayer
import datetime as dt
import concurrent.futures
class MusicApplication():
    color_blue = 0x1EA1F1
    color_red = 0xCD160B
    FORMAT = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    def __init__(self):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.get_event_loop()
        self.pool = concurrent.futures.ThreadPoolExecutor(10)
        self.loop.set_default_executor(self.pool)
        self.logger = logging.getLogger('discord')
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--dry-run", help="Runs the bot without connecting to discord", action="store_true")
        self.parser.add_argument("--setup", help="Runs bot setup and creates config file", action="store_true")
        self.parser.add_argument("--shard-id", help="Instance shard ID", type=int, nargs='?')
        self.parser.add_argument("--shard-count", help="Total number of shards", type=int, nargs='?')
        self.args = self.parser.parse_args()
        if (isinstance(self.args.shard_count, int)) and isinstance(self.args.shard_id, int):
            self.logger.info(f"Sharding: Shards {self.args.shard_count} Shard ID: {self.args.shard_id}")
            self.client = discord.Client(loop=self.loop, shard_id=self.args.shard_id, shard_count=self.args.shard_count)
        else:
            self.logger.warning("No shards found")
            self.client = discord.Client(loop=self.loop)
        self.loadPlaylist = playlist.loadPlaylist
        self.musicPlaylists = playlist.Playlists(self)
        self.musicPlayer = musicplayer.musicPlayer
        self.musicClient = musicplayer.musicClient(self)
        self.app_lock = threading.Lock()
        self.config = config.Config(self)
        self.channels = config.Channels(self).channels
    def voice_client(self, server):
        return self.client.voice_client_in(server)
    def get_permlvl(self, message):
        if message.author.id in self.config.owners:
            return 10
        if message.author.server_permissions.administrator:
            return 9
        elif message.author.server_permissions.mute_members and message.author.server_permissions.deafen_members:
            return 6
        else:
            return 0
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
    async def send_reply(self, channel, em):
        try:
            await self.client.send_message(channel, embed=em)
        except Exception as e:
            self.logger.error(f"Error sending Message: {e}")
    def bot_setup(self):
        config = dict()
        token = getpass.getpass("Token: ")
        prefix = input("Prefix: ")
        config['token'] = token
        config['prefix'] = prefix
        config['owners'] = list()
        channels = list()
        channel_id = input("Channel ID: ")
        channels.append(channel_id)
        with open('./config/config.json', 'w') as f:
            json.dump(config, f)
        with open('./config/channels.json', 'w') as f:
            json.dump(channels, f)
    def bot_login(self, *args, **kwargs):
        try:
            app.logger.info("Connecting to discord...")
            app.loop.run_until_complete(app.client.start(*args, **kwargs))
        except:
            app.logger.info("Disconnecting from discord...")
            app.loop.run_until_complete(app.client.logout())
        finally:
            app.logger.info("Closing loop...")
            app.loop.close()

app = MusicApplication()
def main():
    if app.args.setup:
        app.bot_setup()
        sys.exit()
    if app.args.dry_run:
        app.logger.info("Bot Dry Run")
        sys.exit()
    app.bot_login(app.config.token)
@app.client.event
async def on_ready():
    app.logger.info(f"{app.client.name} is online")
    app.musicPlaylists.clear_playlists()
    app.musicPlaylists.scan_playlists()
    for channel_id in app.channels:
        try:
            channel = app.client.get_channel(channel_id)
            await app.musicClient.voice_connect(channel)
            selectplaylist = playlist.loadPlaylist(app, app.voiceplayer(channel.server.id), "top")
            await selectplaylist.load_playlist()
        except Exception as e:
            app.logger.error(f"Connecting error: {e}")
@app.client.event
async def on_message(message):
    recmp = regex.compile(r"^\{}[A-z0-9]+.*".format(app.config.prefix))
    if recmp.match(message.content):
        try:
            splitmsg = message.content.split(' ')
            cmd = splitmsg[0].strip(app.config.prefix)
            args = splitmsg[1:]
            permlvl = app.get_permlvl(message)
            app.logger.info(f"User level: {permlvl}")
            if permlvl >= 10:
                if cmd == "reloadplaylists":
                    await commands.on_reload_playlists(message, app, args, cmd)
            if permlvl >= 5:
                if cmd == "clearqueue":
                    await commands.on_voice_clearqueue(message. app, args, cmd)
                elif cmd == "stop":
                    await commands.on_voice_stop(message, app, args, cmd)
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
                elif cmd == "forceskip":
                    await commands.on_voice_force_skip(message, app, args, cmd)
            if permlvl >= 0:
                if cmd == "selectplaylist":
                    await commands.on_select_playlist(message, app, args, cmd)
                elif cmd == "play":
                    await commands.on_youtube_play(message, app, args, cmd)
                elif cmd == "skip":
                    await commands.on_voice_skip(message, app, args, cmd)
                elif cmd == "playing":
                    await commands.on_voice_playing(message, app, args, cmd)
                elif cmd == "listplaylists":
                    await commands.on_list_playlists(message, app, args, cmd)
                elif cmd == "startqueue":
                    await commands.on_voice_startqueue(message, app, args, cmd)
                elif cmd == "queued":
                    await commands.on_queued(message, app, args, cmd)
                elif cmd == "help":
                    await commands.on_help(message, app, args, cmd)
        except Exception as e:
            app.logger.error(f"Exception in message: {e}")
@app.client.event
async def on_server_join(server):
    pass

@app.client.event
async def on_server_leave(server):
    pass

if __name__ == "__main__":
    app.logger.info("Started as script...")
    main()
