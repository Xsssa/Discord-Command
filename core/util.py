import asyncio
import calendar
from collections import Counter
import datetime
import functools
import logging
import time
from typing import Any
import discord
from discord.ext import commands, tasks
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


def throttle(rate: int, per: str = "user"): #ussage @throttle(rate=3, per="user")
    """
    Decorator that throttles command execution based on rate and timeframe.

    Args:
        rate (int): Maximum number of executions allowed within the timeframe.
        per (str, optional): Unit for throttling (default: "user"). Options: "user", "role", "channel", "guild".
    """

    def decorator(func):
        cooldown = {}

        async def wrapper(self, ctx, *args, **kwargs):
            current = time.time()
            limiter_key = (ctx.author.id if per == "user" else
                           (ctx.author.roles[0].id if per == "role" else str(ctx.channel.id) if per == "channel" else str(ctx.guild.id)))

            if limiter_key in cooldown:
                remaining = cooldown[limiter_key] - current
                if remaining > 0:
                    await ctx.send(f"Silahkan tunggu {remaining:.2f} detik untuk menggunakan command ini lagi.")
                    return
            cooldown[limiter_key] = current + (1 / rate)
            await asyncio.sleep(1 / rate)  # Ensure minimum delay even if cooldown is not met
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def log_usage(logger_name: str = "discord_bot"):
    """
    Decorator that logs command usage information.

    Args:
        logger_name (str, optional): Name of the logger to use (default: "discord_bot").
    """

    def decorator(func):
        logger = logging.getLogger(logger_name)

        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            logger.info(f"{ctx.author} ({ctx.author.id}) used command '{ctx.command.qualified_name}' in channel #{ctx.channel.name} ({ctx.channel.id})")
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def has_roles(*roles): #usage @has_roles("Admin", "Moderator")
    """
    Decorator that checks if the user has any of the specified roles.

    Args:
        *roles (str): Names of the required roles (can be multiple).
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            author_roles = [role.name for role in ctx.author.roles]
            if not any(role in author_roles for role in roles):
                await ctx.send(f"Maaf, Anda tidak memiliki permission untuk menggunakan command ini. Role yang dibutuhkan: {', '.join(roles)}")
                return
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def alias(*aliases): #ussage @alias("pingpong")
    """
    Decorator that creates aliases for a command.

    Args:
        *aliases (str): Aliases for the command (can be multiple).
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            return await func(self, ctx, *args, **kwargs)

        wrapper.__aliases__ = aliases
        return wrapper

    return decorator


def cooldown_with_reset(rate: int, per: str = "user", reset_after: int = 60): #ussage @cooldown_with_reset(rate=2, per="user", reset_after=30)  # Allow 2 commands per user every second, reset after 30 seconds
  """
  Decorator that throttles command execution with a reset timer.

  Args:
      rate (int): Maximum number of executions allowed within the timeframe.
      per (str, optional): Unit for throttling (default: "user"). Options: "user", "role", "channel", "guild".
      reset_after (int, optional): Time (in seconds) after which the cooldown resets (default: 60).
  """
  def decorator(func):
    cooldown = {}
    last_reset = {}

    async def wrapper(self, ctx, *args, **kwargs):
      current = time.time()
      limiter_key = (ctx.author.id if per == "user" else
                     (ctx.author.roles[0].id if per == "role" else str(ctx.channel.id) if per == "channel" else str(ctx.guild.id)))

      if limiter_key in cooldown and current - last_reset.get(limiter_key, 0) < reset_after:
        remaining = cooldown[limiter_key] - current + last_reset[limiter_key]
        if remaining > 0:
          await ctx.send(f"Silahkan tunggu {remaining:.2f} detik untuk menggunakan command ini lagi.")
          return
      cooldown[limiter_key] = current
      last_reset[limiter_key] = current
      await asyncio.sleep(1 / rate)  # Ensure minimum delay even if cooldown is not met
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  return decorator



