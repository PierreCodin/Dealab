import discord
import asyncio
import random
import os
from discord.ext import tasks
from playwright.async_api import async_playwright
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

URL_DEALABS = "https://www.dealabs.com/groupe/erreur-de-prix"
CHECK_INTERVAL = 35  # secondes

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

deals_envoyes = set()

# ==========================
# DISCORD CLIENT
# ==========================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ==========================
# SCRAPING DEALABS (Playwright)
# ==========================
async def fetch_deals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # voir le navigateur pour debug
            args=["--no-sandbox"]
        )
        page = await browser.new_page()

        # Anti-bot
        await page.set_user_agent(random.choice(user_agents))
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.evaluate(
            "() => { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}) }"
        )

        await page.goto(URL_DEALABS, timeout=60000)
        await page.wait_for_timeout(5000)  # attendre 5s pour que le JS charge

        try:
            await page.wait_for_selector("a.thread-title--list.js-thread-title", timeout=30000)
        except:
            print("⚠️ Aucun deal trouvé sur la page")
            html = await page.content()
            print(html[:2000])  # debug: premiers 2000 caractères du HTML
            await browser.close()
            return []

        elements = await page.query_selector_all("a.thread-title--list.js-thread-title")
        deals = []

        for el in elements:
            titre = await el.inner_text()
            lien = await el.get_attribute("href")
            if lien:
                deals.append({
                    "titre": titre.strip(),
                    "lien": lien
                })

        await browser.close()
        return deals

# ==========================
# TÂCHE AUTOMATIQUE
# ==========================
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_deals():
    channel = client.get_channel(CHANNEL_ID)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"⏱ [{now}] 🔎 Démarrage d'une nouvelle recherche...")

    deals = await fetch_deals()
    print(f"⏱ [{now}] Nombre de deals trouvés : {len(deals)}")

    nouveaux = 0
    for d in deals:
        if d["lien"] not in deals_envoyes:
            deals_envoyes.add(d["lien"])
            nouveaux += 1

            embed = discord.Embed(
                title=d["titre"],
                url=d["lien"],
                color=0x00FF00
            )
            await channel.send(embed=embed)

    print(f"⏱ [{now}] Total nouveaux deals envoyés : {nouveaux}")
    print(f"⏱ [{now}] Prochain check dans {CHECK_INTERVAL} sec…")

# ==========================
# DÉMARRAGE DU BOT
# ==========================
@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")
    await asyncio.sleep(2)
    check_deals.start()

client.run(DISCORD_TOKEN)
