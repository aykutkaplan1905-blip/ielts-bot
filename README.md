# IELTS Takip Botu

Bilkent Hazırlık IELTS kayıt sayfasını (https://prep.bilkent.edu.tr/ielts-kayit/) düzenli olarak kontrol eder. Yeni bir sınav oturumu açıldığında telefonuna **anında push bildirimi** atar. Bildirime dokununca doğrudan kayıt linki açılır.

- GitHub Actions üzerinde ücretsiz çalışır, sunucu ve açık bilgisayar gerekmez.
- 7/24, **15 dakikada bir** kontrol eder.
- Sadece okur ve haber verir, kayıt yapmaz.

```
ielts_bot.py                  → botun kendisi (ek kütüphane gerektirmez)
.github/workflows/ielts.yml   → zamanlama
seen_sessions.json            → ilk çalıştırmada otomatik oluşur, görülen oturumlar
```

---

## 1. Bildirim kanalını seç (birini yapman yeterli)

### Seçenek A: ntfy (en kolayı, hesap gerekmez)

1. Telefonuna **ntfy** uygulamasını kur (App Store / Google Play).
2. Tahmin edilmesi zor bir konu adı uydur, ör. `murat-ielts-x7k2q9`.
   Konu adını bilen herkes mesajlarını görebilir, bu yüzden rastgele bir şey seç.
3. Uygulamada **+ → Subscribe to topic** ile bu adı ekle.
4. Bu ad, aşağıdaki `NTFY_TOPIC` secret'ı olacak.

### Seçenek B: Telegram

1. Telegram'da **@BotFather**'a `/newbot` yaz, bir isim ver ve sana verdiği **token**'ı kopyala.
2. Oluşturduğun bota bir mesaj at (ör. "merhaba").
3. Tarayıcıda şu adresi aç: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Çıkan JSON'daki `"chat":{"id": 123456789 ...}` değeri senin **chat id**'n.
4. Bunlar `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` secret'ları olacak.

İkisini birden ayarlarsan bildirim iki kanala da gider.

## 2. GitHub'a yükle

1. GitHub'da yeni bir **Public** repo oluştur. 15 dakikalık sıklık private repoda ücretsiz kotayı aşar, public repoda ise sınırsız ve ücretsizdir.
   Secret'ların (ntfy konusu, Telegram token) public repoda da gizli kalır. Repoda sadece kod ve zaten herkese açık olan oturum linkleri görünür.
2. Bu klasördeki dosyaları yükle. `.github/workflows/ielts.yml` yolunun aynen korunması gerekiyor.
   Web arayüzünden yüklerken klasörü sürükleyip bırakabilirsin.
3. **Settings → Secrets and variables → Actions → New repository secret** ile şunları ekle:
   - `NTFY_TOPIC`, ya da
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
4. **Settings → Actions → General → Workflow permissions** altında **Read and write permissions** seçili olsun.

## 3. Çalıştır

**Actions → IELTS takibi → Run workflow** ile ilk çalıştırmayı elle yap. Telefonuna
"🤖 IELTS botu başladı" bildirimi ve şu anki oturumların listesi gelmeli.

Bu noktadan sonra:

| Durum | Ne olur |
|---|---|
| Yeni oturum açıldı | 🔔 **YENİ IELTS OTURUMU AÇILDI** bildirimi + kayıt linki (en yüksek öncelikte) |
| Değişiklik yok | Sessiz kalır |
| Sayfa açılmadı / yapısı değişti | Workflow başarısız olur ve GitHub sana e-posta atar |

Aynı oturum için ikinci kez bildirim gelmez.

---

## Ayarlar

- **Kontrol sıklığı:** `ielts.yml` içindeki `cron` satırını değiştir. Saatler UTC'dir (TR = UTC+3).
  - Şu anki ayar, 15 dakikada bir: `"*/15 * * * *"`
  - Saatte bir: `"17 * * * *"`
  - Günde bir (TR 08:17): `"17 5 * * *"`
- **Yerelde test:**
  ```bash
  NTFY_TOPIC=senin-konun python ielts_bot.py --test   # sadece test bildirimi
  DRY_RUN=1 python ielts_bot.py                        # bildirim atmadan kuru çalıştırma
  ```

## Bilmen gerekenler

- GitHub zamanlanmış işleri yoğun saatlerde birkaç dakika ile yarım saat arası gecikmeli çalıştırabilir.
- Public repolarda 60 gün boyunca hiç commit olmazsa GitHub zamanlanmış işleri durdurur. Bot bunu önlemek için 45 günde bir kendiliğinden küçük bir commit atar, senin bir şey yapmana gerek yok.
- Private repo kullanırsan ayda 2000 dakika ücretsiz hakkın var. 15 dakikalık sıklık ayda yaklaşık 2900 dakika harcar, yani kotayı aşar. Private istiyorsan cron'u saatte bire düşür, o zaman ayda yaklaşık 720 dakika harcar.
- **Gerçek SMS** istersen Netgsm, İletimerkezi veya Twilio gibi ücretli bir SMS sağlayıcısı gerekir. Türk sağlayıcılarda gönderici başlığı onayı da isteniyor. ntfy/Telegram bildirimi pratikte SMS kadar hızlı ve ücretsiz.
