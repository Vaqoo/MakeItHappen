import discord
from discord import app_commands
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Zeigt die Bot-Latenz an.")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")

    @app_commands.command(name="serverinfo", description="Zeigt Informationen über den Server.")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Dieser Befehl funktioniert nur auf einem Server.", ephemeral=True)
            return

        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blurple())
        embed.add_field(name="👑 Besitzer", value=guild.owner.mention if guild.owner else "Unbekannt")
        embed.add_field(name="👥 Mitglieder", value=str(guild.member_count))
        embed.add_field(name="💬 Textkanäle", value=str(len(guild.text_channels)))
        embed.add_field(name="🔊 Sprachkanäle", value=str(len(guild.voice_channels)))
        embed.add_field(name="🎭 Rollen", value=str(len(guild.roles)))
        embed.add_field(name="🆔 Server-ID", value=str(guild.id), inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Zeigt Informationen über ein Mitglied.")
    @app_commands.describe(member="Das Mitglied")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        member = member or interaction.user
        embed = discord.Embed(title=f"👤 {member}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=str(member.id), inline=False)
        embed.add_field(name="📅 Account erstellt", value=discord.utils.format_dt(member.created_at, "D"), inline=False)
        if member.joined_at:
            embed.add_field(name="📥 Server beigetreten", value=discord.utils.format_dt(member.joined_at, "D"), inline=False)
        embed.add_field(name="🎭 Höchste Rolle", value=member.top_role.mention)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Zeigt den Avatar eines Mitglieds.")
    @app_commands.describe(member="Das Mitglied")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        member = member or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar von {member}", color=member.color)
        embed.set_image(url=member.display_avatar.replace(size=1024).url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Utility(bot))
