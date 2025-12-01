import os
import asyncio
import random
import datetime
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from playwright.async_api import async_playwright

# ========================
# 🔐 Variables d'environnement
# ========================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

URL = "https://www.dealabs.com/groupe/erreur-de-prix"
MIN_INTERVAL = 20
MAX_INTERVAL = 40

seen_deals = set()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# 🌐 Fetch page Dealabs via Playwright
# ========================
async def fetch(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)  # 30s max
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print("⚠️ Fetch error (Playwright):", e)
        return None

# ========================
# 🔎 Boucle de recherche
# ========================
async def check_deals(channel):
    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏱ [{timestamp}] 🔎 Nouvelle recherche…")

        html = await fetch(URL)
        if not html:
            print("⚠️ Aucune réponse de Dealabs.")
            await asyncio.sleep(random.uniform(10, 20))
            continue

        soup = BeautifulSoup(html, "html.parser")
        deals = soup.select("article a[href*='/bons-plans/']")
        print(f"➡️ Deals trouvés : {len(deals)}")

        new_deals = 0
        for d in deals:
            try:
                title = d.get_text(strip=True)
                url = "https://www.dealabs.com" + d["href"]

                key = (title, url)
                if key not in seen_deals:
                    seen_deals.add(key)
                    new_deals += 1
                    await channel.send(f"🔥 **Nouveau deal détecté !**\n**{title}**\n{url}")
                    print(f"➡️ envoyé : {title}")

            except Exception as e:
                print("❌ Erreur parsing deal :", e)

        print(f"📩 Nouveaux deals envoyés : {new_deals}")
        delay = max(10, random.uniform(MIN_INTERVAL, MAX_INTERVAL))
        print(f"⏳ Prochain check dans {round(delay, 2)} sec…\n")
        await asyncio.sleep(delay)

# ========================
# 🚀 Démarrage du bot
# ========================
@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ ERREUR : Impossible de trouver le salon. Vérifie DISCORD_CHANNEL_ID.")
        return
    bot.loop.create_task(check_deals(channel))

# ========================
# 🔐 Lancement du bot
# ========================
bot.run(TOKEN)
