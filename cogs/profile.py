import discord
from discord import app_commands
from discord.ext import commands

from database import get_achievements, get_stats, set_profile


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="Zeigt dein persönliches MakeItHappen-Profil.")
    @app_commands.describe(member="Optional: Profil eines anderen Mitglieds")
    async def profile(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        member = member or interaction.user
        stats = get_stats(interaction.guild.id, member.id)
        profile = get_profile(interaction.guild.id, member.id)
        achievements = get_achievements(interaction.guild.id, member.id)
        level = int(stats["xp"]) // 100 + 1
        embed = discord.Embed(title=f"✨ {profile['display_name'] or member.display_name}'s MIH Profile", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        if profile["bio"]:
            embed.description = profile["bio"]
        embed.add_field(name="⭐ Level", value=f"{level} • {stats['xp']} XP")
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} Tage")
        embed.add_field(name="🏆 Achievements", value=str(len(achievements)))
        if profile["favorite_quote"]:
            embed.add_field(name="💭 Favorite Quote", value=f"_{profile['favorite_quote']}_", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile_edit", description="Passe dein MakeItHappen-Profil an.")
    @app_commands.describe(display_name="Name im MIH-Profil", bio="Kurze Bio", favorite_quote="Dein Lieblingsspruch")
    async def profile_edit(self, interaction: discord.Interaction, display_name: str | None = None, bio: str | None = None, favorite_quote: str | None = None) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if display_name is None and bio is None and favorite_quote is None:
            return await interaction.response.send_message("ℹ️ Gib mindestens eine Sache an, die du ändern möchtest.", ephemeral=True)
        set_profile(interaction.guild.id, interaction.user.id, display_name=display_name, bio=bio, favorite_quote=favorite_quote)
        await interaction.response.send_message("✨ **Dein MIH-Profil wurde aktualisiert.**", ephemeral=True)

    @app_commands.command(name="profile_reset", description="Setzt dein MIH-Profil auf die Standardwerte zurück.")
    async def profile_reset(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        set_profile(interaction.guild.id, interaction.user.id, display_name="", bio="", favorite_quote="")
        await interaction.response.send_message("♻️ **Dein MIH-Profil wurde zurückgesetzt.**", ephemeral=True)


from database import get_profile


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Profile(bot))
