import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import get_achievements, get_economy, get_profile, get_rank, get_stats, get_wins

app = FastAPI(title="MakeItHappen Web")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("WEB_SECRET_KEY", "dev-only-change-me"), same_site="lax", https_only=os.getenv("WEB_COOKIE_SECURE", "0") == "1")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
DISCORD_API = "https://discord.com/api/v10"


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


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    with open("web/static/index.html", encoding="utf-8") as file:
        return file.read()


@app.get("/api/profile/{guild_id}/{user_id}")
async def profile(guild_id: int, user_id: int) -> dict:
    return serialize_profile(guild_id, user_id)


@app.get("/auth/login")
async def login(request: Request):
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(503, "Discord OAuth2 ist noch nicht konfiguriert.")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
    }
    return RedirectResponse("https://discord.com/oauth2/authorize?" + urlencode(params))


@app.get("/auth/callback")
async def callback(request: Request, code: str = "", state: str = ""):
    if not code or not secrets.compare_digest(state, request.session.pop("oauth_state", "")):
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
        user_response = await client.get(f"{DISCORD_API}/users/@me", headers={"Authorization": f"Bearer {token}"})
        user_response.raise_for_status()
        request.session["discord_user"] = user_response.json()
    return RedirectResponse("/")


@app.get("/api/me")
async def me(request: Request):
    user = request.session.get("discord_user")
    return {"authenticated": bool(user), "user": user}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "mih-web"}
