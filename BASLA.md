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

18 yapay örnekte model 9 ilgili çiftin 7’sini buldu. Yeni konum kodu kontrolü, bu doğru önerileri koruyarak yanlış adayları 5’ten 2’ye düşürdü. Bu kontrol aynı örneklerdeki hatalara bakılarak geliştirildi; bağımsız başarı ölçümü değildir. “Barınak A / Barınak B” gibi kod çelişkileri ayrı gösterilir; aynı yerdeki farklı gruplar ve varsayımsal mesajlar hâlâ sorun çıkarabilir. Bu nedenle varsayılan hâlâ konum/kategori kuralıdır. Ölçümün ayrıntıları `evaluation/README.md` dosyasında. Serbest metinden otomatik bilgi çıkarımı, bağımsız değerlendirme ve gerçek kullanıcı doğrulaması sonraki aşamalar.

Portföyünde doğru ifade: “Ortak Olay için kaynak metinleri koruyan, insan onaylı ihtiyaç takibi ve yerel çok dilli benzerlik önerileri içeren bir prototip geliştiriyorum.” Saha kullanımı ve gerçek kullanıcı doğrulaması henüz yapılmadı.

## Grup ve mesaj türü kontrolü

Yeni raporda **Grup / çadır kodu** ve **Mesajın türü** alanları var. Aynı grup için her dilde aynı kodu kullan; bilmiyorsan boş bırak. Tür seçenekleri: belirsiz, ihtiyaç bildirimi, güncelleme/teslimat, varsayımsal durum, genel bilgi/tavsiye.

Varsayımsal ve genel bilgi olarak işaretlenen mesajlardan ihtiyaç açılamaz. Farklı olduğu açıkça belirtilen gruplar aynı ihtiyaca bağlanamaz. Bilgi eksikse sistem uyarır; kendisi grup veya mesaj türü uydurmaz. Bu alanları sen değerlendiriyorsun, yapay zekâ değil.

Yanlış sınıflandırılan ve henüz bağlanmamış raporu **Rapor değerlendirmesini düzelt** bölümünden gerekçeyle güncelleyebilirsin. Kaynak mesaj korunur; kim, neyi, neden değiştirdi görünür. Bağlandıktan sonra bu alanlar bu sürümde değiştirilemez.

Eski veritabanı açıldığında yeni alanlar otomatik eklenir. Eski raporlar, bağlantılar ve geçmiş korunur; eski kayıtlar için sınıflandırma yapılmış gibi gösterilmez.
