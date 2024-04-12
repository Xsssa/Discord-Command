import random
import aiohttp
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from _test.cokies import get_cookies
from _test.video_src import get_video_src
from core.util import *


class rule34(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name='rule34', nsfw=True, invoke_without_command=True)
    @processing_message
    @nsfw_check
    async def rule34(self, ctx, *tags):
        try:
            # Periksa apakah tag telah diberikan
            if not tags:
                await ctx.send('Harap berikan tag untuk mencari gambar acak.')
                return

            # Gabungkan semua tag menjadi satu string dengan tanda '+' sebagai pemisah
            tag_string = '+'.join(tags)
            total_pages = await self.get_total_pages(tag_string)

            # Tentukan URL pencarian dengan tag yang diberikan dan halaman yang diacak
            random_page = random.randint(1, total_pages)
            search_url = f'https://rule34.xxx/index.php?page=post&s=list&tags={tag_string}&pid={random_page}'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            cookies = await get_cookies(ctx)
            if cookies is None:
                return

            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        # Parse konten HTML
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        # Temukan semua elemen gambar
                        image_elements = soup.find_all('span', class_='thumb')
                        if image_elements:
                            # Pilih elemen gambar acak dari daftar
                            random_image_element = random.choice(image_elements)
                            image_page_url = random_image_element.find('a')['href']
                            
                            

                            # Dapatkan URL gambar dari halaman gambar individu
                            image_url = await self.get_individual_image_url(f'https://rule34.xxx{image_page_url}')
                            video_url = await get_video_src(f'https://rule34.xxx{image_page_url}')

                            if image_url:
                                # Buat sebuah embed untuk menampilkan gambar yang dipilih
                                embed = discord.Embed(title=f"Random Image from rule34.xxx.\nTags: `{' '.join(tags)}`",
                                                      description=f"Page link klik [sini]({search_url})", timestamp=time, color=discord.Color.random())
                                embed.set_image(url=image_url)
                                
                                # Kirim embed ke channel Discord
                                await ctx.send(embed=embed)
                                logger.info(f"{total_pages} {search_url}")
                                
                            elif video_url:
                                await ctx.send(f"page link:[Sini]({search_url})\n video [Download]({video_url})")
                                
                                
                            else:
                                await ctx.send('Gagal mengambil gambar. Silahkan coba lagi (1).')
                        else:
                            await ctx.send(f'Tidak ada gambar yang ditemukan dengan tag: `{tag_string}` silahkan priksa kembali')
                    else:
                        await ctx.send('Gagal mengambil gambar. Silahkan coba lagi (2)')
        except Exception as e:
            await ctx.send(f'Terjadi kesalahan: {str(e)}')

    async def get_individual_image_url(self, image_page_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_page_url, headers=self.headers) as response:
                if response.status == 200:
                    # Parse konten HTML dari halaman gambar individu
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    # Temukan elemen gambar
                    image_element = soup.find('img', id='image')
                    if image_element:
                        return image_element['src']
                return None

    async def get_total_pages(self, tag_string):
        try:
            search_url = f'https://rule34.xxx/index.php?page=post&s=list&tags={tag_string}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers= self.headers) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        pager_element = soup.find('div', id='paginator')
                        if pager_element:
                            # Cek apakah ada tanda ">>" yang mengarah ke halaman terakhir
                            last_page_link = pager_element.find('a', text='>>')
                            if last_page_link:
                                last_page_url = last_page_link['href']
                                # Ekstrak nomor halaman dari URL halaman terakhir
                                last_page_number = int(last_page_url.split('&pid=')[-1])
                                return last_page_number
        except Exception as e:
            logger.error(f'Error in get_total_pages: {str(e)}')
        return 1  # Kembalikan 1 jika terjadi kesalahan

#===========================================================================================================================================
    
    @rule34.command(name='random')
    async def rule_random(self, ctx):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://rule34.xxx/index.php?page=post&s=random') as response:
                    if response.status == 200:
                        # Parse the HTML content
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        # Find the image element
                        image_element = soup.find('img', id='image')
                        if image_element:
                            image_url = image_element['src']

                            # Create an embed to display the image
                            embed = discord.Embed(title='Random Image from rule34.xxx', color=discord.Color.random())
                            embed.set_image(url=image_url)
                            # Send the embed to the channel
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send('Failed to fetch an image (1).')
                    else:
                        await ctx.send('Failed to fetch an image (2).')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')