import os
import discord
import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
import datetime  # pour les timestamps

# Variables Railway
TOKEN = os.environ['TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
URL_DEALABS = os.environ['URL_DEALABS']

# Intervalle le plus "humain" possible
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
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"⏱ [{timestamp}] 🔎 Démarrage d'une nouvelle recherche...")

            html = await fetch(session, URL_DEALABS)

            if not html:
                print(f"⏱ [{timestamp}] ⚠️ Pas de réponse, nouvelle tentative dans quelques secondes...")
                await asyncio.sleep(random.uniform(20, 40))
                continue

            soup = BeautifulSoup(html, "html.parser")

            # ---- NOUVEAU : Sélecteurs mis à jour Dealabs ----
            deal_selectors = [
                'a[data-testid="offer-title"]',
                'a[data-test="thread-title"]',
                'h3.dealTitle a'  # ancien format
            ]

            deals = []
            for selector in deal_selectors:
                found = soup.select(selector)
                deals.extend(found)

            # Supprimer les doublons potentiels
            deals = list(set(deals))

            print(f"⏱ [{timestamp}] Nombre de deals trouvés : {len(deals)}")

            # ---- Mélange pour éviter un pattern IA ----
            random.shuffle(deals)

            new_deals_count = 0
            for d in deals:
                try:
                    title = d.text.strip()
                    link = d.get("href")
                    url = f"https://www.dealabs.com{link}"

                    key = (title, link)
                    if key not in seen_deals:
                        seen_deals.add(key)
                        new_deals_count += 1

                        await channel.send(f"🔥 **Nouveau deal détecté !**\n{title}\n{url}")
                        print(f"✅ [{timestamp}] Nouveau deal : {title} -> {url}")

                except Exception as e:
                    print(f"❌ [{timestamp}] Erreur parsing deal : {e}")

            print(f"⏱ [{timestamp}] Total nouveaux deals envoyés : {new_deals_count}")

            # ---- Délai ultra naturel ----
            delay = random.uniform(MIN_INTERVAL, MAX_INTERVAL) + random.uniform(-2, 2)
            delay = max(10, delay)  # sécurité
            print(f"⏱ [{timestamp}] Prochain check dans {round(delay, 2)} sec…\n")

            await asyncio.sleep(delay)

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")
    asyncio.create_task(check_deals())

client.run(TOKEN)
