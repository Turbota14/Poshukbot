import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from threading import Thread
from flask import Flask
import aiohttp
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

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

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ Не вдалося отримати дані: {response.status}")
                return
            data = await response.json()

        members = data.get("members", [])

        for member in members:
            char = member["character"]
            name = char["name"]
            realm = char.get("realm", "")
            api_url = f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={name}&fields=mythic_plus_recent_runs"

            try:
                async with session.get(api_url) as char_response:
                    if char_response.status != 200:
                        continue
                    char_data = await char_response.json()
            except Exception as e:
                print(f"⚠️ Помилка при запиті до {name}: {e}")
                continue

            runs = char_data.get("mythic_plus_recent_runs", [])
            for run in runs:
                run_id = run.get("run_id")
                if not run_id or run_id in checked_runs:
                    continue

                checked_runs.add(run_id)
                flagged_players = []

                for player in run.get("roster", []):
                    player_info = player.get("character", {})
                    player_name = player_info.get("name", "")
                    player_realm = player_info.get("realm", "").lower()
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
logging.info(
    f"Новий ключ:\n"
    f"Ключ: {keystone['dungeon']} +{keystone['key_level']}\n"
    f"Гравці: {', '.join(player['name'] for player in keystone['members'])}\n"
    f"Час: {datetime.utcnow()} UTC\n"
    f"Сумнівні: {', '.join(suspicious_players) if suspicious_players else 'немає'}"
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
