import regex
import asyncio
import discord
import playlist
from persistence import *

def peeweeconnect(func):
    async def wrapper(*args, **kwargs):
        my_db.connect()
        function = await func(*args)
        my_db.close()
        return function
    return wrapper

@peeweeconnect
async def on_set_default_channel(message, app, args, cmd):
    try:
        app.logger.info(f"Server Setup: {message.server.name}")
        if len(args) > 0:
            app.logger.info(f"Channel: {args[0]} Playlist: {args[1]}")
            Servers.update(channel=args[0], playlist=args[1]).where(Servers.server == message.server.id).execute()
        else:
            app.logger.info(f"Channel: {args[0]}")
            Servers.update(channel=args[0]).where(Servers.server == message.server.id).execute()
    except Exception as e:
        app.logger.error(e)

@peeweeconnect
async def on_init(message, app, args, cmd):
    try:
        for server in list(app.client.servers):
            try:
                s = Servers.get(Servers.server == server.id)
            except Exception as e:
                app.logger.error(f"Server {server.name} not found, inserting....")
                s = Servers.create(server=server.id)
    except Exception as e:
        app.logger.error(e)

async def on_help(message, app, args, cmd):
    cmd_list = list()
    cmd_list.append(("Volume", "Changes music volume"))
    cmd_list.append(("clearqueue", "Clears queued items"))
    cmd_list.append(("join", "Joins voice channel"))
    cmd_list.append(("leave", "Leaves voice channel"))
    cmd_list.append(("stop", "Stops voice player"))
    cmd_list.append(("resume", "Resumes music playback"))
    cmd_list.append(("forceskip", "Forceskips current track"))
    cmd_list.append(("play", "Plays youtube video url or searches youtube"))
    cmd_list.append(("selectplaylist", "Selects a playlists to queue"))
    cmd_list.append(("skip", "Skips track after enough people vote"))
    cmd_list.append(("playing", "Info about current playing song"))
    cmd_list.append(("startqueue", "Force starts queue"))
    cmd_list.append(("listplaylists", "List of all available playlists"))
    cmd_list.append(("queued", "Queued items"))
    cmd_list.append(("help", "This command"))
    em = app.make_embed(cmd_list, inline=False)
    await app.send_reply(message.author, em)

async def on_volume(message, app, args, cmd):
    vol_msg=list()
    try:
        app.voiceplayer(message.server.id)
        if not app.voiceplayer(message.server.id).player:
            raise AttributeError("Client is not playing anything")
        if len(args) == 0:
            raise IndexError(str(int(app.voiceplayer(message.server.id).player.volume * 100)))
        volregex = regex.compile("^([0-9])+$")
        if volregex.match(args[0]):
            vol = min(max(float(args[0])/100, 0.1), 2.0)
            app.voiceplayer(message.server.id).default_volume = vol
            app.voiceplayer(message.server.id).player.volume = vol
            vol_msg.append(("Volume Changed", f"Volume has been set to {int(vol * 100)}"))
        else:
            raise IndexError("Volume has to be a number between 1 & 200")
    except (IndexError, AttributeError) as e:
        vol_msg.append(("Volume", e))
    except KeyError:
        vol_msg.append(("Voice Client Error", "Voice player was not found"))
    if len(vol_msg) > 0:
        em = app.make_embed(vol_msg)
        await app.send_reply(message.channel, em)
@peeweeconnect
async def on_list_playlists(message, app, args, cmd):
    try:
        playlists = Playlists.select()
        playlist_list = list()
        for playlist in playlists:
            if playlist.playlist not in playlist_list:
                playlist_list.append(playlist.playlist)
        msg_list=list()
        num=0
        for playlist in playlist_list:
            num+=1
            msg_list.append((num, playlist))
        if len(msg_list) > 0:
            embed = app.make_embed(msg_list)
            await app.send_reply(message.channel, embed)
    except Exception as e:
        app.logger.error(e)



async def on_voice_connect(message, app, args, cmd):
    connectlist=list()
    try:
        if len(args) > 0:
            channel = discord.utils.get(message.server.channels, id=args[0], type=ChannelType.voice)
        else:
            channel = message.author.voice.voice_channel
        if not channel:
            raise discord.DiscordException("Channel not found")
        await app.musicClient.voice_connect(channel)
        connectlist.append(("Connected to voice", f"Connected to {channel.name}"))
    except discord.Forbidden as e:
        app.logger.error(e)
        connectlist.append(("Permission Error", f"Permission error when connecting to {channel.name}"))
    except discord.DiscordException as e:
        app.logger.error(e)
        connectlist.append(("Channel Error", e))
    except Exception as e:
        app.logger.error(e)
    if len(connectlist) > 0:
        em = app.make_embed(connectlist)
        await app.send_reply(message.channel, em)