async def handle_errors(func): #ussage @handle_errors
    """
    Decorator that catches and handles errors from a command.

    Args:
        func: The command function to wrap.
    """

    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            logging.exception(f"Error in command '{ctx.command.qualified_name}': {e}")
            await ctx.send(f"An error occurred while processing your command. Please try again later.")

    return wrapper



def validate_args(**validations):
  """
  Decorator that validates command arguments.

  Args:
      **validations (dict): Dictionary where keys are argument names and values are functions that take the argument value and return True if valid, False otherwise.
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      invalid_args = []
      for arg_name, validation in validations.items():
        if arg_name not in kwargs:
          invalid_args.append(arg_name)
          continue
        if not validation(kwargs[arg_name]):
          invalid_args.append(arg_name)
      if invalid_args:
        await ctx.send(f"Invalid arguments: {', '.join(invalid_args)}.")
        return
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  return decorator


#exsample of validate_args dectator 
def is_positive_int(value):
  """
  Helper function to check if a value is a positive integer.
  """
  try:
    return int(value) > 0
  except ValueError:
    return False

#@bot.command()
#@validate_args(number=is_positive_int)
#async def repeat(ctx, number: int):
#  """
#  Repeats a message a specified number of times.
#  """
#  for _ in range(number):
#    await ctx.send(ctx.message.content)
#===========================================================================


async def paginate(ctx, pages):
  """
  Decorator that paginates long text outputs into embeds.

  Args:
      ctx (discord.ext.commands.Context): Command context.
      pages (list): List of strings or embeds to paginate.
  """
  page = 1
  message = await ctx.send(embed=pages[0])
  await message.add_reaction("⬅️")
  await message.add_reaction("➡️")

  def check(reaction, user):
    return user == ctx.author and str(reaction.emoji) in ("⬅️", "➡️")

  while True:
    reaction, user = await ctx.bot.wait_for("reaction_add", check=check)
    if str(reaction.emoji) == "⬅️" and page > 1:
      page -= 1
    elif str(reaction.emoji) == "➡️" and page < len(pages):
      page += 1
    await message.edit(embed=pages[page-1])
    await reaction.remove(user)


def has_permissions(*perms):
  """
  Decorator that checks if the user has all of the specified permissions.

  Args:
      *perms (discord.Permissions): Permissions to check (can be multiple).
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      author_perms = ctx.channel.permissions_for(ctx.author)
      if not all(perm in author_perms for perm in perms):
        missing_perms = [perm.name for perm in perms if perm not in author_perms]
        await ctx.send(f"Maaf, Anda tidak memiliki permission: {', '.join(missing_perms)}")
        return
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  return decorator

# Example permissions
send_messages = discord.Permissions.send_messages
manage_messages = discord.Permissions.manage_messages
#ussage @has_permissions(send_messages, manage_messages)

#=========================================================================================================


def track_usage(stats_dict=None):
  """
  Decorator that tracks command usage statistics.

  Args:
      stats_dict (collections.Counter, optional): Dictionary to store usage counts (default: None).
  """
  if stats_dict is None:
    stats_dict = Counter()

  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      stats_dict[ctx.command.qualified_name] += 1
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  return decorator

# Example usage with a global stats dictionary
stats = Counter()

#@bot.command()
#@track_usage(stats)
#async def my_command(ctx):
  # ...

#=========================================================================================================    


class CooldownManager:
  """
  Class to manage cooldowns with context.
  """
  def __init__(self, cooldown_time):
    self.cooldowns = {}
    self.cooldown_time = cooldown_time

  def is_on_cooldown(self, ctx, key):
    """
    Checks if a specific context (key) is on cooldown.
    """
    cooldown_key = (ctx.author.id, key)
    if cooldown_key in self.cooldowns:
      if time.time() - self.cooldowns[cooldown_key] < self.cooldown_time:
        return True
    return False

  def set_cooldown(self, ctx, key):
    """
    Sets the cooldown for a specific context.
    """
    cooldown_key = (ctx.author.id, key)
    self.cooldowns[cooldown_key] = time.time()

cooldown_manager = CooldownManager(60)  # 60 seconds cooldown

def cooldown_with_context(cooldown_time=None): #usage @cooldown_with_context()
  """
  Decorator that implements cooldown with context.

  Args:
      cooldown_time (int, optional): Cooldown time in seconds (default: None, inherits from CooldownManager).
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      # Use channel name as context key by default, customize as needed
      context_key = ctx.channel.name
      if cooldown_manager.is_on_cooldown(ctx, context_key):
        remaining = cooldown_manager.cooldown_time - (time.time() - cooldown_manager.cooldowns[(ctx.author.id, context_key)])
        await ctx.send(f"Silahkan tunggu {remaining:.2f} detik untuk menggunakan command ini lagi di channel ini.")
        return
      cooldown_manager.set_cooldown(ctx, context_key)
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  if cooldown_time is not None:
    decorator.cooldown_time = cooldown_time
  return decorator

