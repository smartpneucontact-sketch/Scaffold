"""Fire-and-forget visitor notification via Resend HTTPS API.

Ported from Site Copilot's notifications module. Resend is the primary
transport because Railway blocks outbound SMTP. Same dedup + bot-filter
pipeline."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

_DEDUP_TTL_SEC = 24 * 3600
_seen_ips: dict[str, float] = {}

_BOT_SUBSTRINGS = (
    "bot", "crawler", "spider", "facebookexternalhit", "curl/",
    "python-requests", "axios/", "wget/", "go-http-client", "okhttp",
    "headlesschrome", "lighthouse", "uptime", "pingdom", "monitor",
)

_DEFAULT_FROM = "Case Pilot <onboarding@resend.dev>"


def _is_bot(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    if not ua:
        return True
    return any(s in ua for s in _BOT_SUBSTRINGS)


def _is_private_or_loopback(ip: str) -> bool:
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return True
    if ":" in ip:
        return False
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return True
    if a in (10, 127):
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 169 and b == 254:
        return True
    return False


def _extract_ip(request: Any) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip", "")
    if real:
        return real.strip()
    return request.client.host if request.client else ""


def _recipient() -> str:
    return os.environ.get("NOTIFY_TO_EMAIL", "")


def _from_address() -> str:
    return os.environ.get("NOTIFY_FROM_EMAIL") or _DEFAULT_FROM


async def _lookup_ip(ip: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(f"https://ipapi.co/{ip}/json/")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and not data.get("error"):
                    return data
    except Exception as e:
        print(f"[case-pilot] ipapi lookup failed for {ip}: {e}", flush=True)
    return {}


async def _send_via_resend(subject: str, body: str) -> dict[str, Any]:
    api_key = os.environ.get("RESEND_API_KEY", "")
    to = _recipient()
    sender = _from_address()
    if not api_key:
        return {"ok": False, "error": "RESEND_API_KEY not set"}
    if not to:
        return {"ok": False, "error": "NOTIFY_TO_EMAIL not set"}
    payload = {"from": sender, "to": [to], "subject": subject, "text": body}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
        if 200 <= r.status_code < 300:
            return {"ok": True, "id": r.json().get("id")}
        return {"ok": False, "error": f"HTTP {r.status_code}", "detail": r.text[:500]}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}


async def _notify(ip: str, user_agent: str, path: str, referer: str, host: str = "") -> None:
    info = await _lookup_ip(ip)
    org = info.get("org") or info.get("asn") or ""
    city = info.get("city") or ""
    region = info.get("region") or info.get("region_code") or ""
    country = info.get("country_name") or info.get("country") or ""
    location = ", ".join(p for p in (city, region, country) if p) or "unknown"

    label = org or location or ip
    full_url = f"https://{host}{path}" if host else path
    subject = f"[Case Pilot] visit from {label}"
    body = (
        "Case Pilot — icotec medical demo · new visitor.\n\n"
        f"URL:       {full_url}\n"
        f"IP:        {ip}\n"
        f"Location:  {location}\n"
        f"Org:       {org or 'unknown'}\n"
        f"Referer:   {referer or '(direct)'}\n"
        f"UA:        {user_agent or 'unknown'}\n"
    )
    result = await _send_via_resend(subject, body)
    if result.get("ok"):
        print(f"[case-pilot] visitor email sent: {subject}", flush=True)
    else:
        print(f"[case-pilot] visitor email failed: {result}", flush=True)


async def maybe_notify_visitor(request: Any, path: str) -> None:
    if os.environ.get("VISITOR_NOTIFY_ENABLED", "1") != "1":
        return
    ip = _extract_ip(request)
    if _is_private_or_loopback(ip):
        return
    ua = request.headers.get("user-agent", "")
    if _is_bot(ua):
        return
    now = time.time()
    last = _seen_ips.get(ip, 0)
    if now - last < _DEDUP_TTL_SEC:
        return
    _seen_ips[ip] = now
    if len(_seen_ips) > 2000:
        cutoff = now - _DEDUP_TTL_SEC
        for k in [k for k, v in _seen_ips.items() if v < cutoff]:
            _seen_ips.pop(k, None)
    referer = request.headers.get("referer", "")
    host = (
        request.headers.get("x-forwarded-host", "")
        or request.headers.get("host", "")
    )
    print(f"[case-pilot] visitor: queued notify for ip={ip}", flush=True)
    asyncio.create_task(_notify(ip, ua, path, referer, host))


def diagnostic_status() -> dict[str, Any]:
    rk = os.environ.get("RESEND_API_KEY")
    to = _recipient()
    return {
        "enabled": os.environ.get("VISITOR_NOTIFY_ENABLED", "1") == "1",
        "transport": "resend" if rk else "none",
        "resend_api_key_set": bool(rk),
        "notify_to_email_set": bool(to),
        "effective_from": _from_address(),
        "effective_to_email_domain": to.partition("@")[2] if to else "",
        "deduped_ip_count": len(_seen_ips),
    }


async def send_test_email() -> dict[str, Any]:
    return await _send_via_resend(
        subject="Case Pilot — visitor-notify test",
        body=(
            "Test from the Case Pilot deploy.\n\n"
            "If this arrived, notifications will fire on the next un-deduped page view."
        ),
    )
