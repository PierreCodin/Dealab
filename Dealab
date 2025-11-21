import os
import discord
import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup

# Variables Railway
TOKEN = os.environ['TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
URL_DEALABS = os.environ['URL_DEALABS']

# Intervalle le plus "humaine possible"
MIN_INTERVAL = float(os.environ.get('MIN_INTERVAL', 25))
MAX_INTERVAL = float(os.environ.get('MAX_INTERVAL', 40))

# User-Agents très variés
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X)",
    "Mozilla/5.0 (Android 13; Mobile)",
    "Mozilla/5.0 (Android 12; Tablet)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.6; rv:90.0)"
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

seen_deals = set()

async def fetch(session, url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": random.choice([
            "fr-FR,fr;q=0.9",
            "fr-FR,fr;q=0.8,en-US;q=0.5",
            "en-US,en;q=0.9"
        ]),
        "Cache-Control": random.choice(["no-cache", "max-age=0", "no-store"]),
        "Pragma": random.choice(["no-cache", ""]),
        "DNT": random.choice(["1", "0"])
    }

    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status in [429, 503]:
                print("⚠️ Dealabs throttle → pause 20 sec…")
                await asyncio.sleep(20)
                return None

            return await resp.text()

    except Exception as e:
        print(f"Erreur HTTP : {e}")
        return None

async def check_deals():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel introuvable.")
        return

    async with aiohttp.ClientSession() as session:
        while True:
            html = await fetch(session, URL_DEALABS)

            if not html:
                await asyncio.sleep(random.uniform(20, 40))
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Randomize l'ordre pour éviter un pattern IA
            deals = soup.select("h3.dealTitle a")
            random.shuffle(deals)

            for d in deals:
                try:
                    title = d.text.strip()
                    link = d.get("href")
                    url = f"https://www.dealabs.com{link}"

                    key = (title, link)
                    if key not in seen_deals:
                        seen_deals.add(key)
                        await channel.send(f"🔥 **Nouveau deal détecté !**\n{title}\n{url}")

                except Exception as e:
                    print("Erreur parsing deal :", e)

            # Délai ultra naturel (pas de pattern)
            delay = random.uniform(MIN_INTERVAL, MAX_INTERVAL) + random.uniform(-2, 2)
            delay = max(10, delay)  # sécurité
            print(f"⏳ Prochain check dans {round(delay, 2)} sec…")

            await asyncio.sleep(delay)

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")
    asyncio.create_task(check_deals())

client.run(TOKEN)
