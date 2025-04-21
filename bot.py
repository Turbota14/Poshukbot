import discord
from discord.ext import commands, tasks
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

GUILD_NAME = "MRIYA"
REALM = "Silvermoon"
REGION = "eu"

RUSSIAN_REALMS = [
    "Гордунни", "Ревущий фьорд", "Свежеватель Душ",
    "Ясеневый лес", "Пиратская бухта", "Азурегос", "Разувий",
    "Термоштепсель", "Галакронд", "Дракономор", "Черный Шрам"
]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    monitor_keys.start()

@tasks.loop(minutes=5)
async def monitor_keys():
    channel = bot.get_channel(CHANNEL_ID)
    print("🔍 Checking keys...")

    url = f"https://raider.io/api/v1/guilds/profile?region={REGION}&realm={REALM}&name={GUILD_NAME}&fields=mythic_plus_recent_runs"
    response = requests.get(url)

    if response.status_code != 200:
        await channel.send("⚠️ Raider.IO API unavailable")
        return

    data = response.json()
    runs = data.get("mythic_plus_recent_runs", [])

    flagged_runs = []

    for run in runs:
        for player in run.get("roster", []):
            char = player.get("character", {})
            name = char.get("name", "")
            realm = char.get("realm", "")

            if realm in RUSSIAN_REALMS or re.search(r'[а-яА-ЯёЁ]', name):
                flagged_runs.append({
                    "dungeon": run.get("dungeon"),
                    "level": run.get("mythic_level"),
                    "url": run.get("url"),
                    "offender": f"{name}-{realm}"
                })
                break

    if flagged_runs:
        msg = f"🚨 **Знайдено підозрілих гравців у M+ ключах!** <@&968091538053816320>"
        for f in flagged_runs:
            msg += f"\n🔸 [{f['dungeon']} +{f['level']}]({f['url']}) — `{f['offender']}`"
        await channel.send(msg)
    else:
        print("✅ No suspicious players found.")

bot.run(TOKEN)
