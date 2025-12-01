import os
import asyncio
import random
import datetime
import aiohttp
from bs4 import BeautifulSoup
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
# 🌐 Headers pour Dealabs
# ========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ========================
# 🌐 Fetch page Dealabs
# ========================
async def fetch(session, url):
    try:
        async with session.get(url, timeout=20, headers=HEADERS) as resp:
            if resp.status == 200:
                return await resp.text()
            print(f"⚠️ HTTP status: {resp.status}")
            return None
    except Exception as e:
        print("⚠️ Fetch error:", e)
        return None

# ========================
# 🔎 Boucle de recherche
# ========================
async def check_deals(channel):
    async with aiohttp.ClientSession() as session:
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"⏱ [{timestamp}] 🔎 Nouvelle recherche…")

            html = await fetch(session, URL)
            if not html:
                print("⚠️ Aucune réponse de Dealabs.")
                await asyncio.sleep(random.uniform(10, 20))
                continue

            soup = BeautifulSoup(html, "html.parser")
            articles = soup.select("article.thread")  # tous les deals
            print(f"➡️ Articles trouvés : {len(articles)}")

            new_deals = 0
            for article in articles:
                try:
                    # Ignorer si deal expiré
                    if article.select_one(".thread-expired"):
                        continue

                    # Titre
                    title_tag = article.select_one("h2.thread-title a")
                    title = title_tag.get_text(strip=True) if title_tag else "Pas de titre"

                    # URL
                    url = "https://www.dealabs.com" + title_tag["href"] if title_tag else URL

                    # Commerçant
                    merchant_tag = article.select_one(".merchant-name")
                    merchant = merchant_tag.get_text(strip=True) if merchant_tag else "Inconnu"

                    # Prix actuel
                    price_tag = article.select_one(".thread-price span.price")
                    current_price = price_tag.get_text(strip=True) if price_tag else "N/A"

                    # Ancien prix
                    old_price_tag = article.select_one(".thread-price .old-price")
                    old_price = old_price_tag.get_text(strip=True) if old_price_tag else "N/A"

                    # Réduction
                    discount_tag = article.select_one(".thread-price .reduction")
                    discount = discount_tag.get_text(strip=True) if discount_tag else "N/A"

                    # Image
                    image_tag = article.select_one("img.thread-image")
                    image_url = image_tag["data-src"] if image_tag and image_tag.has_attr("data-src") else None

                    key = (title, url)
                    if key not in seen_deals:
                        seen_deals.add(key)
                        new_deals += 1

                        message = f"🔥 **Nouveau deal détecté !**\n**{title}**\n"
                        message += f"Commerçant : {merchant}\n"
                        message += f"Prix : {current_price} | Ancien prix : {old_price} | Réduction : {discount}\n"
                        message += f"URL : {url}\n"
                        if image_url:
                            message += f"Image : {image_url}"

                        await channel.send(message)
                        print(f"➡️ Envoyé : {title}")

                except Exception as e:
                    print("❌ Erreur parsing deal :", e)

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
