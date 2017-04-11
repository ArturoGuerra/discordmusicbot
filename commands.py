import regex
import asyncio
import discord
import playlist

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
            app.voiceplayer(message.server.id).player = vol
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
async def on_list_playlists(message, app, args, cmd):
    x = 0
    playlist_list=list()
    try:
        for playlist in app.musicPlaylists:
            x += 1
            playlist_list.append((f"Playlist {x}", playlist))
        em = app.make_embed(playlist_list)
        await app.send_reply(message.channel, em)
    except Exception as e:
        app.logger.error(e)
async def on_voice_connect(message, app, args, cmd):
    try:
        if len(args) > 0:
            channel = discord.utils.get(message.server.channels, id=args[0], type=ChannelType.voice)
        else:
            channel = message.author.voice.voice_channel
        await app.musicClient.voice_connect(channel)
    except Exception as e:
        app.logger.error(e)
async def on_voice_disconnect(message, app, args, cmd):
    try:
        await app.musicClient.voice_diconnect(message.server)
    except Exception as e:
        app.logger.error(e)
async def on_youtube_play(message, app, args, cmd):
    try:
        if app.voiceplayer(message.server.id).youtube_cmp(args[0]):
            app.voiceplayer(message.server.id).queue.put(args[0])
    except Exception as e:
        app.logger.error(e)
async def on_voice_startqueue(message, app, args, cmd):
    try:
        app.voiceplayer(message.server.id).play()
    except Exception as e:
        app.logger.error(e)
async def on_voice_stop(message, app, args, cmd):
    try:
        for i in app.voiceplayer(message.server.id).queue.queue:
            app.voiceplayer(message.server.id).queue.get()
        await app.voiceplayer(message.server.id).stop()
    except Exception as e:
        app.loggger.info(e)
async def on_voice_clearqueue(message, app, args, cmd):
    try:
        for i in app.voiceplayer(message.server.id).queue.queue:
            app.voiceplayer(message.server.id).queue.get()
    except Exception as e:
        app.logger.error(e)
async def on_voice_skip(message, app, args, cmd):
    try:
        await app.voiceplayer(message.server.id).stop()
    except Exception as e:
        app.loggger.error(e)
async def on_voice_playing(message, app, args, cmd):
    pass
async def on_select_playlist(message, app, args, cmd):
    try:
        voiceplayer = app.voiceplayer(message.server.id)
        playlist = args[0]
        select_playlist = playlist.loadPlaylist(app, voiceplayer, playlist)
        select_playlist.load_playlist()
    except (IndexError, ValueError):
        app.logger.error("Playlist not found")
