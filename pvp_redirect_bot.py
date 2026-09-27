import os
import io
import aiohttp
import discord

# ============================================================
# CONFIG
# ============================================================

# Put the new bot's token in Railway as DISCORD_TOKEN.
TOKEN = os.getenv("DISCORD_TOKEN")

# Existing Dink Drops channel.
DROPS_CHANNEL_ID = 1540706808262430792

# Dedicated PvP channel.
PVP_CHANNEL_ID = 1553869180925644811

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

        # Copy the Dink embed. Dink's screenshot can be hosted as a
        # Discord attachment/proxy URL. Simply copying the embed URL can
        # result in Discord not rendering the image in the new message.
        # Download the image and re-upload it to the PvP channel instead.
        embeds = [e.copy() for e in message.embeds]
        files = []

        image_url = None

        # Prefer an actual Discord attachment if Dink supplied one.
        if message.attachments:
            attachment = message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                image_url = attachment.url

        # Otherwise use the image URL stored in the Dink embed.
        if image_url is None:
            for e in embeds:
                if e.image and e.image.url:
                    image_url = e.image.url
                    break

        if image_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    response.raise_for_status()
                    image_data = await response.read()

            # Keep the screenshot as an attachment so it is hosted by
            # Discord in the new PvP message and cannot depend on Dink's
            # original/expiring image URL.
            filename = "pvp_screenshot.png"
            files.append(
                discord.File(io.BytesIO(image_data), filename=filename)
            )

            for e in embeds:
                if e.image and e.image.url:
                    e.set_image(url=f"attachment://{filename}")

        await pvp_channel.send(
            content=message.content or None,
            embeds=embeds,
            files=files,
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
