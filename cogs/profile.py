import discord
from discord import app_commands
from discord.ext import commands

from database import get_achievements, get_economy, get_profile, get_rank, get_stats, get_wins, set_profile


DEV_USER_ID = 1283785169664213101
PROFILE_COLORS = {
    "purple": (155, 89, 182), "blue": (52, 152, 219), "red": (231, 76, 60), "green": (46, 204, 113),
    "orange": (230, 126, 34), "pink": (233, 30, 99), "yellow": (241, 196, 15), "cyan": (26, 188, 156),
}
COLOR_CHOICES = [
    app_commands.Choice(name="🟣 Lila", value="purple"), app_commands.Choice(name="🔵 Blau", value="blue"),
    app_commands.Choice(name="🔴 Rot", value="red"), app_commands.Choice(name="🟢 Grün", value="green"),
    app_commands.Choice(name="🟠 Orange", value="orange"), app_commands.Choice(name="🩷 Pink", value="pink"),
    app_commands.Choice(name="🟡 Gelb", value="yellow"), app_commands.Choice(name="🩵 Cyan", value="cyan"),
]


def level_from_xp(xp: int) -> int:
    return xp // 100 + 1


def bar(xp: int, size: int = 14) -> str:
    filled = round((xp % 100) / 100 * size)
    return "█" * filled + "░" * (size - filled)


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
        wins = get_wins(interaction.guild.id, member.id, 3)
        economy = get_economy(interaction.guild.id, member.id)
        rank = get_rank(interaction.guild.id, member.id)
        xp = int(stats["xp"])
        color = discord.Color.from_rgb(*PROFILE_COLORS.get(profile["favorite_color"], PROFILE_COLORS["purple"]))
        title = profile["title"] or "MakeItHappen Member"
        display = profile["display_name"] or member.display_name
        dev_badge = " 🛠️ DEV" if member.id == DEV_USER_ID else ""
        embed = discord.Embed(title=f"✨ {display}{dev_badge}", description=profile["bio"] or "*Make it happen.*", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        if profile["banner_url"].startswith(("http://", "https://")):
            embed.set_image(url=profile["banner_url"])
        embed.add_field(name="🏷️ Title", value=title, inline=True)
        embed.add_field(name="⭐ Level", value=f"**{level_from_xp(xp)}** · {xp} XP", inline=True)
        embed.add_field(name="🏅 Server Rank", value=f"**#{rank}**", inline=True)
        if member.id == DEV_USER_ID:
            embed.add_field(name="🛠️ MakeItHappen Dev", value="**Official Developer** • Project Owner", inline=False)
        embed.add_field(name="📈 Progress", value=f"`{bar(xp)}` **{xp % 100}/100**", inline=False)
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} Tage", inline=True)
        embed.add_field(name="🏆 Achievements", value=str(len(achievements)), inline=True)
        embed.add_field(name="🪙 Coins", value=str(economy["coins"]), inline=True)
        if profile["favorite_quote"]:
            embed.add_field(name="💭 Favorite Quote", value=f"_{profile['favorite_quote']}_", inline=False)
        if profile["showcase"]:
            embed.add_field(name="✨ Showcase", value=profile["showcase"], inline=False)
        if wins:
            embed.add_field(name="🏅 Recent Wins", value="\n".join(f"• {row['win'][:120]}" for row in wins), inline=False)
        embed.set_footer(text="MakeItHappen • Believe. Begin. Become.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile_edit", description="Passe dein MakeItHappen-Profil an.")
    @app_commands.describe(
        display_name="Name im MIH-Profil", bio="Kurze Bio", favorite_quote="Dein Lieblingsspruch",
        favorite_color="Deine Lieblingsfarbe", title="Dein Profil-Titel", banner_url="Optionale Bild-URL",
        showcase="Was möchtest du hervorheben?",
    )
    @app_commands.choices(favorite_color=COLOR_CHOICES)
    async def profile_edit(
        self,
        interaction: discord.Interaction,
        display_name: str | None = None,
        bio: str | None = None,
        favorite_quote: str | None = None,
        favorite_color: app_commands.Choice[str] | None = None,
        title: str | None = None,
        banner_url: str | None = None,
        showcase: str | None = None,
    ) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if all(value is None for value in (display_name, bio, favorite_quote, favorite_color, title, banner_url, showcase)):
            return await interaction.response.send_message("ℹ️ Gib mindestens eine Sache an, die du ändern möchtest.", ephemeral=True)
        if banner_url and not banner_url.startswith(("http://", "https://")):
            return await interaction.response.send_message("❌ Die Banner-URL muss mit http:// oder https:// beginnen.", ephemeral=True)
        set_profile(
            interaction.guild.id, interaction.user.id, display_name=display_name, bio=bio,
            favorite_quote=favorite_quote, favorite_color=favorite_color.value if favorite_color else None,
            title=title, banner_url=banner_url, showcase=showcase,
        )
        await interaction.response.send_message("✨ **Dein MIH-Profil wurde aktualisiert.**", ephemeral=True)

    @app_commands.command(name="profile_reset", description="Setzt dein MIH-Profil auf die Standardwerte zurück.")
    async def profile_reset(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        set_profile(interaction.guild.id, interaction.user.id, display_name="", bio="", favorite_quote="", favorite_color="purple", title="", banner_url="", showcase="")
        await interaction.response.send_message("♻️ **Dein MIH-Profil wurde zurückgesetzt.**", ephemeral=True)

    @app_commands.command(name="showcase", description="Zeigt deine ausgewählten Achievements.")
    async def showcase(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_achievements(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("✨ Du hast noch keine Achievements zum Ausstellen.", ephemeral=True)
        selected = ", ".join(row["achievement"] for row in rows[:5])
        set_profile(interaction.guild.id, interaction.user.id, showcase=selected)
        await interaction.response.send_message("✨ Deine ersten fünf Achievements sind jetzt im Profil ausgestellt.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Profile(bot))
