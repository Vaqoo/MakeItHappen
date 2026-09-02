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

    async def _log(self, guild: discord.Guild, title: str, description: str, color: discord.Color) -> None:
        self.bot.dispatch("mih_moderation_log", guild, title, description, color)

    @app_commands.command(name="kick", description="Kickt ein Mitglied vom Server.")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(member="Das Mitglied", reason="Grund für den Kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            return await interaction.response.send_message("❌ Dieses Mitglied kann nicht gekickt werden.", ephemeral=True)
        await member.kick(reason=f"{reason} | von {interaction.user}")
        await self._log(interaction.guild, "👢 Member Kicked", f"**User:** {member} (`{member.id}`)\n**Moderator:** {interaction.user.mention}\n**Grund:** {reason}", discord.Color.orange())
        await interaction.response.send_message(f"👢 **{member}** wurde gekickt.", ephemeral=True)

    @app_commands.command(name="ban", description="Bannt ein Mitglied vom Server.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(member="Das Mitglied", reason="Grund für den Ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            return await interaction.response.send_message("❌ Dieses Mitglied kann nicht gebannt werden.", ephemeral=True)
        await member.ban(reason=f"{reason} | von {interaction.user}")
        await self._log(interaction.guild, "🔨 Member Banned", f"**User:** {member} (`{member.id}`)\n**Moderator:** {interaction.user.mention}\n**Grund:** {reason}", discord.Color.red())
        await interaction.response.send_message(f"🔨 **{member}** wurde gebannt.", ephemeral=True)

    @app_commands.command(name="unban", description="Entbannt einen User anhand seiner ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user_id="Discord User-ID", reason="Grund")
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Kein Grund angegeben") -> None:
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{reason} | von {interaction.user}")
        except (ValueError, discord.NotFound):
            return await interaction.response.send_message("❌ User-ID ungültig oder User nicht gebannt.", ephemeral=True)
        await self._log(interaction.guild, "🔓 Member Unbanned", f"**User:** {user} (`{user.id}`)\n**Moderator:** {interaction.user.mention}\n**Grund:** {reason}", discord.Color.green())
        await interaction.response.send_message(f"🔓 **{user}** wurde entbannt.", ephemeral=True)

    @app_commands.command(name="timeout", description="Gibt einem Mitglied einen Timeout.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Das Mitglied", minutes="Timeout-Dauer in Minuten", reason="Grund")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: app_commands.Range[int, 1, 40320], reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            return await interaction.response.send_message("❌ Dieses Mitglied kann nicht moderiert werden.", ephemeral=True)
        await member.timeout(timedelta(minutes=minutes), reason=f"{reason} | von {interaction.user}")
        await self._log(interaction.guild, "⏳ Member Timed Out", f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Dauer:** {minutes} Minuten\n**Grund:** {reason}", discord.Color.gold())
        await interaction.response.send_message(f"⏳ **{member}** hat {minutes} Minuten Timeout bekommen.", ephemeral=True)

    @app_commands.command(name="untimeout", description="Entfernt den Timeout eines Mitglieds.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Das Mitglied", reason="Grund")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben") -> None:
        if not await self._can_moderate(interaction, member):
            return await interaction.response.send_message("❌ Dieses Mitglied kann nicht moderiert werden.", ephemeral=True)
        await member.timeout(None, reason=f"{reason} | von {interaction.user}")
        await self._log(interaction.guild, "⏱️ Timeout Removed", f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Grund:** {reason}", discord.Color.green())
        await interaction.response.send_message(f"✅ Timeout von **{member}** entfernt.", ephemeral=True)

    @app_commands.command(name="purge", description="Löscht mehrere Nachrichten aus dem aktuellen Kanal.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Anzahl der zu löschenden Nachrichten")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Dieser Befehl funktioniert nur in Textkanälen.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await channel.purge(limit=amount)
        await self._log(interaction.guild, "🧹 Messages Purged", f"**Moderator:** {interaction.user.mention}\n**Channel:** {channel.mention}\n**Amount:** {len(deleted)}", discord.Color.orange())
        await interaction.followup.send(f"🧹 **{len(deleted)}** Nachrichten gelöscht.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
