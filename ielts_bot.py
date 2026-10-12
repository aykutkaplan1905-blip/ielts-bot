#!/usr/bin/env python3
"""
Bilkent Hazırlık IELTS kayıt sayfasını izler; yeni bir sınav oturumu
açıldığında telefona bildirim atar (ntfy ve/veya Telegram).

Ortam değişkenleri:
  NTFY_TOPIC          ntfy konu adı (ör. murat-ielts-x7k2q9)  -> ntfy bildirimi
  TELEGRAM_BOT_TOKEN  BotFather'dan alınan token               -> Telegram bildirimi
  TELEGRAM_CHAT_ID    Senin chat id'n
  IELTS_URL           İzlenecek sayfa (varsayılan Bilkent IELTS kayıt)
  STATE_FILE          Görülen oturumların tutulduğu dosya (varsayılan seen_sessions.json)
  DRY_RUN=1           Bildirim göndermez, sadece ekrana yazar

Kullanım:
  python ielts_bot.py          # normal kontrol
  python ielts_bot.py --test   # sadece test bildirimi gönderir
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL = os.environ.get("IELTS_URL", "https://prep.bilkent.edu.tr/ielts-kayit/")
STATE_FILE = Path(os.environ.get("STATE_FILE", "seen_sessions.json"))
DRY_RUN = os.environ.get("DRY_RUN") == "1"
UA = "Mozilla/5.0 (X11; Linux x86_64) ielts-watch-bot/1.0"


class LinkParser(HTMLParser):
    """Sayfadaki tüm <a> etiketlerini (href, görünen metin) olarak toplar."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join("".join(self._text).split())
            self.links.append((self._href, text))
            self._href = None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_sessions(html: str) -> dict:
    """{kayıt_linki: 'Saat Oturumu – Tarih IELTS Sınavı'} döndürür."""
    p = LinkParser()
    p.feed(html)
    sessions = {}
    for href, text in p.links:
        low = text.lower()
        if "ielts" in low and "oturum" in low and href.startswith("http"):
            label = text
            for prefix in ("Kayıt İçin –", "Kayıt İçin -", "Kayıt İçin"):
                if label.startswith(prefix):
                    label = label[len(prefix):].strip(" –-")
                    break
            sessions[href] = label
    return sessions


def post(url: str, data: bytes, content_type: str):
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": content_type, "User-Agent": UA}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def notify(title: str, body: str, click: str | None = None):
    if DRY_RUN:
        print(f"[DRY_RUN] {title}\n{body}\n(link: {click})")
        return

    sent = False
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        payload = {
            "topic": topic,
            "title": title,
            "message": body,
            "priority": 5,
            "tags": ["rotating_light"],
        }
        if click:
            payload["click"] = click
        # JSON ile gönderiyoruz ki Türkçe karakterler sorunsuz gitsin
        post("https://ntfy.sh/", json.dumps(payload).encode(), "application/json")
        sent = True

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": f"{title}\n\n{body}", "disable_web_page_preview": "true"}
        ).encode()
        post(f"https://api.telegram.org/bot{token}/sendMessage", data,
             "application/x-www-form-urlencoded")
        sent = True

    if not sent:
        sys.exit("HATA: Bildirim kanalı yok. NTFY_TOPIC veya TELEGRAM_BOT_TOKEN+TELEGRAM_CHAT_ID ayarla.")


def format_list(sessions: dict) -> str:
    return "\n\n".join(f"• {label}\n{href}" for href, label in sessions.items())


def main():
    if "--test" in sys.argv:
        notify("✅ IELTS botu test", "Bildirimler çalışıyor. Yeni oturum açılınca buradan haber vereceğim.", URL)
        print("Test bildirimi gönderildi.")
        return

    current = extract_sessions(fetch(URL))
    if not current:
        # Sayfa yapısı değişmiş ya da sayfa boş gelmiş olabilir; iş başarısız sayılsın
        sys.exit("HATA: Sayfada hiç IELTS oturumu bulunamadı (sayfa yapısı değişmiş olabilir).")

    first_run = not STATE_FILE.exists()
    seen = {} if first_run else json.loads(STATE_FILE.read_text(encoding="utf-8"))

    if first_run:
        notify(
            "🤖 IELTS botu başladı",
            f"Şu an sayfada {len(current)} oturum var:\n\n{format_list(current)}",
            URL,
        )
    else:
        new = {h: l for h, l in current.items() if h not in seen}
        if new:
            click = next(iter(new)) if len(new) == 1 else URL
            notify(
                f"🔔 YENİ IELTS OTURUMU AÇILDI ({len(new)})",
                format_list(new),
                click,
            )
            print(f"{len(new)} yeni oturum bildirildi.")
        else:
            print(f"Değişiklik yok. {len(current)} oturum mevcut.")

    if current != seen:
        STATE_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