async def on_voice_disconnect(message, app, args, cmd):
    try:
        await app.musicClient.voice_disconnect(message.server)
        em = app.make_embed(None, title="Voice Update", desc="Voice Client disconnected from voice")
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
async def on_youtube_play(message, app, args, cmd):
    try:
        await app.musicClient.voice_connect(message.author.voice.voice_channel)
    except Exception as e:
        app.logger.error(e)
    try:
        while app.voice_client(message.server) == None:
            await asyncio.sleep(1)
        ytmatch = app.voiceplayer(message.server.id).yt_url_cmp.match(args[0])
        if ytmatch:
            if ytmatch.group(1):
                app.voiceplayer(message.server.id).queue.put(args[0])
            elif ytmatch.group(2) or ytmatch.group(3):
                urls = await app.voiceplayer(message.server.id).playlistparser(args[0])
                for url in urls:
                    if app.voiceplayer(message.server.id).yt_url_cmp.match(url):
                        app.logger.info(f"Adding url to queue: {url}")
                        app.voiceplayer(message.server.id).queue.put(url)
        else:
            app.logger.info(f"Seaching youtube...")
            app.voiceplayer(message.server.id).queue.put(f"ytsearch:{' '.join(args[0:])}")
        app.voiceplayer(message.server.id).play()
        await app.client.send_message(message.channel, "Your song has been added to the queue")
    except Exception as e:
        app.logger.error(e)

async def on_voice_startqueue(message, app, args, cmd):
    try:
        app.voiceplayer(message.server.id).play()
    except Exception as e:
        app.logger.error(e)
async def on_queued(message, app, args, cmd):
    try:
        queuesize = app.voiceplayer(message.server.id).queue.qsize()
        em = app.make_embed(None, title="Queue", desc=f"{queuesize} Items queued")
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
async def on_voice_clearqueue(message, app, args, cmd):
    try:
        x = app.voiceplayer(message.server.id).queue.qsize()
        for i in list(app.voiceplayer(message.server.id).queue.queue):
            app.voiceplayer(message.server.id).queue.get()
        em = app.make_embed(None, title="Voice Queue", desc=f"{x} items have been removed from the queue")
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
async def on_voice_stop(message, app, args, cmd):
    try:
        player = app.voiceplayer(message.server.id)
    except:
        return
    try:
        for i in list(player.queue.queue):
            player.queue.get()
        player.stop()
    except Exception as e:
        app.logger.error(e)
        return
    await app.client.send_message(message.channel, "Voice player stopped")
async def on_voice_skip(message, app, args, cmd):
    queuelist=list()
    try:
        if app.voiceplayer(message.server.id).skipcount == 4:
            app.voiceplayer(message.server.id).skippers = list()
            app.voiceplayer(message.server.id).stop()
            app.logger.info("Skipping...")
            queuelist.append(("VoiceQueue", "Skipped song"))
        elif not message.author.id in app.voiceplayer(message.server.id).skippers:
            app.logger.info("Skip count is not 5")
            app.voiceplayer(message.server.id).skippers.append(message.author.id)
            app.voiceplayer(message.server.id).skipcount += 1
            queuelist.append(("VoiceQueue", f"{int(5 - app.voiceplayer(message.server.id).skipcount)} skips left"))
    except Exception as e:
        app.logger.error(e)
        return
    if len(queuelist) > 0:
        em = app.make_embed(queuelist)
        await app.send_reply(message.channel, em)
async def on_voice_force_skip(message, app, args, cmd):
    try:
        app.logger.info("Forced skipped song")
        app.voiceplayer(message.server.id).stop()
        em = app.make_embed(None, title="Force Skip", desc="User with perm level 5 or above force skipped song")
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
        return
async def on_voice_playing(message, app, args, cmd):
    try:
        player = app.voiceplayer(message.server.id).player
    except:
        return
    try:
        playerlist=list()
        playerlist.append(("Title", player.title))
        playerlist.append(("Duration", player.duration))
        em = app.make_embed(playerlist, inline=False)
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
async def on_voice_resume(message, app, args, cmd):
    try:
        app.voiceplayer(message.server.id).player.resume()
    except Exception as e:
        app.logger.error(e)
        return
    await app.client.send_message(message.channel, "Voice player resumed")
async def on_voice_pause(message, app, args, cmd):
    try:
        app.voiceplayer(message.server.id).player.pause()
    except Exception as e:
        app.logger.error(e)
        return
    await app.client.send_message(message.channel, "Voice player paused")
@peeweeconnect
async def on_select_playlist(message, app, args, cmd):
    try:
        voiceplayer = app.voiceplayer(message.server.id)
    except KeyError:
        await app.musicClient.voice_connect(message.author.voice.voice_channel)
        voiceplayer = app.voiceplayer(message.server.id)
    try:
        playlist_query = Playlists.select().where(Playlists.playlist == args[0])
        select_playlist = playlist.loadPlaylist(app, voiceplayer, playlist_query)
        await select_playlist.load_playlist()
    except Exception as e:
        app.logger.error(e)


@peeweeconnect
async def on_add_playlist(message, app, args, cmd):
    try:
        links = args[1:]
        for link in links:
            try:
                Playlists.create(playlist=args[0], link=link)
            except Exception as e:
                app.logger.error(e)
    except Exception as e:
        app.logger.error(e)

@peeweeconnect
async def on_remove_playlist(message, app, args, cmd):
    if len(args) > 1:
        Playlists.delete().where((Playlists.playlist == args[0]) & (Playlists.link == args[1])).execute()
    else:
        Playlists.delete().where(Playlists.playlist == args[0]).execute()


