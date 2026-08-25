"""Acumen User Profile - Persistent memory about the user across conversations."""

import json
from pathlib import Path
from acumen.core.config import DATA_DIR
from acumen.core.logger import get_logger

logger = get_logger("acumen.memory.profile")

PROFILE_PATH = DATA_DIR / "user_profile.json"

def load_profile():
    if PROFILE_PATH.exists():
        return json.loads(PROFILE_PATH.read_text())
    return {"facts": [], "preferences": {}, "projects": [], "name": ""}

def save_profile(profile):
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))

def add_fact(fact):
    profile = load_profile()
    if fact not in profile["facts"]:
        profile["facts"].append(fact)
        save_profile(profile)
        logger.info(f"User fact saved: {fact[:50]}")

def set_preference(key, value):
    profile = load_profile()
    profile["preferences"][key] = value
    save_profile(profile)

def set_name(name):
    profile = load_profile()
    profile["name"] = name
    save_profile(profile)

def add_project(project):
    profile = load_profile()
    if project not in profile["projects"]:
        profile["projects"].append(project)
        save_profile(profile)

def get_profile_context():
    profile = load_profile()
    parts = []
    if profile["name"]:
        parts.append(f"User's name: {profile['name']}")
    if profile["facts"]:
        parts.append("Known facts: " + "; ".join(profile["facts"][-10:]))
    if profile["projects"]:
        parts.append("Active projects: " + ", ".join(profile["projects"][-5:]))
    if profile["preferences"]:
        prefs = ", ".join(f"{k}: {v}" for k, v in list(profile["preferences"].items())[-5:])
        parts.append(f"Preferences: {prefs}")
    return "\n".join(parts) if parts else ""

def extract_user_info(message, response):
    """Auto-extract user info from conversations."""
    msg_lower = message.lower()
    if "my name is " in msg_lower:
        name = message.split("my name is ")[-1].split(".")[0].split(",")[0].strip()
        if name and len(name) < 30:
            set_name(name)
    if "i'm working on " in msg_lower or "i am working on " in msg_lower:
        project = message.split("working on ")[-1].split(".")[0].strip()
        if project and len(project) < 100:
            add_project(project)
    if "i prefer " in msg_lower or "i like " in msg_lower:
        for trigger in ["i prefer ", "i like "]:
            if trigger in msg_lower:
                pref = message.split(trigger)[-1].split(".")[0].strip()
                if pref and len(pref) < 100:
                    add_fact(pref)