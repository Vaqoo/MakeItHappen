import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.middleware.sessions import SessionMiddleware

from database import _connect, get_achievements, get_economy, get_profile, get_rank, get_stats, get_wins, init_db, set_profile

app = FastAPI(title="MakeItHappen Web")
init_db()

WEB_SECRET = os.getenv("WEB_SECRET_KEY")
if not WEB_SECRET:
    raise RuntimeError("WEB_SECRET_KEY muss gesetzt sein.")
app.add_middleware(
    SessionMiddleware,
    secret_key=WEB_SECRET,
    same_site="lax",
    https_only=os.getenv("WEB_COOKIE_SECURE", "0") == "1",
    max_age=60 * 60 * 24 * 7,
)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
DISCORD_API = "https://discord.com/api/v10"
OAUTH_STATE = URLSafeTimedSerializer(WEB_SECRET, salt="mih-oauth-state")


def level_from_xp(xp: int) -> int:
    return xp // 100 + 1


def configured_guild_ids() -> set[int]:
    """Return guilds initialized by the bot, without creating rows for them."""
    with _connect() as db:
        rows = db.execute("SELECT guild_id FROM guild_config").fetchall()
    return {int(row["guild_id"]) for row in rows}


def session_guilds(request: Request) -> list[dict]:
    return request.session.get("discord_guilds", [])


def user_has_guild(request: Request, guild_id: int) -> bool:
    return any(int(guild["id"]) == guild_id for guild in session_guilds(request))


def serialize_profile(guild_id: int, user_id: int) -> dict:
    stats = get_stats(guild_id, user_id)
    profile = get_profile(guild_id, user_id)
    achievements = get_achievements(guild_id, user_id)
    wins = get_wins(guild_id, user_id, 5)
    economy = get_economy(guild_id, user_id)
    xp = int(stats["xp"])
    return {
        "guild_id": guild_id,
        "user_id": user_id,
        "display_name": profile["display_name"],
        "bio": profile["bio"],
        "favorite_quote": profile["favorite_quote"],
        "favorite_color": profile["favorite_color"],
        "title": profile["title"],
        "banner_url": profile["banner_url"] if str(profile["banner_url"]).startswith(("http://", "https://")) else "",
        "showcase": profile["showcase"],
        "xp": xp,
        "level": level_from_xp(xp),
        "level_progress": xp % 100,
        "streak": int(stats["streak"]),
        "coins": int(economy["coins"]),
        "rank": get_rank(guild_id, user_id),
        "achievements": [dict(row) for row in achievements],
        "wins": [dict(row) for row in wins],
    }


def require_user(request: Request) -> dict:
    user = request.session.get("discord_user")
    if not user:
        raise HTTPException(401, "Discord-Login erforderlich.")
    return user


def require_user_guild(request: Request, guild_id: int) -> dict:
    user = require_user(request)
    if not user_has_guild(request, guild_id):
        raise HTTPException(403, "Du bist kein Mitglied dieses Discord-Servers.")
    if guild_id not in configured_guild_ids():
        raise HTTPException(404, "MakeItHappen ist auf diesem Discord-Server noch nicht initialisiert.")
    return user


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    with open("web/static/index.html", encoding="utf-8") as file:
        return file.read()


@app.get("/api/profile/{guild_id}/{user_id}")
async def profile(guild_id: int, user_id: int) -> dict:
    return serialize_profile(guild_id, user_id)


@app.get("/api/my-guilds")
async def my_guilds(request: Request) -> list[dict]:
    require_user(request)
    configured = configured_guild_ids()
    return [guild for guild in session_guilds(request) if int(guild["id"]) in configured]


@app.get("/api/my-profile/{guild_id}")
async def my_profile(request: Request, guild_id: int) -> dict:
    user = require_user_guild(request, guild_id)
    return serialize_profile(guild_id, int(user["id"]))


@app.patch("/api/my-profile/{guild_id}")
async def edit_my_profile(request: Request, guild_id: int) -> dict:
    user = require_user_guild(request, guild_id)
    payload = await request.json()
    allowed = {"display_name", "bio", "favorite_quote", "favorite_color", "title", "banner_url", "showcase"}
    unknown = set(payload) - allowed
    if unknown:
        raise HTTPException(400, "Ungültige Profilfelder.")
    values = {key: str(payload[key]).strip() for key in allowed if key in payload}
    if "banner_url" in values and values["banner_url"] and not values["banner_url"].startswith(("http://", "https://")):
        raise HTTPException(400, "Banner-URL muss mit http:// oder https:// beginnen.")
    if "favorite_color" in values and values["favorite_color"] not in {"purple", "blue", "red", "green", "orange", "pink", "yellow", "cyan"}:
        raise HTTPException(400, "Ungültige Profilfarbe.")
    set_profile(guild_id, int(user["id"]), **values)
    return serialize_profile(guild_id, int(user["id"]))


@app.get("/auth/login")
async def login(request: Request):
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(503, "Discord OAuth2 ist noch nicht konfiguriert.")

    state = OAUTH_STATE.dumps({"nonce": secrets.token_urlsafe(24)})
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    return RedirectResponse("https://discord.com/oauth2/authorize?" + urlencode(params))


@app.get("/auth/callback")
async def callback(request: Request, code: str = "", state: str = ""):
    if not code or not state:
        raise HTTPException(400, "Discord-OAuth2 Callback ist unvollständig.")
    try:
        OAUTH_STATE.loads(state, max_age=600)
    except SignatureExpired:
        raise HTTPException(400, "Der Discord-OAuth2-Login ist abgelaufen. Bitte erneut einloggen.")
    except BadSignature:
        raise HTTPException(400, "Ungültiger OAuth2-Status.")

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_response = await client.get(f"{DISCORD_API}/users/@me", headers=headers)
        user_response.raise_for_status()
        guilds_response = await client.get(f"{DISCORD_API}/users/@me/guilds", headers=headers)
        guilds_response.raise_for_status()
        discord_guilds = guilds_response.json()
        configured = configured_guild_ids()
        request.session.clear()
        request.session["discord_user"] = user_response.json()
        # Only keep servers where MIH is actually initialized. This keeps the
        # signed session cookie small enough for mobile browsers and avoids
        # selecting an unrelated Discord server as the default profile.
        request.session["discord_guilds"] = [
            {"id": guild["id"], "name": guild["name"], "icon": guild.get("icon")}
            for guild in discord_guilds
            if int(guild["id"]) in configured
        ]
    return RedirectResponse("/")


@app.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/api/me")
async def me(request: Request):
    user = request.session.get("discord_user")
    return {"authenticated": bool(user), "user": user}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "mih-web"}
