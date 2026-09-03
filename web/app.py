import hashlib
import hmac
import os
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import get_achievements, get_economy, get_profile, get_rank, get_stats, get_wins, init_db, set_profile

app = FastAPI(title="MakeItHappen Web")
WEB_SECRET = os.getenv("WEB_SECRET_KEY")
if not WEB_SECRET:
    raise RuntimeError("WEB_SECRET_KEY muss gesetzt sein.")

init_db()

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
OAUTH_STATE_MAX_AGE = 10 * 60


def make_oauth_state() -> str:
    payload = f"{int(time.time())}.{secrets.token_urlsafe(32)}"
    signature = hmac.new(WEB_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_oauth_state(state: str) -> bool:
    try:
        timestamp, nonce, signature = state.split(".", 2)
        payload = f"{timestamp}.{nonce}"
        issued_at = int(timestamp)
    except (ValueError, TypeError):
        return False
    if abs(time.time() - issued_at) > OAUTH_STATE_MAX_AGE:
        return False
    expected = hmac.new(WEB_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def level_from_xp(xp: int) -> int:
    return xp // 100 + 1


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


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    with open("web/static/index.html", encoding="utf-8") as file:
        return file.read()


@app.get("/api/profile/{guild_id}/{user_id}")
async def profile(guild_id: int, user_id: int) -> dict:
    return serialize_profile(guild_id, user_id)


@app.get("/api/my-profile/{guild_id}")
async def my_profile(request: Request, guild_id: int) -> dict:
    user = require_user(request)
    return serialize_profile(guild_id, int(user["id"]))


@app.patch("/api/my-profile/{guild_id}")
async def edit_my_profile(request: Request, guild_id: int) -> dict:
    user = require_user(request)
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
    state = make_oauth_state()
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    return RedirectResponse("https://discord.com/oauth2/authorize?" + urlencode(params))


@app.get("/auth/callback")
async def callback(request: Request, code: str = "", state: str = ""):
    if not code or not state or not verify_oauth_state(state):
        raise HTTPException(400, "Ungültiger oder abgelaufener OAuth2-Status.")
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
        user_response = await client.get(f"{DISCORD_API}/users/@me", headers={"Authorization": f"Bearer {token}"})
        user_response.raise_for_status()
        request.session["discord_user"] = user_response.json()
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
