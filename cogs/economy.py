from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from database import add_coins, add_xp, buy_item, get_economy, get_inventory, get_profile, get_stats, set_profile, claim_work, transfer_coins


SHOP = {
    "title_grinder": {"name": "🔥 Grinder", "price": 250, "type": "title", "value": "Grinder"},
    "title_driven": {"name": "🚀 Driven", "price": 500, "type": "title", "value": "Driven"},
    "title_elite": {"name": "👑 Elite", "price": 1000, "type": "title", "value": "Elite"},
    "title_legend": {"name": "💎 Legend", "price": 2500, "type": "title", "value": "Legend"},
    "badge_fire": {"name": "🔥 Fire Badge", "price": 750, "type": "badge", "value": "🔥"},
    "badge_star": {"name": "⭐ Star Badge", "price": 750, "type": "badge", "value": "⭐"},
}


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="balance", description="Zeigt deine MIH Coins.")
    async def balance(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        member = member or interaction.user
        data = get_economy(interaction.guild.id, member.id)
        await interaction.response.send_message(f"🪙 **{member.display_name}** hat **{data['coins']} MIH Coins**.")

    @app_commands.command(name="work", description="Verdiene einmal pro Stunde MIH Coins.")
    async def work(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        stats = get_stats(interaction.guild.id, interaction.user.id)
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(hours=1)).isoformat()
        if stats["last_work"]:
            try:
                last = datetime.fromisoformat(str(stats["last_work"]).replace("Z", "+00:00"))
                remaining = timedelta(hours=1) - (now - last)
                if remaining.total_seconds() > 0:
                    minutes = max(1, int(remaining.total_seconds() // 60))
                    return await interaction.response.send_message(f"⏳ Du kannst `/work` in **{minutes} Minuten** wieder benutzen.", ephemeral=True)
            except ValueError:
                pass
        if not claim_work(interaction.guild.id, interaction.user.id, now.isoformat(), cutoff):
            latest = get_stats(interaction.guild.id, interaction.user.id)
            try:
                last = datetime.fromisoformat(str(latest["last_work"]).replace("Z", "+00:00"))
                minutes = max(1, int((timedelta(hours=1) - (now - last)).total_seconds() // 60))
            except (ValueError, TypeError):
                minutes = 1
            return await interaction.response.send_message(f"⏳ Du kannst `/work` in etwa **{minutes} Minuten** wieder benutzen.", ephemeral=True)
        reward = 80 + (interaction.user.id % 71)
        coins = add_coins(interaction.guild.id, interaction.user.id, reward)
        xp = add_xp(interaction.guild.id, interaction.user.id, 10)
        await interaction.response.send_message(f"💼 **Work abgeschlossen!**\n\n🪙 +{reward} Coins · ⭐ +10 XP\n💰 Kontostand: **{coins} Coins** · XP: **{xp}**")

    @app_commands.command(name="shop", description="Zeigt den MIH Cosmetic Shop.")
    async def shop(self, interaction: discord.Interaction) -> None:
        lines = [f"`{item_id}` — {item['name']} · **{item['price']} 🪙**" for item_id, item in SHOP.items()]
        await interaction.response.send_message("🛍️ **MIH Shop**\n\n" + "\n".join(lines) + "\n\nKaufen mit `/buy item:<ID>`. ")

    @app_commands.command(name="buy", description="Kauft ein Cosmetic aus dem MIH Shop.")
    @app_commands.describe(item="Die ID aus /shop")
    async def buy(self, interaction: discord.Interaction, item: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        item = item.strip().lower()
        product = SHOP.get(item)
        if product is None:
            return await interaction.response.send_message("❌ Dieses Item gibt es nicht. Nutze `/shop`.", ephemeral=True)
        if not buy_item(interaction.guild.id, interaction.user.id, item, product["price"]):
            balance = get_economy(interaction.guild.id, interaction.user.id)["coins"]
            return await interaction.response.send_message(f"❌ Kauf nicht möglich. Du besitzt **{balance} Coins** oder hast das Item bereits.", ephemeral=True)
        balance = get_economy(interaction.guild.id, interaction.user.id)["coins"]
        await interaction.response.send_message(f"🛍️ **{product['name']}** gekauft!\n💰 Rest: **{balance} Coins**")

    @app_commands.command(name="inventory", description="Zeigt deine gekauften MIH Cosmetics.")
    async def inventory(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_inventory(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🎒 Dein Inventar ist noch leer. `/shop` wartet auf dich.")
        lines = [f"• `{row['item_id']}` — {SHOP.get(row['item_id'], {}).get('name', 'Unknown Item')}" for row in rows]
        await interaction.response.send_message("🎒 **Dein MIH Inventar**\n\n" + "\n".join(lines))

    @app_commands.command(name="equip", description="Rüstet einen gekauften Titel aus.")
    @app_commands.describe(item="Item-ID eines gekauften Titel-Cosmetics")
    async def equip(self, interaction: discord.Interaction, item: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        item = item.strip().lower()
        product = SHOP.get(item)
        owned = {row["item_id"] for row in get_inventory(interaction.guild.id, interaction.user.id)}
        if item not in owned or not product or product["type"] != "title":
            return await interaction.response.send_message("❌ Dieses Titel-Item besitzt du nicht.", ephemeral=True)
        set_profile(interaction.guild.id, interaction.user.id, title=product["value"])
        await interaction.response.send_message(f"👑 Titel ausgerüstet: **{product['value']}**")

    @app_commands.command(name="pay", description="Überweist MIH Coins an ein anderes Mitglied.")
    @app_commands.describe(member="Empfänger", amount="Anzahl Coins")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 1000000]) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if member.bot or member == interaction.user:
            return await interaction.response.send_message("❌ Ungültiger Empfänger.", ephemeral=True)
        if not transfer_coins(interaction.guild.id, interaction.user.id, member.id, amount):
            balance = get_economy(interaction.guild.id, interaction.user.id)["coins"]
            return await interaction.response.send_message(f"❌ Überweisung nicht möglich. Dein Kontostand: **{balance} Coins**.", ephemeral=True)
        await interaction.response.send_message(f"💸 **{amount} Coins** an {member.mention} überwiesen.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))
