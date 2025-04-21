import os
import discord
from discord.ext import commands, tasks
import requests
from dotenv import load_dotenv
from threading import Thread
from flask import Flask

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = False

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_NAME = "MRIYA"
REALM = "Silvermoon"
OFFICER_ROLE_ID = 968091538053816320
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

checked_runs = set()

def has_cyrillic(text):
    return any('\u0400' <= c <= '\u04FF' for c in text)

@bot.event
async def on_ready():
    print(f'✅ Бот запущено як {bot.user}')
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Бот запущено! Готовий до моніторингу гільдії.")
    monitor_mplus_runs.start()

@tasks.loop(minutes=5)
async def monitor_mplus_runs():
    print("🔍 Перевірка останніх M+ ключів...")
    url = f"https://raider.io/api/v1/guilds/profile?region=eu&realm={REALM}&name={GUILD_NAME}&fields=members"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Не вдалося отримати дані: {response.status_code}")
        return

    data = response.json()
    members = data.get("members", [])

    for member in members:
        char = member["character"]
        name = char["name"]
        realm = char.get("realm", "")
        api_url = f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={name}&fields=mythic_plus_recent_runs"
        char_response = requests.get(api_url)

        if char_response.status_code != 200:
            continue

        char_data = char_response.json()
        runs = char_data.get("mythic_plus_recent_runs", [])

        for run in runs:
            run_id = run.get("run_id")
            if not run_id or run_id in checked_runs:
                continue

            checked_runs.add(run_id)
            flagged_players = []

            for player in run.get("roster", []):
                player_name = player.get("character", {}).get("name", "")
                player_realm = player.get("character", {}).get("realm", "").lower()
                if has_cyrillic(player_name) or "ru" in player_realm:
                    flagged_players.append(f"{player_name} ({player_realm})")

            if flagged_players:
                channel = bot.get_channel(DISCORD_CHANNEL_ID)
                if channel:
                    mention = f"<@&{OFFICER_ROLE_ID}>"
                    dungeon = run.get("dungeon", "Невідомо")
                    level = run.get("mythic_level", "?")
                    await channel.send(
                        f"🚨 У ключі {dungeon} +{level} знайдено підозрілих гравців: {', '.join(flagged_players)}. {mention}"
                    )

# ===== Flask Web Server для Render =====
app = Flask('')

@app.route('/')
def home():
    return "Бот працює! 🟢"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Запуск Discord-бота
bot.run(os.getenv("DISCORD_BOT_TOKEN"))