#========================================================================================================= 

def command_category(category):
  """
  Decorator that assigns a category to a command.

  Args:
      category (str): The category name.
  """
  def decorator(func):
    func.category = category
    return func

  return decorator
#usage
'''
@bot.command()
@command_category("Fun")
async def funny_command(ctx):
    # ...

@bot.command()
@command_category("Utility")
async def utility_command(ctx):
    # ...
'''

#========================================================================================================= 

def has_precondition(precondition):
  """
  Decorator to enforce a precondition before a command can be executed.

  Args:
      precondition (callable): Function that returns True if the precondition is met, False otherwise.
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      if not precondition(ctx):
        await ctx.send("Precondition failed: You cannot use this command right now.")
        return
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  return decorator

#example ussage
def is_weekend():
  """
  Example precondition function (check if it's the weekend).
  """
  today = datetime.datetime.today()
  return today.weekday() in (calendar.SATURDAY, calendar.SUNDAY)
'''
    @bot.command()
    @has_precondition(is_weekend)
    async def weekend_command(ctx):
    # This command can only be used on weekends
    # ...
'''

#========================================================================================

# Define the handle_errors_with_context decorator
def handle_errors_with_context(default_message="An error occurred."):
    """
    Decorator to handle errors with context-specific messages.

    Args:
        default_message (str, optional): Default error message (default: "An error occurred.").
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            try:
                return await func(self, ctx, *args, **kwargs)
            except Exception as e:
                logging.exception(f"Error in command '{ctx.command.qualified_name}': {e}")
                error_message = getattr(e, "error_message", default_message)  # Look for custom error message attribute
                await ctx.send(f"Error: {error_message}")

        return wrapper

    return decorator

#example ussage
# Define a custom exception class
class MyCustomError(Exception):
    def __init__(self, message):
        self.error_message = message

# Define a command using the decorator
"""
    @bot.command()
    @handle_errors_with_context()
    async def my_command(ctx):
        # Code that might raise exceptions
        if some_condition:
            raise MyCustomError("This is a specific error message.")
        # ...
"""
#========================================================================================

def type_check(func):
  """
  Decorator for type checking command arguments (optional).

  Args:
      func: The command function to wrap.
  """
  @functools.wraps(func)
  async def wrapper(self, ctx: commands.Context, *args, **kwargs):
    # Type hints for clarity (even without type checking)
    arg1: str
    arg2: int
    result = func(self, ctx, arg1, arg2)  # Assuming func takes two arguments
    return result

  # Optional type checking (requires external libraries like `mypy`)
  wrapper.__annotations__ = {
      'return': func.__annotations__.get('return', None),  # Preserve return type
  }
  return wrapper

# usaage
'''
    @bot.command()
    @type_check
    async def my_command(ctx: commands.Context, arg1: str, arg2: int) -> str:
    """
    Example command with type hints.

    Args:
        ctx (commands.Context): Discord command context.
        arg1 (str): First argument (string).
        arg2 (int): Second argument (integer).

    Returns:
        str: A string result (example).
    """
    # Function logic here
    return f"You provided: {arg1} and {arg2}"
    
'''
#=======================================================================================

def cooldown_with_backoff(cooldown_time: int = 30, max_cooldown: int = 300): #ussage @cooldown_with_backoff()
    """
    Decorator dengan pengendalian cooldown eksponensial.

    Args:
        cooldown_time (int, opsional): Waktu cooldown awal (default: 30 detik).
        max_cooldown (int, opsional): Waktu cooldown maksimum (default: 300 detik).
    """
    def decorator(func):
        cooldowns = {}

        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            current = time.time()
            author_id = ctx.author.id
            if author_id in cooldowns:
                elapsed = current - cooldowns[author_id]
                remaining = cooldown_time * 2**min(cooldowns[author_id] != 0, 3)  # Pengendalian kembali eksponensial
                remaining = min(remaining, max_cooldown)  # Batasi cooldown maksimum
                if elapsed < remaining:
                    await ctx.send(f"Silahkan tunggu {remaining:.2f} detik untuk menggunakan perintah ini lagi.")
                    return
                cooldowns[author_id] = current
            else:
                cooldowns[author_id] = current
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator

#=======================================================================================

def command_help(help_text: str = None, use_embed: bool = True):
    """
    Decorator untuk menghasilkan pesan bantuan untuk perintah.

    Args:
        help_text (str, opsional): Teks bantuan default (default: None).
        use_embed (bool, opsional): Menentukan apakah menggunakan embed atau tidak (default: True).
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if "help" in ctx.message.content.lower():  # Jika subcommand "help" dipanggil, tampilkan pesan bantuan
                if help_text:
                    if use_embed:
                        embed = discord.Embed(title=f"Bantuan untuk perintah '{ctx.command.qualified_name}'", description=help_text, color=discord.Color.blue())
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"Bantuan untuk perintah '{ctx.command.qualified_name}':\n{help_text}")
                else:
                    await ctx.send(f"Tidak ada bantuan yang tersedia untuk perintah '{ctx.command.qualified_name}'.")
                return
            else:  # Jika tidak ada subcommand atau subcommand tidak dienksukusi, jalankan perintah asli
                return await func(self, ctx, *args, **kwargs)

        wrapper.__help__ = help_text or func.__doc__  # Menyimpan teks bantuan untuk bot.get_command
        return wrapper

    return decorator


def track_usage(logger=None): #ussage @track_usage()
    """
    Dekorator untuk melacak penggunaan perintah dan mencatatnya ke logger.

    Args:
        logger (logging.Logger, opsional): Logger yang digunakan untuk pencatatan (default: None, membuat logger baru).
    """
    if logger is None:
        logger = logging.basicConfig(filename='command_usage.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Mendapatkan tanggal dan waktu saat ini
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Mencatat informasi penggunaan perintah ke dalam logger
            logger.info(f"[{current_time}] Perintah '{ctx.command.qualified_name}' digunakan oleh {ctx.author.name} ({ctx.author.id}) di guild {ctx.guild.name} ({ctx.guild.id})")
            # Memanggil fungsi perintah asli
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator

def track_slow_commands(threshold=10):  # Ambang batas waktu eksekusi dalam detik, ussage @track_slow_commands() 
  """
  Dekorator untuk melacak perintah yang lambat dan mencatatnya.

  Args:
      threshold (int, optional): Batas waktu minimum untuk dianggap lambat (default: 10 detik).
  """
  slow_commands = {}


  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      start_time = time.time()
      result = await func(self, ctx, *args, **kwargs)
      elapsed_time = time.time() - start_time
      if elapsed_time > threshold:
        slow_commands[ctx.command.qualified_name] = elapsed_time
        logging.warning(f"Perintah '{ctx.command.qualified_name}' lambat: {elapsed_time:.2f} detik")
      return result

    return wrapper

  return decorator

def with_temp_permissions(*perms, duration=60): #ussage @with_temp_permissions(discord.Permissions.kick_members, duration=30)
  """
  Dekorator untuk memberikan hak akses sementara kepada pengguna.

  Args:
      *perms (discord.Permissions): Izin sementara yang diberikan (dapat berupa beberapa izin).
      duration (int, optional): Durasi izin sementara dalam detik (default: 60).
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      author = ctx.author
      guild = ctx.guild
      # Simpan izin pengguna saat ini
      stored_perms = author.guild_permissions
      # Tambahkan izin sementara
      await author.edit(guild=guild, add_perms=perms)
      try:
        await func(self, ctx, *args, **kwargs)
      finally:
        # Batalkan izin sementara setelah durasi tertentu
        await asyncio.sleep(duration)
        await author.edit(guild=guild, permissions=stored_perms)

    return wrapper

  return decorator


def validate_arguments(**validations):
  """
  Dekorator untuk memvalidasi argumen perintah.

  Args:
      **validations (dict): Pemetaan antara nama argumen dan fungsi validasi yang sesuai.
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      for arg_name, validation in validations.items():
        if arg_name not in kwargs:
          await ctx.send(f"Argumen '{arg_name}' tidak ditemukan.")
          return
        if not validation(kwargs[arg_name]):
          await ctx.send(f"Argumen '{arg_name}' tidak valid.")
          return
      return await func(self, ctx, *args, **kwargs)
    
    
    return wrapper

  return decorator


def retry_on_error(retries: int = 3, delay: int = 5): #ussafe @retry_on_error()
  """
  Decorator to retry commands on error.

  Args:
      retries (int, optional): Number of retry attempts (default: 3).
      delay (int, optional): Delay between retries in seconds (default: 5).
  """
  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      for attempt in range(retries + 1):
        try:
          return await func(self, ctx, *args, **kwargs)
        except Exception as e:
          logging.warning(f"Error in command '{ctx.command.qualified_name}': {e}, attempt {attempt}/{retries}")
          if attempt < retries:
            await asyncio.sleep(delay)
          else:
            await ctx.send("An error occurred while processing your command. Please try again later.")
            raise

    return wrapper

  return decorator


def throttle(rate_limit: int, per: int, bucket_name_factory=lambda ctx: ctx.author.id): #ussage @throttle(rate_limit=5, per=60, bucket_name_factory=lambda ctx: ctx.author.roles[0])  # Throttle based on first role
  """
  Decorator with dynamic rate limiting.

  Args:
      rate_limit (int): Maximum allowed executions within the period.
      per (int): Time period in seconds.
      bucket_name_factory (callable, optional): Function to calculate bucket name (default: user ID).
  """
  rates = {}

  def decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
      bucket_name = bucket_name_factory(ctx)
      if bucket_name not in rates:
        rates[bucket_name] = {"remaining": rate_limit, "last_used": time.time()}
      now = time.time()
      last_used = rates[bucket_name]["last_used"]
      if now - last_used < per:
        remaining = rates[bucket_name]["remaining"] - 1
        if remaining <= 0:
          await ctx.send(f"Silahkan tunggu {per - int(now - last_used):.2f} detik lagi untuk menggunakan perintah ini.")
          return
        rates[bucket_name]["remaining"] = remaining
      else:
        rates[bucket_name]["remaining"] = rate_limit
      rates[bucket_name]["last_used"] = now
      return await func(self, ctx, *args, **kwargs)

    return wrapper

  @tasks.loop(seconds=per)
  async def reset_rates():
    for key, data in rates.items():
      data["remaining"] = rate_limit
    await reset_rates.start()
    return reset_rates

  return decorator

