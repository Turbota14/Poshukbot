import discord
from discord.ext import tasks, commands
import aiohttp
import asyncio
import logging
from flask import Flask
from threading import Thread
from datetime import datetime

TOKEN = "MTM2Mzg0MjM5NDE5MzEzNzc4NQ.GgSKaj.fc6RBABlwonoRL_dfLkB5TBddCCXOyJANx93xE"
GUILD_NAME = "MRIYA"
REALM = "Silvermoon"
OFFICER_ROLE_ID = 968091538053816320
CHECK_INTERVAL = 300  # 5 хв

app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

seen_runs = set()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    check_mplus_runs.start()

def has_cyrillic(text):
    return any('а' <= char <= 'я' or 'А' <= char <= 'Я' for char in text)

async def fetch_keystones():
    url = f"https://raider.io/api/v1/guilds/profile?region=eu&realm={REALM}&name={GUILD_NAME}&fields=members"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data.get("members", [])

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_mplus_runs():
    channel = discord.utils.get(bot.get_all_channels(), name="general")  # або твій канал
    if not channel:
        print("Канал не знайдено")
        return

    members = await fetch_keystones()
    for member in members:
        char = member.get("character", {})
        name = char.get("name")
        realm = char.get("realm")
        url = f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={name}&fields=mythic_plus_recent_runs"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    continue
                data = await response.json()
                runs = data.get("mythic_plus_recent_runs", [])
                for run in runs:
                    run_id = f"{run['dungeon']}+{run['mythic_level']}-{run['completed_at']}"
                    if run_id in seen_runs:
                        continue
                    seen_runs.add(run_id)

                    party = run.get("party", [])
                    player_names = [p['character']['name'] for p in party]
                    player_realms = [p['character']['realm'] for p in party]
                    suspicious_players = [
                        f"{p['character']['name']} ({p['character']['realm']})"
                        for p in party
                        if has_cyrillic(p['character']['name']) or ".ru" in p['character']['realm'].lower() or "-ru" in p['character']['realm'].lower()
                    ]

                    # 📝 Лог кожного ключа
                    logging.info(
                        f"Новий ключ:\n"
                        f"{run['dungeon']} +{run['mythic_level']}, "
                        f"{', '.join(player_names)}\n"
                        f"Сумнівні: {', '.join(suspicious_players) if suspicious_players else 'немає'}"
                    )

                    # Якщо є підозрілі — надсилаємо в Discord
                    if suspicious_players:
                        message = (
                            f"🕵️ Знайдено RU-гравця або кирилицю у ключі!\n"
                            f"Ключ: {run['dungeon']} +{run['mythic_level']}\n"
                            f"Гравці: {', '.join(player_names)}\n"
                            f"Сумнівні: {', '.join(suspicious_players)}"
                        )
                        await channel.send(f"<@&{OFFICER_ROLE_ID}>\n{message}")
                        logging.info(f"🔔 {message}")

keep_alive()
bot.run(TOKEN)
