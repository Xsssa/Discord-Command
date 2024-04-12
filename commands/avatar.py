import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional
from discord import User, Member





class avatar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.hybrid_command(
        name="avatar",
        description="Menampilkan avatar pengguna atau pengguna yang ditentukan"
        )
    async def avatar(self, ctx: Context, member: Optional[Member] = None, format: Optional[str] = None) -> None:
        if member is None:
            member = ctx.author

        valid_formats = ["jpg", "jpeg", "png", "webp"]
        if format is not None and format.lower() not in valid_formats:
            await ctx.send(f"Format yang dimasukkan tidak valid. Format yang tersedia: {', '.join(valid_formats)}")
            return

        avatar_url = member.avatar.with_format(format) if format else member.avatar.url

        embed = discord.Embed(title=f"Avatar dari {member.display_name}")
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    
        if format:
            await ctx.send(f"Klik link ini untuk membuka gambar avatar {member.display_name} [SINI]({avatar_url})")
        else:
            await ctx.send(embed=embed)