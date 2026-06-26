import aiohttp
from data.config import YOUTHGUARD_API_URL, YOUTHGUARD_BOT_SECRET

BASE = YOUTHGUARD_API_URL
SECRET = YOUTHGUARD_BOT_SECRET

_tokens = {}


async def bot_auth(telegram_id: int, full_name: str, username: str = None) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}/accounts/api/bot-auth/", json={
            "secret_key": SECRET,
            "telegram_id": telegram_id,
            "full_name": full_name,
            "username": username or "",
        }) as resp:
            return await resp.json()


async def get_token(telegram_id: int, full_name: str, username: str = None) -> str:
    if telegram_id in _tokens:
        return _tokens[telegram_id]
    data = await bot_auth(telegram_id, full_name, username)
    token = data.get("token")
    if token:
        _tokens[telegram_id] = token
    return token


async def check_telegram(telegram_id: int) -> dict:
    """Telegram_id bazada bormi — rolini qaytaradi (user yaratmaydi)."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}/accounts/api/check-telegram/", json={
            "secret_key": SECRET,
            "telegram_id": telegram_id,
        }) as resp:
            data = await resp.json()
    if data.get("token"):
        _tokens[telegram_id] = data["token"]
    return data


async def phone_lookup(telegram_id: int, phone: str, full_name: str, username: str = None) -> dict:
    """Telefon raqamni yuboradi — bazadan rolni topadi yoki oddiy user yaratadi."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}/accounts/api/phone-lookup/", json={
            "secret_key": SECRET,
            "telegram_id": telegram_id,
            "phone": phone,
            "full_name": full_name,
            "username": username or "",
        }) as resp:
            data = await resp.json()
    if data.get("token"):
        _tokens[telegram_id] = data["token"]
    return data


async def get_my_youth(token: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}/yoshlar/api/",
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            data = await resp.json()
            if isinstance(data, list):
                return data
            return data.get("results", [])


async def create_meeting(token: str, payload: dict) -> dict:
    data = aiohttp.FormData()
    for key, val in payload.items():
        if key == "photo" and val:
            data.add_field("photo", val["data"], filename=val["filename"], content_type="image/jpeg")
        else:
            data.add_field(key, str(val))
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE}/uchrashuvlar/api/list/",
            data=data,
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            return await resp.json()


async def get_pending_verifications(token: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}/uchrashuvlar/api/pending-verifications/",
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            data = await resp.json()
            if isinstance(data, list):
                return data
            return data.get("results", [])


async def verify_meeting(token: str, meeting_id: int, action: str, reason: str = "") -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE}/uchrashuvlar/api/{meeting_id}/verify/",
            json={"action": action, "rejection_reason": reason},
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            return await resp.json()


async def get_my_meetings(token: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}/uchrashuvlar/api/list/",
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            data = await resp.json()
            if isinstance(data, list):
                return data
            return data.get("results", [])


async def _get(path: str, token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}{path}",
            headers={"Authorization": f"Token {token}"}
        ) as resp:
            return await resp.json()


async def get_my_youth_stats(token: str) -> list:
    data = await _get("/uchrashuvlar/api/my-youth/", token)
    return data if isinstance(data, list) else []


async def get_youth_stats(token: str, youth_id: int) -> dict:
    return await _get(f"/uchrashuvlar/api/youth/{youth_id}/stats/", token)


async def get_my_yetakchilar(token: str) -> list:
    data = await _get("/uchrashuvlar/api/my-yetakchilar/", token)
    return data if isinstance(data, list) else []


async def get_my_stats(token: str) -> dict:
    return await _get("/uchrashuvlar/api/my-stats/", token)


async def get_active_survey(token: str) -> dict:
    """Faol so'rovnomani va savollarni qaytaradi."""
    try:
        return await _get("/sorovnoma/api/active/", token)
    except Exception:
        return {"active": False}
