# MakeItHappen 🚀

MakeItHappen (MIH) is a Discord community bot built around one idea: **turn motivation into action.**

## 🧠 Mindset
- `/motivate` — kurzer Motivationsboost
- `/quote` — Quotes nach Kategorie
- `/challenge` — kleine Challenges
- `/daily` — tägliche Motivation + Streak + Rewards
- `/helpme` — wenn du gerade nicht weiterweißt
- `/mood` + `/mood_history` — Mood-Tracking
- `/journal` + `/journal_history` — private Journal-Einträge
- `/win` + `/wins` — kleine Erfolge festhalten

## 👥 Progression & Community
- Nachrichten geben XP (mit Cooldown gegen Spam-Farming)
- Level-System mit Level-Up-Meldungen
- `/stats` — Level, XP, Fortschritt, Rang und Streak
- `/leaderboard` — Server-XP-Ranking
- `/goal` — persönliches Ziel erstellen
- `/goals` — offene Ziele
- `/complete` — Ziel abschließen und Rewards bekommen
- `/goal_delete` — Ziel löschen
- `/achievements` — freigeschaltete Achievements

## 👤 MIH Profile
- `/profile` — modernes MIH-Profil
- `/profile_edit` — Name, Bio, Quote, Farbe, Titel, Banner und Showcase anpassen
- `/profile_reset` — Profil zurücksetzen
- `/showcase` — Achievements im Profil ausstellen
- XP-Fortschrittsbalken, Server-Rang, Coins, Streak und Wins im Profil

## 🪙 MIH Economy
- `/balance` — Coins anzeigen
- `/work` — einmal pro Stunde Coins verdienen
- `/shop` — Cosmetics kaufen
- `/buy` — Shop-Item kaufen
- `/inventory` — gekaufte Cosmetics
- `/equip` — gekauften Titel ausrüsten
- `/pay` — Coins an andere User schicken

## 🛡️ Safety & Moderation
- `/kick`, `/ban`, `/unban`
- `/timeout`, `/untimeout`
- `/warn`, `/warnings`, `/clearwarns`
- `/purge`
- persistent Moderations-Warnungen
- AutoMod: Invite-Links, Links, Caps, Mention-Spam und Flooding
- Anti-Raid: Join-Burst-Erkennung mit Mod-Log-Alarm
- umfangreiche Mod-Logs
- `/lockdown` für Server-Notfälle

## 🔊 Temporary Voice
- `/setup_tempvoice`
- automatische temporäre Räume
- `/voice_rename`
- `/voice_limit`
- `/voice_lock` / `/voice_unlock`
- `/voice_kick`
- `/voice_transfer`

## 🌐 Server Tools
- Welcome-System: `/setup_welcome`
- Goodbye-System: `/setup_goodbye`
- Suggestions: `/setup_suggestions` + `/suggest`
- Ja/Nein-Polls: `/poll`
- Birthday-System: `/birthday`

## 🧰 Utility & Fun
- `/ping`
- `/serverinfo`
- `/userinfo`
- `/avatar`
- `/8ball`
- `/coinflip`
- `/roll`

## ⚙️ Setup

1. Python 3.12 installieren.
2. Dependencies installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env.example` nach `.env` kopieren und Token/Guild-ID eintragen.
4. Im Discord Developer Portal **Server Members Intent** und **Message Content Intent** aktivieren.
5. Starten:
   ```bash
   python bot.py
   ```

### GitHub Actions
- `CI` prüft bei Push/PR automatisch die Python-Syntax.
- `Run Discord Bot` kann den Bot über `workflow_dispatch` starten.
- Der GitHub Runner ist nur temporäres Hosting und daher **kein 24/7-Produktivhosting**.

## 🗂️ Architektur

```text
MakeItHappen/
├── bot.py
├── config.py
├── database.py
├── cogs/
│   ├── admin.py
│   ├── community.py
│   ├── economy.py
│   ├── fun.py
│   ├── logs.py
│   ├── moderation.py
│   ├── motivation.py
│   ├── profile.py
│   ├── server.py
│   ├── utility.py
│   └── voice.py
└── .github/workflows/
    ├── ci.yml
    └── bot.yml
```

**Make it happen. 🔥**
