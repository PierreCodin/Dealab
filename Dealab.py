import discord
import asyncio
import random
from discord.ext import tasks
from playwright.async_api import async_playwright
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================
DISCORD_TOKEN = "TON_TOKEN_ICI"
CHANNEL_ID = 000000000000000  # <-- Mets l'ID du channel Discord

URL_DEALABS = "https://www.dealabs.com/nouveaux"
CHECK_INTERVAL = 35  # secondes

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# pour éviter de renvoyer plusieurs fois les mêmes deals
deals_envoyes = set()

# ==========================
# DISCORD CLIENT
# ==========================

intents = discord.Intents.default()
client = discord.Client(intents=intents)


# ==========================
# SCRAPPING DEALABS (Playwright)
# ==========================
async def fetch_deals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # tu peux passer à False en local si tu veux voir
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

        # Attendre que les deals chargent
        await page.wait_for_selector("article[data-qa='thread-item']", timeout=10000)

        # Extraire les deals
        elements = await page.query_selector_all("article[data-qa='thread-item']")

        deals = []
        for el in elements:
            titre = await el.query_selector("a[data-qa='thread-title-link']")
            prix = await el.query_selector("span[data-qa='thread-price']")
            lien = await el.query_selector("a[data-qa='thread-title-link']")

            if not titre or not lien:
                continue

            t = await titre.inner_text()
            url = await lien.get_attribute("href")
            url = "https://www.dealabs.com" + url

            p = await prix.inner_text() if prix else "Prix inconnu"

            deals.append({
                "titre": t.strip(),
                "prix": p.strip(),
                "lien": url
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
                description=f"💰 **{d['prix']}**",
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
