import os
import discord
import asyncio
import random
import datetime
from playwright.async_api import async_playwright

# Variables Railway
TOKEN = os.environ['TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
URL_DEALABS = os.environ['URL_DEALABS']

# Intervalle le plus "humain" possible
MIN_INTERVAL = float(os.environ.get('MIN_INTERVAL', 25))
MAX_INTERVAL = float(os.environ.get('MAX_INTERVAL', 40))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

seen_deals = set()

async def fetch_deals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # User-Agent aléatoire pour réduire le blocage
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Windows NT 6.1; WOW64)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X)",
            "Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X)",
            "Mozilla/5.0 (Android 13; Mobile)"
        ]
        await page.set_user_agent(random.choice(user_agents))

        await page.goto(URL_DEALABS)
        try:
            # Attendre que les deals apparaissent
            await page.wait_for_selector('a[data-testid="offer-title"]', timeout=7000)
        except:
            print("⚠️ Aucun deal trouvé sur la page")
            await browser.close()
            return []

        # Récupération de tous les deals
        deals_elements = await page.query_selector_all('a[data-testid="offer-title"]')
        deals = []
        for d in deals_elements:
            title = await d.inner_text()
            link = await d.get_attribute('href')
            if link:
                url = f"https://www.dealabs.com{link}"
                deals.append((title.strip(), url))

        await browser.close()
        return deals

async def check_deals():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel introuvable.")
        return

    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏱ [{timestamp}] 🔎 Démarrage d'une nouvelle recherche...")

        deals = await fetch_deals()

        if not deals:
            print(f"⏱ [{timestamp}] Aucun deal trouvé. Nouvelle tentative après délai.")
        else:
            # Mélange pour éviter pattern bot
            random.shuffle(deals)

            new_deals_count = 0
            for title, url in deals:
                key = (title, url)
                if key not in seen_deals:
                    seen_deals.add(key)
                    new_deals_count += 1
                    await channel.send(f"🔥 **Nouveau deal détecté !**\n{title}\n{url}")
                    print(f"✅ [{timestamp}] Nouveau deal : {title} -> {url}")

            print(f"⏱ [{timestamp}] Total nouveaux deals envoyés : {new_deals_count}")

        # Délai naturel entre deux checks
        delay = random.uniform(MIN_INTERVAL, MAX_INTERVAL) + random.uniform(-2, 2)
        delay = max(10, delay)
        print(f"⏱ [{timestamp}] Prochain check dans {round(delay, 2)} sec…\n")
        await asyncio.sleep(delay)

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")
    asyncio.create_task(check_deals())

client.run(TOKEN)
