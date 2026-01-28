from itertools import count
import itertools
import logging
from dotenv import load_dotenv
load_dotenv("local.env")
import os

handler = logging.FileHandler(filename='robort.log', encoding='utf-8', mode='w')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('robort')
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.setLevel(LOG_LEVEL)
logger.addHandler(handler)
logger.propagate = False

import discord
from discord.ext import commands
from db import set_channel, get_channel


MAX_PINS = 50
TOKEN = os.getenv("DISCORD_TOKEN")
PATCH_NOTES_CHANNEL = int(os.getenv("PATCH_NOTES_CHANNEL"))


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

def prefix(bot, message):
    chars = [(c.lower(), c.upper()) if c.isalpha() else (c,) for c in "robort "]
    return [''.join(p) for p in itertools.product(*chars)]

bot = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot ready! Meow :3')
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="meow meow meow meow moew moeow eow eow moew emow meow"))


@bot.event
# when pins update in a guild channel we check if mad pins are exceeded, if true unpin latest pin and archive it
async def on_guild_channel_pins_update(channel, last_pin_time):
    if last_pin_time is None:
        return
    pins = []
    pin = None
    async for message in channel.pins(limit=None):
        pins.append(message)
    c = len(pins)
    c = c if c is not None else 0
    if c >= MAX_PINS:
        await pins[0].unpin(reason="Exceeded max pin limit")
        pin_archive = get_channel(channel.guild)
        if pin_archive is not None:
            archive_channel = channel.guild.get_channel(pin_archive)
            if archive_channel is not None:
                    webhook = await archive_channel.create_webhook(name=f"archive-{pins[0].author.id}")
                    try:
                        files = [await attachment.to_file() for attachment in pins[0].attachments]
                        avatar_url = None
                        if hasattr(pins[0].author, 'display_avatar'):
                            avatar_url = getattr(pins[0].author.display_avatar, 'url', None)
                        await webhook.send(content=pins[0].content + f"\n-# Sent: {pins[0].created_at.strftime('%Y-%m-%d %H:%M')}", username=str(pins[0].author), avatar_url=avatar_url, embeds=pins[0].embeds, files=files)
                    finally:
                        await webhook.delete()

@bot.event
# when a message is sent to internal patch notes channel, forward to all guilds' patch notes channels
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == PATCH_NOTES_CHANNEL:
        if (message.content and "patch" in message.content.lower()) or message.attachments or message.embeds:
            for guild in bot.guilds:
                try:
                    pn_id = get_channel(guild, channel_type="patch_notes")
                    if not pn_id:
                        continue
                    ch = guild.get_channel(pn_id)
                    if ch is None:
                        continue

                    files = [await a.to_file() for a in message.attachments]
                    embeds = message.embeds
                    try:
                        await ch.send(content=message.content or "", embeds=embeds, files=files)
                    except Exception:
                        logger.exception("Failed sending patch notes to guild %s", getattr(guild, 'id', 'unknown'))
                except Exception:
                    logger.exception("Failed forwarding patch notes to guild %s", getattr(guild, 'id', 'unknown'))

    await bot.process_commands(message)

# set pin channel or patch notes channel in guilds setings db
@bot.command()
async def set(ctx, *, arg=None):
    if arg is None:
        msg = await ctx.send(f'Set what? Please provide an argument.')
        await msg.delete(delay=10)
        return
    
    if arg.lower().replace(" ", "") in ('pinchannel', 'pin'):
        if ctx.guild is None:
            return
        
        set_channel(ctx.guild, ctx.channel.id)
        msg = await ctx.send(f'Set pin channel to {ctx.channel.mention}')
        await msg.delete(delay=10)
        return
    
    if arg.lower().strip() in ('patch notes', 'patchnotes'):
        set_channel(ctx.guild, ctx.channel.id, channel_type="patch_notes")
        msg = await ctx.send(f'Set patch notes channel to {ctx.channel.mention}')
        await msg.delete(delay=10)
        return

    msg = await ctx.send(f'Unknown set argument: {arg}')
    await msg.delete(delay=10)

# config bot settings (future use), TBA: set filo/fifo archiving. Currently only fifo is supported.
#                                        enable/disable date stamping of archived pins.
@bot.command()
async def config(ctx, *, arg=None):
    pass

# get pin channel or patch notes channel from guilds settings db
@bot.command()
async def where(ctx, *, arg=None):
    if arg is None:
        msg = await ctx.send(f'Where what? Please provide an argument.')
        await msg.delete(delay=10)
        return
    
    if arg.lower().strip() == 'pin channel':
        if ctx.guild is None:
            msg = await ctx.send('No server context. Use this command in a server.')
            await msg.delete(delay=10)
            return
        
        pin_id = get_channel(ctx.guild)
        if pin_id is None:
            msg = await ctx.send('Pin channel hasn\'t been set yet for this server.')
            await msg.delete(delay=10)
            return
        
        channel = ctx.guild.get_channel(pin_id)
        if  not channel:
            msg = await ctx.send('Pin channel was set but wasn\'t found (maybe the channel it was deleted).')
            await msg.delete(delay=20)
            return
        
        msg = await ctx.send(f'Pin channel is: {channel.mention}')
        await msg.delete(delay=20)
        return

    if arg.lower() == 'am i':
        msg = await ctx.send(f'You are in {ctx.channel.mention} on server {ctx.guild.name}.')
        await msg.delete(delay=20)
        return
    
    if arg.lower() == 'patch notes':
        msg = await ctx.send('Patch notes can be found at:')
        await msg.delete(delay=20)
        return
    msg = await ctx.send(f'Unknown where argument: {arg}')
    await msg.delete(delay=10)

@bot.command()
async def how(ctx, *, args):
    if arg.lower().replace(" ", "") in ('manypins', 'manypin'):
        pins = []
        pin = None
        async for message in channel.pins(limit=None):
            pins.append(message)
        c = len(pins)
        c = c if c is not None else 0
        msg = await ctx.send(f'Maximum pins allowed per channel is {MAX_PINS}. This channel has {c} pinned messages.')
        await msg.delete(delay=20)
        return

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)