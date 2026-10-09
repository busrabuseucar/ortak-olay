# İlk koordinatör denemesi

**Durum: Sentetik hazırlık paketi. Henüz katılımcı, görüşme sonucu veya başarı ölçümü yok.**

Bu paket v0.5 prototipindeki karar ve düzeltme akışlarını bir koordinatöre göstermek için hazırlandı. Altı görev, bağımsız model testi değildir. İlk oturumun amacı iş akışını anlamak ve kullanılabilirlik sorunlarını bulmaktır; yüzde zaman kazancı hesaplamak değildir.

## Kullanım sırası

1. [Görüşme rehberi](../COORDINATOR_RESEARCH_TR.md) ile kişinin mevcut işini öğren. Özellik anlatmadan önce son somut örneği sor.
2. Not alma izni iste. İsim, telefon, gerçek afetzede bilgisi veya hassas kurum verisi toplama.
3. Kurulum için kökteki [README](../../README.md) talimatını izle. Ayrı bir deneme veritabanı kullan; mevcut verileri silme veya gerçek operasyon ortamında çalıştırma.
4. Oturum kaydına kod sürümünü, eşleştirme modunu, gözlemci tarafından önceden girilen kayıtları ve katılımcının ilgili deneyimini yaz.
5. [Katılımcı görevlerini](PARTICIPANT_TR.md) paylaş; [gözlemci anahtarını](OBSERVER_TR.md) paylaşma.
6. Önce puanlanmayan kısa bir alıştırma yap. Altı görevin tamamı için yaklaşık 30-45 dakika ayır; bu süre bir tahmin, ölçülmüş sonuç değildir. Görüşme ayrı zaman alır.
7. [Boş kayıt şablonunu](SESSION_RECORD_TR.md) özel bir çalışma alanına kopyala. Doldurulmuş ham notları açık GitHub deposuna yükleme.
8. Gözlenen sorunları ürün kararına çevir; işe yaramayan yönleri de kaydet.

## Deneme ortamı

Yerel başlatıcıdan önce farklı bir veritabanı yolu seç:

- PowerShell: `$env:ORTAK_DB = "data/exercise-P01.db"`
- macOS/Linux: `export ORTAK_DB="data/exercise-P01.db"`

Ardından `python scripts/run_local.py` çalıştır. Her oturum için yeni bir dosya adı kullan; var olan dosyayı aynı adla seçersen kayıtlar kalır. Erişim anahtarını notlara veya depoya ekleme. Yeni görevi önceki görevlerden ayırmak için aşağıdaki farklı konum adlarını kullan.

İlk turda varsayılan kural tabanlı mod kullanılır. Bu bilinçli seçim, insan karar akışını model kalitesinden ayrı gözlemlemek içindir. Anlamsal modu ayrıca denersen modu ve model sürümünü kaydet; sonuçları tek ölçümde karıştırma.

## Ölçüm sınırı

Hazır kayıtlar üzerinde çalışılan bu oturumda süre **görev tamamlama süresi**dir; uçtan uca veri giriş süresi değildir. Görev kartı gösterildiğinde başlat, katılımcı bitirdiğinde veya durdurduğunda durdur. Yardımı, kesintiyi ve terk edilen görevleri ayrıca kaydet.

Karşılaştırmalı deney için önce gerçek kullanıcı yöntemini belirlemek, iki araca eşit kaynak/çeviri desteği vermek, veri giriş yükünü dahil etmek ve farklı eşdeğer görev setleri hazırlamak gerekir. Bu altı görevi iki araçta peş peşe yaptırıp aradaki farkı ürün kazancı diye sunma. Ayrıntı: [değerlendirme planı](../VALIDATION_PLAN.md).

Tüm kaynak metinler Türkçedir. Bu paket TR/EL/EN başarısını ölçmez; Yunanca değerlendirici bulunmuş gibi göstermez.
