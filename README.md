# MakeItHappen 🤖💜

**MakeItHappen (MIH)** is a motivational Discord companion with serious server-management tools underneath. The goal is not to be another generic moderation bot: MIH should help people keep moving, build habits, set goals and feel supported while keeping communities safe.

## 🧠 Motivation & support

- `/motivate` — quick motivation boost
- `/quote` — motivation, focus, discipline, mindset or tough-day quotes
- `/daily` — daily motivation + XP + streaks
- `/challenge` — small actionable challenge
- `/helpme` — supportive next-step advice

## 🎯 Personal progress

- `/goal` — create a goal
- `/goals` — view open goals
- `/complete` — complete a goal and earn XP
- `/profile` — MIH profile, level, XP and streak
- `/achievements` — unlocked achievements
- Persistent SQLite storage in `data/makeithappen.db`

## 🔊 Temporary voice

- `/setup_tempvoice` — creates a Join-to-Create system
- `/voice_lock` — lock your temporary room
- `/voice_unlock` — unlock it
- Empty temporary rooms are automatically deleted

## 🛡️ Moderation

- `/kick`
- `/ban`
- `/unban`
- `/timeout`
- `/untimeout`
- `/purge`

## 📋 Mod & activity logs

Use `/setup_logs` in the channel where logs should go. MIH can log:

- joins / leaves
- message edits / deletes
- voice joins / leaves / moves
- nickname changes
- role changes
- channel creation / deletion
- kicks / bans / unbans
- timeouts / timeout removals
- purges

## 🚨 AutoMod

Use `/setup_automod` to enable basic protection against:

- Discord invite spam
- message flooding

Use `/automod_off` to disable it.

## ⚙️ Setup requirements

Because MIH listens for members, voice activity and message content, enable these intents for the bot in the Discord Developer Portal:

- **Server Members Intent**
- **Message Content Intent**

The bot also needs the permissions required for the features you enable, especially **Manage Messages**, **Moderate Members**, **Manage Channels**, **Move Members**, **View Audit Log** (recommended for richer auditing), and **Send Messages / Embed Links**.

## GitHub Actions test hosting

The repository includes a manual GitHub Actions workflow for testing the bot. Store the bot token as the repository secret `DISCORD_TOKEN`; never commit a token.

## Local setup

```bash
git clone https://github.com/Vaqoo/MakeItHappen.git
cd MakeItHappen
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`:
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=
LOG_LEVEL=INFO
```

Start:
```bash
python bot.py
```

## Architecture

```text
MakeItHappen/
├── bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── cogs/
│   ├── moderation.py
│   ├── utility.py
│   ├── fun.py
│   ├── motivation.py
│   ├── community.py
│   ├── voice.py
│   ├── logs.py
│   └── admin.py
└── .github/workflows/
    ├── ci.yml
    └── bot.yml
```

**Make it happen.** 🔥
