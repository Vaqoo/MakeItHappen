# MakeItHappen 🤖

A modular Discord bot built with Python and `discord.py`.

## Features

- ⚡ Slash commands
- 🛡️ Moderation: `/kick`, `/ban`, `/timeout`, `/purge`
- 🔧 Utility: `/ping`, `/serverinfo`, `/userinfo`, `/avatar`
- 🎉 Fun: `/8ball`, `/coinflip`, `/roll`
- 🔐 Environment-based configuration
- 📦 Cog-based architecture for easy expansion

## Requirements

- Python 3.11+
- A Discord application/bot token

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Vaqoo/MakeItHappen.git
cd MakeItHappen
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**
```bash
.venv\\Scripts\\activate
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the bot

Copy `.env.example` to `.env` and add your Discord bot token:

```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=
LOG_LEVEL=INFO
```

Never commit `.env` or your bot token.

### 5. Invite the bot

Create an invite in the Discord Developer Portal with the `bot` and `applications.commands` scopes. Grant only the permissions your bot actually needs.

### 6. Start the bot

```bash
python bot.py
```

If `GUILD_ID` is set, slash commands are synced to that server for fast development updates. Without it, commands are synced globally.

## Project structure

```text
MakeItHappen/
├── bot.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── cogs/
│   ├── __init__.py
│   ├── moderation.py
│   ├── utility.py
│   └── fun.py
├── utils/
│   ├── __init__.py
│   └── checks.py
└── .github/
    └── workflows/
        └── ci.yml
```

## License

This project is currently unlicensed. Add a license before distributing it publicly.
