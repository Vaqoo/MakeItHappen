import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import settings


class MakeItHappenBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        extensions = (
            "cogs.moderation",
            "cogs.utility",
            "cogs.fun",
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

    async def on_ready(self) -> None:
        if self.user:
            logging.info("Logged in as %s (%s)", self.user, self.user.id)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        logging.exception("Prefix command error", exc_info=error)

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        logging.error("Slash command error: %s", error)
        message = "❌ Bei der Ausführung des Befehls ist ein Fehler aufgetreten."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

bot = MakeItHappenBot()

if __name__ == "__main__":
    bot.run(settings.token)
