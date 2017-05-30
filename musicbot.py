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
from persistence import *
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
        self.parser.add_argument("--no-db", help="Starts the bot without the database", action="store_true")
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

        self.musicPlayer = musicplayer.musicPlayer
        self.musicClient = musicplayer.musicClient(self)
        self.app_lock = threading.Lock()
        self.config = config.Config(self)
    def voice_client(self, server):
        return self.client.voice_client_in(server)
    def initdb(self):
        self.app_lock.acquire()
        self.logger.info("Application lock acquired")
        self.logger.info("Connectiong to database...")
        if not my_db:
            app.logger.warning("Faild to connect")
            return
        my_db.connect()
        if Servers.table_exists() and Playlists.table_exists():
            app.logger.info("Connected to Database !!!!")
        else:
            self.logger.info("Populating Database...")
            my_db.create_tables([Servers, Playlists], safe=True)
            self.logger.info("Database is now populated")
        my_db.close()
        self.app_lock.release()
        self.logger.info("Application lock released")
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
    async def admin_pm(self, msg):
        try:
            app_info  = await app.client.application_info()
            admin_user = app_info.owner
            await app.client.start_private_message(admin_user)
            await app.client.send_message(admin_user, msg)
        except Exception as e:
            self.logger.info(e)
    def run(self, *args, **kwargs):
        try:
            self.logger.info("Connecting to discord...")
            self.loop.run_until_complete(self.client.start(*args, **kwargs))
        except Exception as e:
            self.logger.info(f"Disconnecting from discord with error: {e}")
            self.loop.run_until_complete(self.client.logout())
        finally:
            self.logger.info("Closing Loop")
            self.loop.close()




app = MusicApplication()
def main():
    if app.args.setup:
        config.ConfigGenerator(app).bot_setup()
        sys.exit()
    if app.args.dry_run:
        app.logger.info("Bot Dry Run")
        sys.exit()
    if not app.args.no_db:
        app.initdb()
        app.logger.info("Initiazing Database!!!")
    app.run(app.config.token)


@app.client.event
async def on_ready():
    app.logger.info(f"{app.client.user.name} is online")
    app.logger.info(f"Shard ID: {app.client.shard_id} Shard Count: {app.client.shard_count}")
    await app.admin_pm(f"Shard ID: {app.client.shard_id} Shard Count: {app.client.shard_count}")
    for server in Servers.select():
        try:
            channel = app.client.get_channel(str(server.channel))
            await app.musicClient.voice_connect(channel)
            playlist_queue = Playlists.select().where(Playlists.playlist == server.playlist)
            selectplaylist = playlist.loadPlaylist(app, app.voiceplayer(channel.server.id), playlist_queue)
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
                if cmd == "addplaylist":
                    await commands.on_add_playlist(message, app, args, cmd)
                elif cmd == "rmplaylist":
                    await commands.on_remove_playlist(message, app, args, cmd)
                elif cmd == "init":
                    await commands.on_init(message, app, args, cmd)
            if permlvl >= 5:
                if cmd == "clearqueue":
                    await commands.on_voice_clearqueue(message, app, args, cmd)
                elif cmd == "serverconfig":
                    await commands.on_set_default_channel(message, app, args, cmd)
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
async def on_voice_state_update(before, after):
    app.logger.info("Voice state update")
    try:
        voice = app.voice_client(after.server)
        if not voice:
            raise TypeError("Voice Client not found")
        voice_members = voice.channel.voice_members
        if len(voice_members) == 1:
            app.voiceplayer(after.server.id).pause()
            app.logger.info(f"Paused voice player in: {after.server.name}")
        elif len(voice_members) > 1:
            app.voiceplayer(after.server.id).resume()
            app.logger.info(f"Resumed voice player in: {after.server.name}")
    except Exception as e:
        app.logger.error(e)

@app.client.event
async def on_server_join(server):
    await app.admin_pm(f"Joined: {server.name}")
    try:
        s = Servers.get(Servers.server == server.id)
    except:
        s = Servers.create(server=server.id)

@app.client.event
async def on_server_leave(server):
    await app.admin_pm(f"Left: {server.name}")
    try:
        Servers.delete().where(Servers.server == server.id)
    except: pass

if __name__ == "__main__":
    app.logger.info("Started as script...")
    main()
