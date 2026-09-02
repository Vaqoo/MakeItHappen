import random

import discord
from discord import app_commands
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="8ball", description="Stelle der magischen 8-Ball eine Frage.")
    @app_commands.describe(question="Deine Frage")
    async def eight_ball(self, interaction: discord.Interaction, question: str) -> None:
        answers = (
            "Ja, safe. 🗿",
            "Nein. ❌",
            "Sieht gut aus. 👀",
            "Eher nicht. 💀",
            "Definitiv. 🔥",
            "Frag später nochmal. 🕐",
            "Das Universum sagt: vielleicht. 🌌",
            "Bro, ich hab keine Ahnung. 😭",
        )
        await interaction.response.send_message(f"🎱 **Frage:** {question}\n**Antwort:** {random.choice(answers)}")

    @app_commands.command(name="coinflip", description="Wirft eine Münze.")
    async def coinflip(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🪙 **{random.choice(('Kopf', 'Zahl'))}!**")

    @app_commands.command(name="roll", description="Würfelt eine Zahl.")
    @app_commands.describe(sides="Anzahl der Würfelseiten")
    async def roll(self, interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6) -> None:
        await interaction.response.send_message(f"🎲 Du hast eine **{random.randint(1, sides)}** gewürfelt. (1–{sides})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
