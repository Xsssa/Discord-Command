import discord


from discord.ext.commands import Bot
from discord.ext import commands

bot = Bot(
    command_prefix=commands.when_mentioned_or(config["prefix"]),
    intents=discord.Intents.all(),
    help_command=None,
)


@bot.event
async def on_guild_join(guild):
    owner = await bot.fetch_user(USER_ID) # Change to your owner's ID
    embed = discord.Embed(
        title="SAYA DITAMBAHKAN KE SERVER BARU !",
        color=discord.Color.green()
    )
    if guild.icon is not None:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Server owner:", value=f"{guild.owner.name}#{guild.owner.discriminator}", inline=False)
    embed.set_footer(text=f"Currently in {len(bot.guilds)} servers")
    await owner.send(embed=embed)


@bot.event
async def on_guild_remove(guild, reason: str = "Not specified") -> None:
    owner = await bot.fetch_user(USER_ID)  # Change to your owner's ID
    embed = discord.Embed(
        title="SAYA DIKELUARKAN DARI SERVER!",
        color=discord.Color.red()
    )
    if guild.icon is not None:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Server owner:", value=f"{guild.owner.name}#{guild.owner.discriminator}", inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    embed.set_footer(text=f"Currently in {len(bot.guilds)} servers")
    await owner.send(embed=embed)

@bot.event
async def on_guild_ban(guild, user):
    owner = await bot.fetch_user(USER_ID)  # Change to your owner's ID
    embed = discord.Embed(
        title="SAYA DILARANG (BANNED) DARI SERVER!",
        color=discord.Color.red()
    )
    if guild.icon is not None:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Server owner:", value=f"{guild.owner.name}#{guild.owner.discriminator}", inline=False)
    embed.add_field(name="Banned user:", value=f"{user.name}#{user.discriminator}", inline=False)
    embed.set_footer(text=f"Currently in {len(bot.guilds)} servers")
    await owner.send(embed=embed)
