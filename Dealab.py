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
TOKEN = os.getenv("DISCORD_TOKEN")  # À mettre dans Railway
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))  # ID du salon Discord

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
    "Referer": "https://www.dealabs.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
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
            deals = soup.select("article a[href*='/bons-plans/']")

            print(f"➡️ Deals trouvés : {len(deals)}")

            new_deals = 0
            for d in deals:
                try:
                    # 🔹 URL propre
                    href = d.get("href")
                    url = href if href.startswith("http") else "https://www.dealabs.com" + href

                    # 🔹 Titre
                    title = d.select_one("h2")  # le titre principal dans l'article
                    title = title.get_text(strip=True) if title else "Pas de titre"

                    # 🔹 Commerçant / source
                    merchant = d.select_one(".deal-seller-name")
                    merchant = merchant.get_text(strip=True) if merchant else "Inconnu"

                    # 🔹 Image
                    img_tag = d.select_one("img")
                    img_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else None

                    # 🔹 Prix actuel
                    price_tag = d.select_one(".price")
                    price = price_tag.get_text(strip=True) if price_tag else "N/A"

                    # 🔹 Ancien prix / réduction
                    old_price_tag = d.select_one(".old-price")
                    old_price = old_price_tag.get_text(strip=True) if old_price_tag else None
                    discount_tag = d.select_one(".deal-discount")
                    discount = discount_tag.get_text(strip=True) if discount_tag else None

                    key = (title, url)
                    if key not in seen_deals:
                        seen_deals.add(key)
                        new_deals += 1

                        # 🔹 Embed Discord
                        embed = discord.Embed(title=title, url=url, color=0xff0000)
                        embed.add_field(name="Commerçant", value=merchant, inline=True)
                        embed.add_field(name="Prix", value=price, inline=True)
                        if old_price:
                            embed.add_field(name="Ancien prix", value=old_price, inline=True)
                        if discount:
                            embed.add_field(name="Réduction", value=discount, inline=True)
                        if img_url:
                            embed.set_image(url=img_url)
                        embed.set_footer(text=f"Détecté le {timestamp}")

                        await channel.send(embed=embed)
                        print(f"➡️ Envoyé : {title}")

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
