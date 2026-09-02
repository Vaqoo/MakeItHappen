import discord
from discord.ext import commands

from database import get_config


class ModLogs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def send_log(self, guild: discord.Guild, title: str, description: str, color: discord.Color = discord.Color.blurple()) -> None:
        config = get_config(guild.id)
        channel_id = config["log_channel_id"]
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_mih_moderation_log(self, guild: discord.Guild, title: str, description: str, color: discord.Color) -> None:
        await self.send_log(guild, title, description, color)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.send_log(member.guild, "📥 Member Joined", f"{member.mention} `{member}`\nID: `{member.id}`", discord.Color.green())

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self.send_log(member.guild, "📤 Member Left", f"**{member}**\nID: `{member.id}`", discord.Color.orange())

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.nick != after.nick:
            await self.send_log(after.guild, "✏️ Nickname Changed", f"**User:** {after.mention}\n**Before:** {before.nick or before.name}\n**After:** {after.nick or after.name}")
        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}
        added = [role.mention for role in after.roles if role.id not in before_roles]
        removed = [role.mention for role in before.roles if role.id not in after_roles]
        if added or removed:
            changes = []
            if added:
                changes.append("Added: " + ", ".join(added))
            if removed:
                changes.append("Removed: " + ", ".join(removed))
            await self.send_log(after.guild, "🎭 Roles Changed", f"**User:** {after.mention}\n" + "\n".join(changes))

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.guild and not message.author.bot:
            content = message.content[:1000] if message.content else "*(kein Text / nicht im Cache)*"
            await self.send_log(message.guild, "🗑️ Message Deleted", f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {content}", discord.Color.red())

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.guild and not before.author.bot and before.content != after.content:
            await self.send_log(before.guild, "✏️ Message Edited", f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n**Before:** {before.content[:500]}\n**After:** {after.content[:500]}", discord.Color.gold())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if before.channel != after.channel:
            if before.channel is None and after.channel:
                text = f"{member.mention} joined **{after.channel.name}**"
            elif after.channel is None and before.channel:
                text = f"{member.mention} left **{before.channel.name}**"
            else:
                text = f"{member.mention} moved from **{before.channel.name}** to **{after.channel.name}**"
            await self.send_log(member.guild, "🔊 Voice Activity", text)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        await self.send_log(channel.guild, "🆕 Channel Created", f"**{channel.name}** (`{channel.id}`)", discord.Color.green())

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        await self.send_log(channel.guild, "🗑️ Channel Deleted", f"**{channel.name}** (`{channel.id}`)", discord.Color.red())

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        await self.send_log(role.guild, "🎭 Role Created", f"**{role.name}** (`{role.id}`)", discord.Color.green())

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        await self.send_log(role.guild, "🎭 Role Deleted", f"**{role.name}** (`{role.id}`)", discord.Color.red())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModLogs(bot))
