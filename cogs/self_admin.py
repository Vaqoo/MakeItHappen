import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from database import DB_PATH, add_coins, add_xp, get_economy, get_inventory, get_stats, set_profile

AUTHORIZED_USER_ID = 1283785169664213101


class SelfAdmin(commands.Cog):
    """Developer-only controls for manipulating the command user's own MIH account."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != AUTHORIZED_USER_ID:
            await interaction.response.send_message("❌ Dieser MIH Admin-Befehl ist nicht für dich freigeschaltet.", ephemeral=True)
            return False
        if interaction.guild is None:
            await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="miha_coins", description="[DEV] Verändert deine eigenen MIH Coins.")
    @app_commands.describe(amount="Positiv = hinzufügen, negativ = entfernen")
    async def coins(self, interaction: discord.Interaction, amount: int) -> None:
        if not await self._guard(interaction): return
        balance = add_coins(interaction.guild.id, interaction.user.id, amount)
        await interaction.response.send_message(f"🪙 Eigene Balance geändert: **{balance} Coins**.", ephemeral=True)

    @app_commands.command(name="miha_setcoins", description="[DEV] Setzt deine eigenen MIH Coins.")
    @app_commands.describe(amount="Neue Balance")
    async def setcoins(self, interaction: discord.Interaction, amount: app_commands.Range[int, 0, 2147483647]) -> None:
        if not await self._guard(interaction): return
        current = int(get_economy(interaction.guild.id, interaction.user.id)["coins"])
        balance = add_coins(interaction.guild.id, interaction.user.id, amount - current)
        await interaction.response.send_message(f"🪙 Eigene Balance gesetzt: **{balance} Coins**.", ephemeral=True)

    @app_commands.command(name="miha_xp", description="[DEV] Verändert deine eigenen XP.")
    @app_commands.describe(amount="Positiv = hinzufügen, negativ = entfernen")
    async def xp(self, interaction: discord.Interaction, amount: int) -> None:
        if not await self._guard(interaction): return
        total = add_xp(interaction.guild.id, interaction.user.id, amount)
        await interaction.response.send_message(f"⭐ Eigene XP geändert: **{total} XP**.", ephemeral=True)

    @app_commands.command(name="miha_level", description="[DEV] Setzt dein eigenes Level.")
    @app_commands.describe(level="Neues Level (1–100000)")
    async def level(self, interaction: discord.Interaction, level: app_commands.Range[int, 1, 100000]) -> None:
        if not await self._guard(interaction): return
        current = int(get_stats(interaction.guild.id, interaction.user.id)["xp"])
        target_xp = (level - 1) * 100
        total = add_xp(interaction.guild.id, interaction.user.id, target_xp - current)
        await interaction.response.send_message(f"⭐ Eigenes Level gesetzt: **Level {level}** · {total} XP.", ephemeral=True)

    @app_commands.command(name="miha_streak", description="[DEV] Setzt deinen eigenen Streak.")
    @app_commands.describe(days="Neue Streak-Länge")
    async def streak(self, interaction: discord.Interaction, days: app_commands.Range[int, 0, 1000000]) -> None:
        if not await self._guard(interaction): return
        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (interaction.guild.id, interaction.user.id))
            db.execute("UPDATE user_stats SET streak = ? WHERE guild_id = ? AND user_id = ?", (days, interaction.guild.id, interaction.user.id))
        await interaction.response.send_message(f"🔥 Eigener Streak gesetzt: **{days} Tage**.", ephemeral=True)

    @app_commands.command(name="miha_item", description="[DEV] Fügt dir ein beliebiges MIH-Shop-Item kostenlos hinzu.")
    @app_commands.describe(item_id="Shop-Item-ID, z. B. title_legend")
    async def item(self, interaction: discord.Interaction, item_id: str) -> None:
        if not await self._guard(interaction): return
        item_id = item_id.strip().lower()
        from cogs.economy import SHOP
        if item_id not in SHOP:
            return await interaction.response.send_message("❌ Unbekannte Item-ID. Nutze `/shop`.", ephemeral=True)
        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT OR IGNORE INTO inventory (guild_id, user_id, item_id) VALUES (?, ?, ?)", (interaction.guild.id, interaction.user.id, item_id))
        await interaction.response.send_message(f"🎁 **{SHOP[item_id]['name']}** kostenlos zum eigenen Inventar hinzugefügt.", ephemeral=True)

    @app_commands.command(name="miha_removeitem", description="[DEV] Entfernt ein eigenes MIH-Shop-Item.")
    @app_commands.describe(item_id="Shop-Item-ID")
    async def removeitem(self, interaction: discord.Interaction, item_id: str) -> None:
        if not await self._guard(interaction): return
        item_id = item_id.strip().lower()
        with sqlite3.connect(DB_PATH) as db:
            removed = db.execute("DELETE FROM inventory WHERE guild_id = ? AND user_id = ? AND item_id = ?", (interaction.guild.id, interaction.user.id, item_id)).rowcount
        await interaction.response.send_message("🗑️ Eigenes Item entfernt." if removed else "❌ Dieses Item besitzt du nicht.", ephemeral=True)

    @app_commands.command(name="miha_profile", description="[DEV] Setzt deine eigenen MIH-Profilfelder.")
    @app_commands.describe(display_name="Profilname", bio="Bio", quote="Lieblingsquote", title="Titel", banner="Banner-URL", showcase="Showcase")
    async def profile(self, interaction: discord.Interaction, display_name: str | None = None, bio: str | None = None, quote: str | None = None, title: str | None = None, banner: str | None = None, showcase: str | None = None) -> None:
        if not await self._guard(interaction): return
        if all(value is None for value in (display_name, bio, quote, title, banner, showcase)):
            return await interaction.response.send_message("ℹ️ Gib mindestens ein Feld an.", ephemeral=True)
        if banner and not banner.startswith(("http://", "https://")):
            return await interaction.response.send_message("❌ Die Banner-URL muss mit http:// oder https:// beginnen.", ephemeral=True)
        set_profile(interaction.guild.id, interaction.user.id, display_name=display_name, bio=bio, favorite_quote=quote, title=title, banner_url=banner, showcase=showcase)
        await interaction.response.send_message("✨ Eigene MIH-Profilfelder geändert.", ephemeral=True)

    @app_commands.command(name="miha_reset", description="[DEV] Setzt alle manipulierbaren eigenen MIH-Daten zurück.")
    async def reset(self, interaction: discord.Interaction) -> None:
        if not await self._guard(interaction): return
        gid, uid = interaction.guild.id, interaction.user.id
        with sqlite3.connect(DB_PATH) as db:
            for table in ("inventory", "achievements", "goals", "moods", "journal", "wins", "warnings", "birthdays"):
                db.execute(f"DELETE FROM {table} WHERE guild_id = ? AND user_id = ?", (gid, uid))
            db.execute("INSERT OR REPLACE INTO economy (guild_id, user_id, coins) VALUES (?, ?, 0)", (gid, uid))
            db.execute("INSERT OR REPLACE INTO user_stats (guild_id, user_id, xp, streak, last_daily, last_work) VALUES (?, ?, 0, 0, NULL, NULL)", (gid, uid))
        set_profile(gid, uid, display_name="", bio="", favorite_quote="", favorite_color="purple", title="", banner_url="", showcase="")
        await interaction.response.send_message("♻️ Dein eigener MIH-Account wurde vollständig zurückgesetzt.", ephemeral=True)

    @app_commands.command(name="miha_dump", description="[DEV] Zeigt eine kompakte Übersicht deiner eigenen MIH-Daten.")
    async def dump(self, interaction: discord.Interaction) -> None:
        if not await self._guard(interaction): return
        stats = get_stats(interaction.guild.id, interaction.user.id)
        economy = get_economy(interaction.guild.id, interaction.user.id)
        inventory = get_inventory(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(f"🧪 **MIH Dev Account**\n⭐ XP: **{stats['xp']}**\n🏅 Level: **{int(stats['xp']) // 100 + 1}**\n🔥 Streak: **{stats['streak']}**\n🪙 Coins: **{economy['coins']}**\n🎒 Items: **{len(inventory)}**", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelfAdmin(bot))
