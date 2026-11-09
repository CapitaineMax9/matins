#!/usr/bin/env python3
"""Envoie sur Discord les rappels de messages Instagram arrivés à l'heure.

Lancé toutes les 5 minutes par GitHub Actions (.github/workflows/rappels.yml).
- Lit la configuration dans config/messages.json (modifiée par l'interface web).
- Retient dans state/sent.json ce qui a déjà été envoyé aujourd'hui,
  pour ne jamais envoyer deux fois le même rappel le même jour.

Variables d'environnement :
  DISCORD_WEBHOOK_URL  (obligatoire) URL du webhook Discord, stockée en secret GitHub.
  MODE                 "normal" (par défaut) ou "test" : envoie un message de test.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "messages.json"
STATE_PATH = ROOT / "state" / "sent.json"

# GitHub Actions peut lancer le workflow avec du retard (souvent 5 à 30 min).
# Au-delà de cette fenêtre après l'heure prévue, on n'envoie plus le rappel du jour.
SEND_WINDOW = timedelta(hours=2)
DISCORD_MAX_LEN = 2000
ALL_DAYS = [1, 2, 3, 4, 5, 6, 7]  # 1 = lundi … 7 = dimanche (ISO)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def scheduled_today(msg: dict, now: datetime) -> datetime | None:
    """Renvoie l'heure prévue aujourd'hui pour ce rappel, ou None s'il n'est pas prévu aujourd'hui."""
    hour, minute = (int(x) for x in str(msg["time"]).split(":"))
    if msg.get("type", "weekly") == "once":
        if msg.get("date") != now.date().isoformat():
            return None
    elif now.isoweekday() not in msg.get("days", ALL_DAYS):
        return None
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def escape_md(text: str) -> str:
    """Échappe les caractères de mise en forme Discord (ex. les _ des pseudos)."""
    for ch in "\\*_~`|>":
        text = text.replace(ch, "\\" + ch)
    return text


def post_discord(webhook: str, content: str) -> None:
    if len(content) > DISCORD_MAX_LEN:
        content = content[: DISCORD_MAX_LEN - 1] + "…"
    payload = json.dumps(
        {"content": content, "allowed_mentions": {"parse": []}}  # jamais de @everyone
    ).encode("utf-8")
    for attempt in range(3):
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "matins-rappels/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20):
                return
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < 2:  # limite de débit Discord : on patiente
                try:
                    wait = float(json.loads(err.read() or b"{}").get("retry_after", 2))
                except ValueError:
                    wait = 2
                time.sleep(min(wait, 10) + 0.5)
                continue
            raise RuntimeError(f"Discord a répondu HTTP {err.code}") from None


def clean_recipient(value: str) -> str:
    return str(value).strip().lstrip("@").strip()


def send_reminder(webhook: str, msg: dict, text: str) -> None:
    user = clean_recipient(msg["recipient"])
    header = (
        f"⏰ **{msg['time']}** · message Instagram pour **@{escape_md(user)}**\n"
        f"👉 Ouvrir la conversation : <https://ig.me/m/{user}>\n"
        f"📋 Le texte à copier est juste en dessous (appui long → Copier le texte)."
    )
    post_discord(webhook, header)
    post_discord(webhook, text)


def main() -> int:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        print("ERREUR : le secret DISCORD_WEBHOOK_URL n'est pas configuré (voir README).")
        return 1

    config = load_json(CONFIG_PATH, {"messages": []})
    tz = ZoneInfo(config.get("timezone") or "Europe/Paris")
    now = datetime.now(tz)
    messages = config.get("messages", [])

    if os.environ.get("MODE", "normal") == "test":
        active = sum(1 for m in messages if m.get("enabled", True))
        post_discord(
            webhook,
            f"✅ **Test réussi** : matins peut t'envoyer des rappels ici.\n"
            f"{active} rappel(s) actif(s) · heure actuelle : {now:%d/%m/%Y %H:%M} ({tz.key})",
        )
        print("Message de test envoyé.")
        return 0

    state = load_json(STATE_PATH, {})
    today = now.date().isoformat()
    changed = False
    errors = 0

    for msg in messages:
        mid = msg.get("id")
        if not mid or not msg.get("enabled", True):
            continue
        try:
            sched = scheduled_today(msg, now)
        except (KeyError, ValueError) as err:
            print(f"Rappel {mid} ignoré (configuration invalide : {err!r})")
            continue
        if sched is None or now < sched or now - sched > SEND_WINDOW:
            continue
        if state.get(mid, {}).get("last_sent") == today:
            continue
        texts = [t for t in msg.get("texts", []) if str(t).strip()]
        if not texts or not clean_recipient(msg.get("recipient", "")):
            print(f"Rappel {mid} ignoré (pas de texte ou pas de destinataire).")
            continue
        try:
            send_reminder(webhook, msg, random.choice(texts))
        except Exception as err:  # on continue avec les autres rappels
            errors += 1
            print(f"Échec de l'envoi du rappel {mid} : {err}")
            continue
        state[mid] = {"last_sent": today, "at": now.isoformat(timespec="minutes")}
        changed = True
        print(f"Rappel {mid} envoyé (prévu à {msg['time']}).")

    # Oublie l'historique des rappels supprimés de la configuration.
    known_ids = {m.get("id") for m in messages}
    for old_id in [k for k in state if k not in known_ids]:
        del state[old_id]
        changed = True

    if changed:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        print("Aucun rappel à envoyer pour le moment.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
