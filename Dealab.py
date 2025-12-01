import os
import asyncio
import datetime
import random
from playwright.async_api import async_playwright
import discord
from discord.ext import commands

# ========================
# 🔐 Variables d'environnement
# ========================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
URL = "https://www.dealabs.com/groupe/erreur-de-prix"

seen_deals = set()

# ========================
# 🔐 Intents Discord (avec message_content activé)
# ========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# 🔎 Fonction pour récupérer les deals
# ========================
async def fetch_deals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        deals = await page.query_selector_all("article.thread")
        results = []

        for deal in deals:
            expired = await deal.query_selector(".thread-expired")
            if expired:
                continue

            title_el = await deal.query_selector("h2.thread-title a")
            if not title_el:
                continue
            title = await title_el.inner_text()
            href = await title_el.get_attribute("href")
            url = f"https://www.dealabs.com{href}"

            merchant_el = await deal.query_selector(".merchant-name")
            merchant = await merchant_el.inner_text() if merchant_el else "Inconnu"

            price_el = await deal.query_selector(".thread-price span.price")
            current_price = await price_el.inner_text() if price_el else "N/A"
            old_price_el = await deal.query_selector(".thread-price .old-price")
            old_price = await old_price_el.inner_text() if old_price_el else "N/A"
            discount_el = await deal.query_selector(".thread-price .reduction")
            discount = await discount_el.inner_text() if discount_el else "N/A"

            image_el = await deal.query_selector("img.thread-image")
            image_url = await image_el.get_attribute("data-src") if image_el else None

            results.append({
                "title": title.strip(),
                "url": url,
                "merchant": merchant.strip(),
                "current_price": current_price.strip(),
                "old_price": old_price.strip(),
                "discount": discount.strip(),
                "image": image_url
            })

        await browser.close()
        return results

# ========================
# 🔎 Boucle de check
# ========================
async def check_loop(channel):
    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scan_msg = f"⏱ [{timestamp}] 🔎 Nouvelle recherche…"
        print(scan_msg)
        await channel.send(scan_msg)  # <-- envoie l'heure de chaque scan sur Discord

        try:
            deals = await fetch_deals()
            new_deals = 0
            for deal in deals:
                key = (deal["title"], deal["url"])
                if key in seen_deals:
                    continue
                seen_deals.add(key)
                new_deals += 1

                msg = (
                    f"🔥 **Nouveau deal détecté !**\n"
                    f"**{deal['title']}**\n"
                    f"Commerçant : {deal['merchant']}\n"
                    f"Prix : {deal['current_price']} | Ancien prix : {deal['old_price']} | Réduction : {deal['discount']}\n"
                    f"URL : {deal['url']}\n"
                )
                if deal["image"]:
                    msg += f"Image : {deal['image']}"

                await channel.send(msg)
                print(f"➡️ Envoyé : {deal['title']}")

            print(f"📩 Nouveaux deals envoyés : {new_deals}")

        except Exception as e:
            print("❌ Erreur lors de la récupération des deals :", e)

        # ⏱ Délai aléatoire entre 20 et 40 secondes
        delay = random.randint(20, 40)
        print(f"⏳ Prochain scan dans {delay} secondes…")
        await asyncio.sleep(delay)

# ========================
# 🚀 Bot Discord
# ========================
@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ ERREUR : Impossible de trouver le salon Discord. Vérifie DISCORD_CHANNEL_ID.")
        return
    bot.loop.create_task(check_loop(channel))

bot.run(TOKEN)
