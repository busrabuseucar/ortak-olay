# Ortak Olay — Başlangıç

Bu paket başvuru fikrinin çalışan koordinatör arayüzü ve backend sürümüdür. Tamamlanmış bir saha ürünü değildir.

## Hazır olanlar

Rapor kaydı, benzer kayıt önerileri, koordinatör onayı, yanlış bağlantıyı ayırma, ihtiyaç durumları ve işlem geçmişi. Veriler SQLite dosyasında korunur. Backend ve tarayıcı üzerinden iş akışı testleri bulunur. İsteğe bağlı yerel model Türkçe, İngilizce ve Yunanca metinler arasında benzerlik önerir.

## Bilgisayarda açma

1. Python 3.12 kurulu olmalı. ZIP dosyasını çıkar ve `ortak-olay` klasörünü VS Code ile aç.
2. Terminalde `python -m venv .venv` çalıştır.
3. Windows'ta `.\.venv\Scripts\Activate.ps1` ile ortamı etkinleştir. Etkinleştirme engellenirse doğrudan `.\.venv\Scripts\python.exe` kullanarak aşağıdaki Python komutlarını çalıştırabilirsin.
4. `python -m pip install -r requirements.txt` çalıştır.
5. `python scripts/run_local.py` çalıştır.
6. Tarayıcıda `http://127.0.0.1:8000` adresini aç. Terminalde gösterilen geçici anahtarı giriş ekranındaki **Erişim anahtarı** alanına yapıştır.

Buradaki koordinatör arayüzünden rapor ekleyebilir, kaynakları karşılaştırabilir, bağlantı kararlarını ve ihtiyaç durumlarını kaydedebilirsin. Sayfayı yenilersen anahtarını tekrar girmen gerekir. Ayrıntılı kurulum ve örnek senaryo komutları README dosyasında.

## GitHub'a geçiş

Proje deposu: https://github.com/busrabuseucar/ortak-olay

README kurulum adımlarını, ROADMAP geliştirme aşamalarını içerir. Otomatik test tanımı `.github/workflows/tests.yml` dosyasındadır; çalıştırma sonuçlarını GitHub Actions sekmesinden takip edebilirsin.

## Çok dilli modeli açma

Aynı Python ortamında:

```sh
python -m pip install -r requirements-ai.txt
python scripts/run_local.py --semantic
```

İlk açılışta yaklaşık 220 MB model dosyası indirilir. Raporlar bilgisayarında işlenir. Model, benzer raporları kaynaklarıyla önerir; bağlantı ve durum değişikliği kararını sen verirsin. Puan doğruluk yüzdesi değildir. Farklı yer adlarını ve ihtiyacın güncel olup olmadığını mutlaka kaynaklardan kontrol et.

18 yapay örnekte model eklemek daha fazla ilgili kaydı buldu, fakat yanlış adayları da artırdı. Bu nedenle varsayılan hâlâ konum/kategori kuralıdır. Ölçümün ayrıntıları `evaluation/README.md` dosyasında. Serbest metinden otomatik bilgi çıkarımı, bağımsız değerlendirme ve gerçek kullanıcı doğrulaması sonraki aşamalar.

Portföyünde doğru ifade: “Ortak Olay için kaynak metinleri koruyan, insan onaylı ihtiyaç takibi ve yerel çok dilli benzerlik önerileri içeren bir prototip geliştiriyorum.” Saha kullanımı ve gerçek kullanıcı doğrulaması henüz yapılmadı.
