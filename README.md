<div align="center">

<h1>🤖 J.A.R.V.I.S — Windows AI Asistanı</h1>

<p><strong>Gemini Live API veya yerel LM Studio destekli, Türkçe konuşan sesli Windows masaüstü asistanı</strong></p>

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![Gemini](https://img.shields.io/badge/Powered%20by-Gemini%202.5%20Flash-orange?style=for-the-badge&logo=google&logoColor=white)

</div>

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Özellikler](#-özellikler)
- [Mimari](#-mimari)
- [Gereksinimler](#-gereksinimler)
- [Kurulum](#-kurulum)
- [Yapılandırma](#-yapılandırma)
- [Kullanım](#-kullanım)
- [Desteklenen Komutlar](#-desteklenen-komutlar)
- [Yerel Mod (LM Studio)](#-yerel-mod-lm-studio)
- [Proje Yapısı](#-proje-yapısı)
- [Katkı](#-katkı)

---

## 🎯 Proje Hakkında

JARVIS, Windows masaüstü ortamı için geliştirilmiş gerçek zamanlı sesli AI asistanıdır. Google Gemini 2.5 Flash Live API'yi temel alır ve hem **bulut (Gemini)** hem de **tamamen çevrimdışı yerel (LM Studio)** modda çalışabilir.

Kullanıcıyla **Türkçe** konuşur, sesli komutları anlık olarak işler ve 16'dan fazla entegre araç aracılığıyla Windows'ta gerçek eylemleri hayata geçirir.

---

## ✨ Özellikler

### Ses ve Konuşma
- 🎙️ **Gerçek zamanlı ses akışı** — PyAudio ile 16 kHz giriş, 24 kHz çıkış
- 🔊 **Doğal sesli yanıt** — Gemini Native Audio veya Windows SAPI TTS
- ✍️ **Metin modu** — Sesle birlikte yazılı komut desteği
- 🔇 **Duraklat / Devam** — Oturum kesilmeden anlık duraklama

### Sistem Entegrasyonu
- 🖥️ **Uygulama yönetimi** — Herhangi bir Windows uygulamasını sesle aç
- 📊 **Sistem bilgisi** — CPU, RAM, disk, pil, saat, tarih, ağ durumu
- 💻 **PowerShell** — Sesli terminal komutları çalıştırma
- 👁️ **Ekran analizi** — Aktif pencerenin görüntüsünü AI ile analiz etme (Gemini Vision veya LM Studio Vision)

### Üretkenlik
- 📅 **Takvim** — Outlook veya yerel JSON takvim; okuma, ekleme, silme
- ⏰ **Anımsatıcı** — Outlook Tasks veya yerel JSON; oluşturma ve listeleme
- 🧠 **Kalıcı bellek** — Kullanıcıya özel bilgileri JSON'a kaydetme ve silme

### İletişim ve Medya
- 💬 **WhatsApp** — Desktop veya Web üzerinden mesaj hazırlama ve otomatik gönderme; VCF rehber içe aktarma
- 🌦️ **Hava durumu** — Anlık hava durumu özeti (OpenWeatherMap)
- 🎵 **Medya oynatma** — YouTube, Spotify Desktop ve Apple Music Web entegrasyonu
- 🌐 **Tarayıcı kontrolü** — URL açma, Google arama, YouTube video oynatma
- 📈 **YouTube Analytics** — Kanal istatistikleri ve video performans raporu

### Çift Backend Desteği
- ☁️ **Gemini modu** — Google Gemini 2.5 Flash Live API
- 🏠 **Yerel mod** — LM Studio (OpenAI-uyumlu) ile tamamen çevrimdışı çalışma; Whisper veya Google STT

---

## 🏗️ Mimari

```
jarvis/
├── main.py                  ← Gemini Live oturum yöneticisi (JarvisLive)
├── ui.py                    ← Tkinter tabanlı masaüstü arayüzü (JarvisUI)
├── app_config.py            ← Yapılandırma okuma/yazma
├── core/
│   ├── lmstudio_runtime.py  ← Yerel mod motoru (JarvisLocal)
│   └── prompt.txt           ← AI sistem promptu
├── actions/                 ← Araç modülleri
│   └── ...
├── memory/                  ← Kalıcı bellek
└── config/                  ← API anahtarları
```

### Veri Akışı — Gemini Modu

```
Mikrofon → PyAudio → Gemini Live API
                           ↓
                    Tool Call Tespiti
                           ↓
                    actions/* modülleri
                           ↓
                    Sonuç → Gemini → Ses Çıkışı → Hoparlör
```

### Veri Akışı — Yerel Mod

```
Mikrofon → SpeechRecognition (Whisper/Google STT) → Metin
                                                        ↓
                                                 LM Studio API
                                                        ↓
                                                Tool Call Tespiti
                                                        ↓
                                                actions/* modülleri
                                                        ↓
                                                Metin → Windows SAPI TTS → Hoparlör
```

---

## 📦 Gereksinimler

| Gereksinim | Detay |
|-----------|-------|
| **Python** | 3.10 veya üzeri |
| **İşletim Sistemi** | Windows 10 / 11 |
| **Gemini API Anahtarı** | [Google AI Studio](https://aistudio.google.com/apikey)'dan ücretsiz alınır |
| **Mikrofon** | Herhangi bir USB veya dahili mikrofon |
| **YouTube API** | Opsiyonel — kanal istatistikleri için |
| **LM Studio** | Opsiyonel — yerel çevrimdışı mod için |

### Python Bağımlılıkları

```
google-genai
SpeechRecognition
pyaudio
psutil
Pillow
requests
pyautogui
pyttsx3
pywin32
openai-whisper  (opsiyonel, yerel STT için)
```

---

## 🚀 Kurulum

### 1. Depoyu Klonla

```bash
git clone https://github.com/bnsware/jarvis.git
cd jarvis
```

### 2. Otomatik Kurulum (Önerilen)

```batch
setup.bat
```

Bu script sırasıyla şunları yapar:
- Python varlığını kontrol eder
- `venv` sanal ortamı oluşturur
- Gerekli fontları Windows'a kurar
- `requirements.txt` paketlerini yükler
- `config/api_keys.json` dosyasını şablondan oluşturur

### 3. Manuel Kurulum

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy config\api_keys.example.json config\api_keys.json
```

> **Not:** PyAudio kurulumunda hata alırsanız:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## ⚙️ Yapılandırma

`config/api_keys.json` dosyasını düzenle:

```json
{
  "gemini_api_key": "AIza...",
  "voice": "Charon",
  "youtube_api_key": "",
  "youtube_channel_handle": "@kanalin",
  "backend": "gemini",
  "lmstudio_base_url": "http://127.0.0.1:1234/v1",
  "lmstudio_model": "local-model",
  "lmstudio_api_key": "lm-studio",
  "stt_engine": "whisper",
  "stt_language": "tr-TR"
}
```

| Alan | Açıklama | Zorunlu |
|------|----------|---------|
| `gemini_api_key` | Google Gemini API anahtarı | Gemini modunda evet |
| `voice` | Ses tonu: `Charon`, `Aoede`, `Fenrir`, `Kore`, `Puck` | Hayır |
| `youtube_api_key` | YouTube Data API v3 anahtarı | Kanal raporu için |
| `youtube_channel_handle` | `@kanalin` formatında handle | Kanal raporu için |
| `backend` | `gemini` veya `lmstudio` | Hayır (varsayılan: gemini) |
| `lmstudio_base_url` | LM Studio sunucu adresi | Yerel modda evet |
| `lmstudio_model` | Kullanılacak yerel model adı | Yerel modda evet |
| `stt_engine` | `whisper` veya `google` | Yerel modda |
| `stt_language` | STT dil kodu | Yerel modda |

---

## 🎮 Kullanım

### Başlatma

```batch
start.bat
```

veya manuel:

```bash
venv\Scripts\activate
python main.py
```

### Arayüz

JARVIS açıldığında modern bir masaüstü penceresi görünür:

- **Durum göstergesi** — `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`
- **Log paneli** — Gerçek zamanlı konuşma akışı
- **Metin kutusu** — Sesle birlikte yazılı komut girebilirsin
- **Duraklat butonu** — Oturumu kesmeden asistanı susturur
- **Sistem paneli** — CPU, RAM, pil ve hava durumu widget'ları

---

## 🗣️ Desteklenen Komutlar

### Sistem ve Uygulamalar

```
"Spotify'ı aç"
"VS Code'u başlat"
"Pil durumu nedir?"
"RAM kullanımı kaç?"
"Saat kaç?"
"Masaüstündeki dosyaları listele"
```

### Takvim

```
"Bugün takvimimde ne var?"
"Yarın ajandam nasıl?"
"Sıradaki toplantım ne?"
"Önümüzdeki 30 gün takvimimde ne var?"
"Yarın 14:00'e dişçi randevusu ekle"
"Pazartesi 10:00-11:00 toplantı ekle"
"Takvimden toplantıyı sil"
```

### Anımsatıcılar

```
"Bugün anımsatıcılarım ne?"
"Yaklaşan hatırlatmalarımı göster"
"Yarın sabah 9'da dişçiyi hatırlat"
"Bugün akşam süt almayı hatırlat"
```

### Hava Durumu ve Tarayıcı

```
"Hatay'da hava nasıl?"
"Google'da Python öğren ara"
"YouTube'dan The Weeknd Blinding Lights aç"
"github.com'u aç"
```

### Medya

```
"Spotify'da The Weeknd Blinding Lights çal"
"Apple Music'te Sezen Aksu Gülümse aç"
"YouTube'da lofi beats oynat"
```

### WhatsApp

```
"Anneme WhatsApp'tan iyi geceler mesajı gönder"
"Ahmet'e WhatsApp mesajı hazırla: yarın görüşelim"
```

### Ekran Analizi

```
"Ekranda ne var?"
"Bu hatayı oku"
"Bu pencereyi analiz et"
"Burada ne yazıyor?"
```

### YouTube Analytics

```
"YouTube istatistiklerim nasıl?"
"Son videolarımı analiz et"
"Kanal büyümemi özetle"
```

### Bellek

```
"Benim adım Ali"
"Projem bir Python uygulaması"
"Claude limiti notunu hafızandan kaldır"
"Bunu hafızandan sil"
```

---

## 🏠 Yerel Mod (LM Studio)

İnternet bağlantısı gerektirmeden tamamen yerel çalışmak için:

**1. LM Studio'yu indir ve bir model yükle:**
[lmstudio.ai](https://lmstudio.ai) adresinden indir, bir model seçip sunucuyu başlat.

**2. `config/api_keys.json` dosyasını güncelle:**
```json
{
  "backend": "lmstudio",
  "lmstudio_base_url": "http://127.0.0.1:1234/v1",
  "lmstudio_model": "lmstudio-community/mistral-7b-instruct",
  "stt_engine": "whisper"
}
```

**3. Ekran analizi için vision modeli:**
```json
{
  "lmstudio_vision_model": "xtuner/llava-llama-3-8b-v1_1-gguf"
}
```

**Yerel modda neler değişir:**
- Ses girişi → Whisper (yerel) veya Google STT
- Ses çıkışı → Windows SAPI TTS (sistem sesi)
- AI motoru → LM Studio OpenAI-uyumlu API
- Tüm araçlar aynı şekilde çalışır

---

## 📁 Proje Yapısı

```
jarvis/
├── main.py                  ← Ana giriş noktası ve Gemini Live motoru
├── ui.py                    ← Masaüstü arayüzü (Tkinter)
├── app_config.py            ← Yapılandırma yöneticisi
├── requirements.txt         ← Python bağımlılıkları
├── setup.bat                ← Otomatik kurulum scripti
├── start.bat                ← Hızlı başlatma scripti
├── pyrightconfig.json       ← Tip denetimi yapılandırması
├── .gitignore
├── Fonts/                   ← Arayüz fontları
├── Icon/                    ← Uygulama ikonu
├── SFX/                     ← Ses efektleri
├── core/
│   ├── lmstudio_runtime.py  ← Yerel AI motoru
│   └── prompt.txt           ← Sistem promptu
├── actions/
│   ├── __init__.py
│   ├── browser.py           ← Web tarayıcı kontrolü
│   ├── calendar.py          ← Takvim işlemleri (Outlook + JSON)
│   ├── health.py            ← Sağlık takibi
│   ├── media.py             ← Müzik/video oynatma
│   ├── open_app.py          ← Uygulama başlatma
│   ├── reminders.py         ← Anımsatıcı işlemleri (Outlook + JSON)
│   ├── screen_vision.py     ← Ekran görüntüsü + Vision AI
│   ├── shell.py             ← PowerShell entegrasyonu
│   ├── sys_info.py          ← Sistem bilgisi (psutil)
│   ├── tts.py               ← Windows SAPI metin-konuşma
│   ├── weather.py           ← Hava durumu (OpenWeatherMap)
│   ├── whatsapp.py          ← WhatsApp mesajlaşma
│   └── youtube_stats.py     ← YouTube Data API
├── memory/
│   ├── __init__.py
│   ├── memory_manager.py    ← JSON bellek yöneticisi
│   ├── memory.example.json  ← Bellek şablonu
│   └── phone_book.example.json ← Telefon rehberi şablonu
└── config/
    ├── api_keys.json        ← API anahtarları (gitignore'd)
    └── api_keys.example.json ← Şablon
```

---

## 🔒 Güvenlik

- `config/api_keys.json` ve `memory/memory.json` dosyaları `.gitignore`'a eklenmiştir — API anahtarların ve kişisel veriler repoya dahil olmaz.
- `phone_book.json` da yayımlanmaz.
- Yalnızca `*.example.json` şablonları repoya dahildir.

---

## 🤝 Katkı

1. Bu repoyu fork'la
2. Yeni bir dal oluştur: `git checkout -b feature/yeni-ozellik`
3. Değişikliklerini kaydet: `git commit -m "Yeni özellik: açıklama"`
4. Dalını gönder: `git push origin feature/yeni-ozellik`
5. Pull Request aç

---

<div align="center">
<p>Geliştirici: <a href="https://github.com/bnsware">bnsware</a> ve <a href="https://www.instagram.com/alppunlu">alppunlu</a></p>
</div>
