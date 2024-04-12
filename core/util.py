import asyncio
import datetime
import functools
import time
from typing import Any

import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure


command_status = {
    'crt': False,  # 'crt' adalah nama command, dan True menandakan bahwa command aktif
    'web': False,
}

class isenable(CheckFailure):
    """Exception raised when the message author is not the owner of the bot.

    This inherits from :exc:`CheckFailure`
    """

    pass

class isenable2(CheckFailure):
    """
    Thrown when a user is attempting something, but is not an owner of the bot.
    """

    def __init__(self, message="commnds is disabled!"):
        self.message = message
        super().__init__(self.message)

def is_command_enabled(command_name):
    def decorator(ctx):
        if command_name in command_status and not command_status[command_name]:
            error_message = "Command dinonaktifkan"
            raise commands.CheckFailure(error_message)
        return True
    return commands.check(decorator)


def trigger_typing(func):
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        await ctx.typing()
        return await func(self, ctx, *args, **kwargs)

    return wrapper

def processing_message(func):
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        processing_msg = await ctx.send("Memproses...")

        try:
            # Panggil fungsi asli
            result = await func(self, ctx, *args, **kwargs)
        finally:
            await asyncio.sleep(2)
            await processing_msg.delete()

        return result

    return wrapper

def nsfw_check(func):
    @functools.wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        # Periksa apakah channel adalah NSFW
        if ctx.channel.is_nsfw():
            # Jika channel adalah NSFW, panggil fungsi asli
            result = await func(self, ctx, *args, **kwargs)
        else:
            # Jika channel bukan NSFW, kirim pesan peringatan
            await ctx.send("Command ini hanya dapat digunakan di channel NSFW.")
            result = None 
        return result

    return wrapper

#def cooldown(rate, per, type=commands.BucketType.user):
    def decorator(func):
        bucket = commands.CooldownMapping.from_cooldown(rate, per, type)

        @functools.wraps(func)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            key = (func, ctx.command, ctx.author)  # Menggunakan ctx.command dan ctx.author sebagai kunci
            retry_after = bucket.update_rate_limit(key)

            if retry_after:
                await ctx.send(f"Command ini dapat digunakan lagi dalam {retry_after:.2f} detik.")
            else:
                await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator

#def FuncCooldown(cooldown_time: int):
    def decorator(func):
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            if asyncio.get_event_loop().time() - wrapper.last_used < cooldown_time:
                raise CooldownError(f"Command is on cooldown for {cooldown_time} seconds.")

            wrapper.last_used = asyncio.get_event_loop().time()
            await func(*args, **kwargs)

        wrapper.last_used = None
        return wrapper

    return decorator

#class CooldownError(Exception):
    pass

#def cooldown(rate, per, type=commands.BucketType.user):
    def decorator(func):
        @commands.cooldown(rate, per, type)
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator

def cooldown(seconds=10):
    def decorator(func):
        last_used = {}

        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            author_id = ctx.author.id
            current_time = time.time()

            if author_id not in last_used or (current_time - last_used[author_id]) >= seconds:
                # Jika perintah tidak dalam cooldown atau telah melewati cooldown
                last_used[author_id] = current_time
                return await func(self, ctx, *args, **kwargs)
            else:
                # Jika perintah dalam cooldown
                remaining_time = seconds - (current_time - last_used[author_id])
                embed = discord.Embed(color=discord.Color.random())
                embed.add_field(name="Sabar tunggu dalam", value=f"{int(remaining_time)} detik", inline=False)
                await ctx.send(embed=embed)
                return None

        return wrapper

    return decorator

def embed_message(embed_title):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # Tangkap pesan yang akan dikirim melalui ctx.send
            message = args[0] if args else kwargs.get('content', None)

            # Ubah pesan menjadi objek discord.Embed
            embed = discord.Embed(title=embed_title, description=message, color=discord.Color.blue())
            
            # Mengirim embed
            await ctx.send(embed=embed)

        return wrapper
    return decorator
