import discord
from discord.ext import commands


class clear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="clear")
    async def clear(self, ctx, channel: discord.TextChannel = None, amount: int = None):
        """Clears messages in a specific text channel or the current channel.

        Args:
            channel (discord.TextChannel, optional): The text channel to clear messages from. Defaults to the current channel.
            amount (int, optional): The number of messages to delete. Defaults to None (clears all messages).
        """

        if not channel:
            channel = ctx.channel

        if not channel.permissions_for(ctx.me).manage_messages:
            await ctx.send("I don't have permission to manage messages in this channel.")
            return

        if amount is None:
            await ctx.send(f"Are you sure you want to clear all messages in {channel.name}? (y/n)")
            response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            await ctx.send("cuz limit of discord API, this is take a mint (maybe hour) depending on how many messages")
            if response.content.lower() != 'y':
                await ctx.send("Clear operation cancelled.")
                return

        try:
            deleted = await channel.purge(limit=amount or 100, before=ctx.message)
            await ctx.send(f"Deleted {len(deleted)} messages from {channel.name}.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to clear messages: {e}")