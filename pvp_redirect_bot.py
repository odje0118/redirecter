import os
import discord

# ============================================================
# CONFIG
# ============================================================

# Put the new bot's token in Railway as DISCORD_TOKEN.
TOKEN = os.getenv("DISCORD_TOKEN")

# Existing Dink Drops channel.
DROPS_CHANNEL_ID = 1540706808262430792

# Dedicated PvP channel.
PVP_CHANNEL_ID = 1553587563380347053

# Dink's PvP notification uses this embed title.
PLAYER_KILL_TITLE = "Player Kill"


# ============================================================
# DISCORD SETUP
# ============================================================

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Watching Drops channel: {DROPS_CHANNEL_ID}")
    print(f"Forwarding Player Kill messages to: {PVP_CHANNEL_ID}")


@bot.event
async def on_message(message: discord.Message):
    # Never process our own messages.
    if message.author == bot.user:
        return

    # Only watch the Dink Drops channel.
    if message.channel.id != DROPS_CHANNEL_ID:
        return

    # A Dink Player Kill is identified by the embed title.
    if not message.embeds:
        return

    player_kill_embed = None

    for embed in message.embeds:
        if (embed.title or "").strip().lower() == PLAYER_KILL_TITLE.lower():
            player_kill_embed = embed
            break

    if player_kill_embed is None:
        return

    try:
        pvp_channel = bot.get_channel(PVP_CHANNEL_ID)

        if pvp_channel is None:
            pvp_channel = await bot.fetch_channel(PVP_CHANNEL_ID)

        # Copy the original Dink embed.
        # This preserves the Player Kill title, text, world/location,
        # screenshot/image and footer supplied by Dink.
        embeds = [embed.copy() for embed in message.embeds]

        # Copy any normal message content too, although Dink normally
        # puts the Player Kill information inside the embed.
        await pvp_channel.send(
            content=message.content or None,
            embeds=embeds,
        )

        print(
            f"Redirected Player Kill message {message.id} "
            f"from #{message.channel.name} to PvP channel."
        )

        # Only delete the original after the PvP copy succeeded.
        try:
            await message.delete()
            print(f"Deleted original Player Kill message {message.id}.")
        except discord.Forbidden:
            print(
                f"WARNING: Redirect succeeded, but message {message.id} "
                f"could not be deleted. Give this bot 'Manage Messages' "
                f"in the Drops channel."
            )
        except discord.HTTPException as exc:
            print(
                f"WARNING: Redirect succeeded, but deleting "
                f"message {message.id} failed: {exc}"
            )

    except discord.Forbidden:
        print(
            f"ERROR: Could not post Player Kill message {message.id}. "
            f"Give this bot 'View Channel', 'Send Messages' and "
            f"'Embed Links' in the PvP channel."
        )
    except discord.HTTPException as exc:
        print(
            f"ERROR: Discord rejected the Player Kill redirect "
            f"for message {message.id}: {exc}"
        )
    except Exception as exc:
        print(
            f"ERROR: Unexpected Player Kill redirect error "
            f"for message {message.id}: {exc}"
        )


# ============================================================
# START
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. Add your new bot token as the "
        "DISCORD_TOKEN environment variable in Railway."
    )

bot.run(TOKEN)
