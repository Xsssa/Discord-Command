import os
import discord
import datetime
import platform

from discord.ext import commands






class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.start_time = datetime.datetime.utcnow() 
        self.bot = bot
    @commands.command()
    async def info(self, ctx):
        server_count = len(self.bot.guilds)
        uptime = datetime.datetime.utcnow() - self.start_time  # Assuming you have defined self.bot.start_time
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m {uptime.seconds % 60}s"
        ping = round(self.bot.latency * 1000, 2)

        info_embed = discord.Embed(title="Bot Info", color=discord.Color.random())

        info_embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        info_embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
        info_embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        info_embed.add_field(name="\u200b", value="\u200b", inline=False)
        info_embed.add_field(name="Uptime", value=uptime_str, inline=True)
        info_embed.add_field(name="Ping", value=f"{ping} ms", inline=True)
        info_embed.add_field(name="Server Count", value=str(server_count), inline=True)
        info_embed.add_field(name="\u200b", value="\u200b", inline=False)
        info_embed.add_field(name="Operating System", value=f"{platform.system()} {platform.release()} ({os.name})", inline=True)
        guild_info = f"Guild ID - {ctx.guild.name}: {ctx.guild.id}"
        info_embed.add_field(name="Guild ID", value=guild_info, inline=True)

        avatar_url = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url
        info_embed.set_thumbnail(url=avatar_url)

        info_embed.set_footer(text=f"Request dari {ctx.author.name}")

        await ctx.send(embed=info_embed)