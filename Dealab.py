import os
import asyncio
import random
import datetime
from playwright.async_api import async_playwright
import discord
from discord.ext import commands

# ========================
# 🔐 Variables d'environnement
# ========================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

URL = "https://www.dealabs.com/groupe/erreur-de-prix"
MIN_INTERVAL = 20
MAX_INTERVAL = 40

seen_deals = set()

# ========================
# 🔐 Intents Discord
# ========================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# 🔎 Fonction pour récupérer les deals
# ========================
async def fetch_deals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_selector("article.thread")  # attendre que les deals chargent

        articles = await page.query_selector_all("article.thread")
        deals_list = []

        for a in articles:
            expired = await a.query_selector(".thread-expired")
            if expired:
                continue  # ignorer les deals expirés

            title = await a.query_selector_eval("h2.thread-title a", "el => el.textContent") if await a.query_selector("h2.thread-title a") else "Pas de titre"
            url = await a.query_selector_eval("h2.thread-title a", "el => el.href") if await a.query_selector("h2.thread-title a") else URL
            merchant = await a.query_selector_eval(".merchant-name", "el => el.textContent") if await a.query_selector(".merchant-name") else "Inconnu"
            price = await a.query_selector_eval(".thread-price span.price", "el => el.textContent") if await a.query_selector(".thread-price span.price") else "N/A"
            old_price = await a.query_selector_eval(".thread-price .old-price", "el => el.textContent") if await a.query_selector(".thread-price .old-price") else "N/A"
            discount = await a.query_selector_eval(".thread-price .reduction", "el => el.textContent") if await a.query_selector(".thread-price .reduction") else "N/A"
            image = await a.query_selector_eval("img.thread-image", "el => el.src") if await a.query_selector("img.thread-image") else None

            deals_list.append({
                "title": title.strip(),
                "url": url.strip(),
                "merchant": merchant.strip(),
                "price": price.strip(),
                "old_price": old_price.strip(),
                "discount": discount.strip(),
                "image": image.strip() if image else None
            })

        await browser.close()
        return deals_list

# ========================
# 🔎 Boucle de recherche
# ========================
async def check_deals(channel):
    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏱ [{timestamp}] 🔎 Nouvelle recherche…")

        try:
            deals = await fetch_deals()
        except Exception as e:
            print("⚠️ Erreur fetch deals:", e)
            await asyncio.sleep(random.uniform(10, 20))
            continue

        new_deals = 0
        for d in deals:
            key = (d["title"], d["url"])
            if key not in seen_deals:
                seen_deals.add(key)
                new_deals += 1

                message = f"🔥 **Nouveau deal détecté !**\n**{d['title']}**\n"
                message += f"Commerçant : {d['merchant']}\n"
                message += f"Prix : {d['price']} | Ancien prix : {d['old_price']} | Réduction : {d['discount']}\n"
                message += f"URL : {d['url']}\n"
                if d["image"]:
                    message += f"Image : {d['image']}"

                await channel.send(message)
                print(f"➡️ Envoyé : {d['title']}")

        print(f"📩 Nouveaux deals envoyés : {new_deals}")
        delay = max(10, random.uniform(MIN_INTERVAL, MAX_INTERVAL))
        print(f"⏳ Prochain check dans {round(delay,2)} sec…\n")
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
