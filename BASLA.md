# Ortak Olay — Başlangıç

Bu paket başvuru fikrinin çalışan ilk backend sürümüdür. Tamamlanmış bir saha ürünü değildir.

## Hazır olanlar

Rapor kaydı, benzer kayıt önerileri, koordinatör onayı, yanlış bağlantıyı ayırma, ihtiyaç durumları ve işlem geçmişi. Veriler SQLite dosyasında korunur. 11 otomatik test ve çalışan sunucuya karşı örnek senaryo doğrulandı.

## Bilgisayarda açma

1. Python 3.12 kurulu olmalı. ZIP dosyasını çıkar ve `ortak-olay` klasörünü VS Code ile aç.
2. Terminalde `python -m venv .venv` çalıştır.
3. Windows'ta `.\.venv\Scripts\Activate.ps1` ile ortamı etkinleştir. Etkinleştirme engellenirse doğrudan `.\.venv\Scripts\python.exe` kullanarak aşağıdaki Python komutlarını çalıştırabilirsin.
4. `python -m pip install -r requirements.txt` çalıştır.
5. `python scripts/run_local.py` çalıştır.
6. Tarayıcıda `http://127.0.0.1:8000/docs` adresini aç. Terminalde gösterilen geçici anahtarı **Authorize** alanına yapıştır.

Buradaki sayfa geliştiricilere yönelik API deneme ekranıdır. Önerideki koordinatör arayüzünü sonraki aşamada geliştireceğiz. Ayrıntılı kurulum ve örnek senaryo komutları README dosyasında.

## GitHub'a geçiş

Proje deposu: https://github.com/busrabuseucar/ortak-olay

README kurulum adımlarını, ROADMAP geliştirme aşamalarını içerir. Otomatik test tanımı `.github/workflows/tests.yml` dosyasındadır; çalıştırma sonuçlarını GitHub Actions sekmesinden takip edebilirsin.

## Sonraki çalışma

Önce gelen raporlar, olay ayrıntısı ve karar ekranları. Ardından kaynak metne bağlı bilgi çıkarımı ve çok dilli anlamsal eşleştirme. Şimdiki eşleştirme, elle girilmiş konum ve kategori üzerinden çalışan açık bir kural tabanıdır; yapay zekâ başarısı olarak sunulmamalı.

Portföyünde bugün doğru ifade: “Ortak Olay için rapor yönetimi, insan onaylı eşleştirme ve izlenebilir ihtiyaç güncellemelerini içeren backend prototipi geliştiriyorum.” Gerçek kullanıcı doğrulaması ve saha kullanımı henüz yapılmadı.
