import logging
import random

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import settings
from database import init_db

INSPIRATIONAL_QUOTES = (
    "Make it happen.", "Keep going. 🔥", "You got this. 💜", "Stay focused.", "Progress > perfection.",
    "Dream big. Work bigger.", "One step at a time.", "Discipline beats motivation.", "Never stop improving.",
    "Trust the process.", "Your time is now.", "Be better than yesterday.", "Small steps. Big results.",
    "Focus. Execute. Repeat.", "Turn ideas into action.", "Don't quit. Adapt.", "Stay hungry. Stay driven.",
    "Build your future.", "Consistency creates results.", "Believe. Begin. Become.", "Your pace is still progress.",
    "Start now. Adjust later.", "Hard days build strong people.", "Keep showing up.",
)


class MakeItHappenBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.messages = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.last_quote: str | None = None

    async def setup_hook(self) -> None:
        init_db()
        extensions = (
            "cogs.moderation", "cogs.utility", "cogs.fun", "cogs.motivation", "cogs.community",
            "cogs.voice", "cogs.logs", "cogs.admin", "cogs.profile", "cogs.economy", "cogs.server",
        )
        for extension in extensions:
            await self.load_extension(extension)
            logging.info("Loaded %s", extension)
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logging.info("Synced %d commands to development guild %s", len(synced), settings.guild_id)
        else:
            synced = await self.tree.sync()
            logging.info("Synced %d global commands", len(synced))
        self.rotate_presence.start()

    async def on_ready(self) -> None:
        if self.user:
            logging.info("Logged in as %s (%s)", self.user, self.user.id)

    @tasks.loop(minutes=3)
    async def rotate_presence(self) -> None:
        quotes = [quote for quote in INSPIRATIONAL_QUOTES if quote != self.last_quote]
        quote = random.choice(quotes)
        self.last_quote = quote
        await self.change_presence(status=discord.Status.online, activity=discord.Game(name=quote))
        logging.info("Presence changed to: %s", quote)

    @rotate_presence.before_loop
    async def before_rotate_presence(self) -> None:
        await self.wait_until_ready()

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        logging.exception("Prefix command error", exc_info=error)

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        logging.error("Slash command error: %s", error)
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ Dafür fehlen dir die nötigen Berechtigungen."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = "⏳ Dieser Befehl ist gerade im Cooldown."
        else:
            message = "❌ Bei der Ausführung des Befehls ist ein Fehler aufgetreten."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
bot = MakeItHappenBot()

if __name__ == "__main__":
    bot.run(settings.token)
