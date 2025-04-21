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

def has_cyrillic(text):
    return any('\u0400' <= c <= '\u04FF' for c in text)

@bot.event
async def on_ready():
    print(f'✅ Бот запущено як {bot.user}')
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Бот запущено! Готовий до моніторингу гільдії.")
    monitor_guild.start()

@tasks.loop(minutes=5)
async def monitor_guild():
    print("🔍 Перевірка гільдії...")
    url = f"https://raider.io/api/v1/guilds/profile?region=eu&realm={REALM}&name={GUILD_NAME}&fields=members"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        members = data.get("members", [])

        flagged = []
        for member in members:
            char = member["character"]
            name = char["name"]
            realm = char.get("realm", "").lower()

            if has_cyrillic(name) or "ru" in realm:
                flagged.append(f"{name} ({realm})")

        if flagged:
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                mention = f"<@&{OFFICER_ROLE_ID}>"
                flagged_list = ", ".join(flagged)
                await channel.send(
                    f"🚨 У гільдії {GUILD_NAME} на {REALM} знайдено підозрілі імена або RU реалми: {flagged_list}. {mention}"
                )
    else:
        print(f"❌ Не вдалося отримати дані: {response.status_code}")

# ===== Flask Web Server для Render =====
app = Flask('')

@app.route('/')
def home():
    return "Бот працює! 🟢"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Запуск бота
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
