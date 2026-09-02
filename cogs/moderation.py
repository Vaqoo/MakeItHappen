from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    async def _can_moderate(interaction: discord.Interaction, member: discord.Member) -> bool:
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member):
            return False
        if member == guild.owner or member == user:
            return False
        if member.top_role >= user.top_role:
            return False
        bot_member = guild.me
        return bot_member is not None and member.top_role < bot_member.top_role

    @app_commands.command(name="kick", description="Kickt ein Mitglied vom Server.")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(member="Das Mitglied", reason="Grund für den Kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            await interaction.response.send_message("❌ Dieses Mitglied kann nicht gekickt werden (Rollenhierarchie).", ephemeral=True)
            return
        await member.kick(reason=f"{reason} | von {interaction.user}")
        await interaction.response.send_message(f"👢 **{member}** wurde gekickt. Grund: `{reason}`", ephemeral=True)

    @app_commands.command(name="ban", description="Bannt ein Mitglied vom Server.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(member="Das Mitglied", reason="Grund für den Ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            await interaction.response.send_message("❌ Dieses Mitglied kann nicht gebannt werden (Rollenhierarchie).", ephemeral=True)
            return
        await member.ban(reason=f"{reason} | von {interaction.user}")
        await interaction.response.send_message(f"🔨 **{member}** wurde gebannt. Grund: `{reason}`", ephemeral=True)

    @app_commands.command(name="timeout", description="Gibt einem Mitglied einen Timeout.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Das Mitglied", minutes="Timeout-Dauer in Minuten", reason="Grund")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: app_commands.Range[int, 1, 40320], reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            await interaction.response.send_message("❌ Dieses Mitglied kann nicht moderiert werden (Rollenhierarchie).", ephemeral=True)
            return
        await member.timeout(timedelta(minutes=minutes), reason=f"{reason} | von {interaction.user}")
        await interaction.response.send_message(f"⏳ **{member}** hat {minutes} Minuten Timeout bekommen.", ephemeral=True)

    @app_commands.command(name="purge", description="Löscht mehrere Nachrichten aus dem aktuellen Kanal.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Anzahl der zu löschenden Nachrichten")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Dieser Befehl funktioniert nur in Textkanälen.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 **{len(deleted)}** Nachrichten gelöscht.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
