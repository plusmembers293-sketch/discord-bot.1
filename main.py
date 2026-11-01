import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
from threading import Thread
from flask import Flask

# ==========================================
# 7/24 AKTİF TUTMA (KEEP-ALIVE WEB SERVER)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot 7/24 Aktif ve Çalışıyor!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ==========================================
# BOT APPARATUS & INTENTS SETUP
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Üye yönetimi ve ban/kick/mute için gereklidir
intents.moderation = True

class ModerationBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # Özel yardım komutu kullanacağız
        )

    async def setup_hook(self):
        # Slash (/) komutlarını Discord API'ye senkronize eder
        print("Slash komutları senkronize ediliyor...")
        await self.tree.sync()
        print("Slash komutları başarıyla senkronize edildi!")

bot = ModerationBot()

# Basit bellek içi Uyarı (Warn) veritabanı (Sunucu ID -> Üye ID -> [Uyarılar])
warn_database = {}

# ==========================================
# BOT EVENTLARI (OLAYLAR)
# ==========================================
@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"Bot Başarıyla Giriş Yaptı!")
    print(f"Bot Kullanıcı Adı: {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print("----------------------------------------")
    
    # Bot Durumu (Activity)
    activity = discord.Activity(
        type=discord.ActivityType.watching, 
        name="Sunucu Güvenliğini | /yardim"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """Geleneksel prefix komut hatalarını yakalar"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Hata:** Bu komutu kullanmak için yetkiniz yetersiz!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Hata:** Eksik argüman girdiniz. Kullanım için `!yardim` yazabilirsiniz.")
    else:
        print(f"Hata oluştu: {error}")

# ==========================================
# MODERASYON KOMUTLARI (SLASH & PREFIX)
# ==========================================

# 1. KULLANICI YASAKLAMA (BAN)
@bot.hybrid_command(name="ban", description="Belirtilen kullanıcıyı sunucudan yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, uye: discord.Member, *, sebep: str = "Sebep belirtilmedi."):
    """Kullanıcıyı sunucudan yasaklar."""
    try:
        if uye.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ Sizden yüksek veya aynı roldeki birini yasaklayamazsınız!")
            return
            
        await uye.ban(reason=f"{ctx.author} tarafından: {sebep}")
        
        embed = discord.Embed(
            title="🔨 Kullanıcı Yasaklandı",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Yasaklanan:", value=f"{uye.mention} ({uye.id})", inline=False)
        embed.add_field(name="Yetkili:", value=ctx.author.mention, inline=False)
        embed.add_field(name="Sebep:", value=sebep, inline=False)
        embed.set_thumbnail(url=uye.display_avatar.url if uye.display_avatar else None)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ İşlem başarısız: {str(e)}")

# 2. KULLANICI ATMA (KICK)
@bot.hybrid_command(name="kick", description="Belirtilen kullanıcıyı sunucudan atar.")
@app_commands.checks.has_permissions(kick_members=True)
@commands.has_permissions(kick_members=True)
async def kick(ctx: commands.Context, uye: discord.Member, *, sebep: str = "Sebep belirtilmedi."):
    """Kullanıcıyı sunucudan atar."""
    try:
        if uye.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ Sizden yüksek veya aynı roldeki birini sunucudan atamazsınız!")
            return
            
        await uye.kick(reason=f"{ctx.author} tarafından: {sebep}")
        
        embed = discord.Embed(
            title="👢 Kullanıcı Atıldı",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Atılan:", value=f"{uye.mention} ({uye.id})", inline=False)
        embed.add_field(name="Yetkili:", value=ctx.author.mention, inline=False)
        embed.add_field(name="Sebep:", value=sebep, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ İşlem başarısız: {str(e)}")

# 3. ZAMAN AŞIMI / MUTE (TIMEOUT)
@bot.hybrid_command(name="mute", description="Kullanıcıya geçici süreyle zamanaşımı (mute) uygular.")
@app_commands.checks.has_permissions(moderate_members=True)
@commands.has_permissions(moderate_members=True)
async def mute(ctx: commands.Context, uye: discord.Member, dakika: int, *, sebep: str = "Sebep belirtilmedi."):
    """Kullanıcıyı belirtilen dakika kadar susturur."""
    try:
        if uye.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ Sizden yüksek veya aynı roldeki birini susturamazsınız!")
            return

        sure = datetime.timedelta(minutes=dakika)
        await uye.timeout(sure, reason=f"{ctx.author} tarafından: {sebep}")
        
        embed = discord.Embed(
            title="🔇 Kullanıcı Susturuldu (Timeout)",
            color=discord.Color.dark_grey(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Susturulan:", value=uye.mention, inline=True)
        embed.add_field(name="Süre:", value=f"{dakika} Dakika", inline=True)
        embed.add_field(name="Yetkili:", value=ctx.author.mention, inline=False)
        embed.add_field(name="Sebep:", value=sebep, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Mute işlemi başarısız: {str(e)}")

# 4. MUTE KALDIRMA (UNMUTE)
@bot.hybrid_command(name="unmute", description="Kullanıcının zamanaşımını (mute) kaldırır.")
@app_commands.checks.has_permissions(moderate_members=True)
@commands.has_permissions(moderate_members=True)
async def unmute(ctx: commands.Context, uye: discord.Member):
    """Kullanıcının mutesini kaldırır."""
    try:
        await uye.timeout(None)
        await ctx.send(f"🔊 {uye.mention} kullanıcısının susturulması kaldırıldı.")
    except Exception as e:
        await ctx.send(f"❌ Unmute işlemi başarısız: {str(e)}")

# 5. MESAJ TEMİZLEME (CLEAR / SIL)
@bot.hybrid_command(name="temizle", description="Kanalda belirtilen miktarda mesajı siler.")
@app_commands.checks.has_permissions(manage_messages=True)
@commands.has_permissions(manage_messages=True)
async def temizle(ctx: commands.Context, miktar: int):
    """Kanalda toplu mesaj siler."""
    if miktar < 1 or miktar > 100:
        await ctx.send("❌ Lütfen 1 ile 100 arasında bir sayı girin.", delete_after=5)
        return
        
    silinen = await ctx.channel.purge(limit=miktar)
    embed = discord.Embed(
        description=f"🧹 **{len(silinen)}** adet mesaj başarıyla silindi.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, delete_after=5)

# 6. UYARI SİSTEMİ (WARN)
@bot.hybrid_command(name="uyar", description="Kullanıcıya uyarı verir.")
@app_commands.checks.has_permissions(manage_messages=True)
@commands.has_permissions(manage_messages=True)
async def uyar(ctx: commands.Context, uye: discord.Member, *, sebep: str = "Sebep belirtilmedi."):
    """Kullanıcıyı uyarır ve kaydeder."""
    guild_id = ctx.guild.id
    user_id = uye.id
    
    if guild_id not in warn_database:
        warn_database[guild_id] = {}
    if user_id not in warn_database[guild_id]:
        warn_database[guild_id][user_id] = []
        
    warn_database[guild_id][user_id].append({
        "yetkili": ctx.author.name,
        "sebep": sebep,
        "tarih": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    toplam_uyari = len(warn_database[guild_id][user_id])
    
    embed = discord.Embed(
        title="⚠️ Kullanıcı Uyarıldı",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Uyarılan:", value=uye.mention, inline=True)
    embed.add_field(name="Toplam Uyarı:", value=str(toplam_uyari), inline=True)
    embed.add_field(name="Yetkili:", value=ctx.author.mention, inline=False)
    embed.add_field(name="Sebep:", value=sebep, inline=False)
    
    await ctx.send(embed=embed)

# 7. UYARILARI GÖRÜNTÜLEME (WARNS)
@bot.hybrid_command(name="uyarılar", description="Kullanıcının geçmiş uyarılarını listeler.")
async def uyarilar(ctx: commands.Context, uye: discord.Member):
    """Uyarı geçmişini listeler."""
    guild_id = ctx.guild.id
    user_id = uye.id
    
    if guild_id not in warn_database or user_id not in warn_database[guild_id] or not warn_database[guild_id][user_id]:
        await ctx.send(f"ℹ️ {uye.mention} kullanıcısına ait kayıtlı uyarı bulunamadı.")
        return
        
    embed = discord.Embed(
        title=f"📋 {uye.display_name} - Uyarı Geçmişi",
        color=discord.Color.yellow()
    )
    
    for i, warn in enumerate(warn_database[guild_id][user_id], 1):
        embed.add_field(
            name=f"Uyarı #{i}",
            value=f"**Yetkili:** {warn['yetkili']}\n**Sebep:** {warn['sebep']}\n**Tarih:** {warn['tarih']}",
            inline=False
        )
        
    await ctx.send(embed=embed)

# 8. YARDIM KOMUTU
@bot.hybrid_command(name="yardim", description="Tüm moderasyon komutlarını listeler.")
async def yardim(ctx: commands.Context):
    """Bot yardım menüsü."""
    embed = discord.Embed(
        title="🛡️ Moderasyon Bot Komutları",
        description="Aşağıdaki tüm komutları hem `!` prefix'i ile hem de Slash (`/`) komutu olarak kullanabilirsiniz.",
        color=discord.Color.green()
    )
    embed.add_field(name="/ban @kullanıcı [sebep]", value="Kullanıcıyı sunucudan yasaklar.", inline=False)
    embed.add_field(name="/kick @kullanıcı [sebep]", value="Kullanıcıyı sunucudan atar.", inline=False)
    embed.add_field(name="/mute @kullanıcı [dakika] [sebep]", value="Kullanıcıya geçici süreyle zamanaşımı uygular.", inline=False)
    embed.add_field(name="/unmute @kullanıcı", value="Kullanıcının zamanaşımını kaldırır.", inline=False)
    embed.add_field(name="/temizle [sayı]", value="Kanalda belirtilen sayıda mesajı temizler.", inline=False)
    embed.add_field(name="/uyar @kullanıcı [sebep]", value="Kullanıcıyı uyarır.", inline=False)
    embed.add_field(name="/uyarılar @kullanıcı", value="Kullanıcının tüm uyarılarını listeler.", inline=False)
    
    embed.set_footer(text=f"Talep eden: {ctx.author.name}", icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None)
    await ctx.send(embed=embed)

# ==========================================
# BOTU BAŞLATMA
# ==========================================
if __name__ == "__main__":
    # 7/24 Web Sunucusunu başlatıyoruz
    keep_alive()
    
    # Kendi Token'ınız Kodun İçine Yerleştirildi
    BOT_TOKEN = "MTU2NjM3OTE3NzAxMDEzOTE3Ng.GblHvm.qTYoEXL5R02-eAOSK-M76TXof_A-2ARaFlei1w"
    
    try:
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ HATA: Geçersiz Bot Token'ı girdiniz! Lütfen token'ınızı kontrol edin.")
    except Exception as e:
        print(f"❌ Başlatma hatası: {e}")