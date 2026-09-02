import discord


def is_staff(interaction: discord.Interaction) -> bool:
    """Return True when the member has moderation permissions."""
    user = interaction.user
    return isinstance(user, discord.Member) and user.guild_permissions.manage_guild
