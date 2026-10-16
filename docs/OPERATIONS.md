# İşletim ve sürüm doğrulama — İnsan onaylı ihtiyaç koordinasyonu

Son inceleme: **16 Ekim 2026**. Bu belge kurulum, veri akışı, sürüm kapıları, geri dönüş ve doğrulama kapsamını birlikte kaydeder. Bir yayın adresinin açılması, tüm üretim koşullarının tamamlandığı anlamına gelmez.

## Sürüm kanıtı

- Denetlenen uygulama commit’i: `fe08e234b36d753001cfcfc7ec160468008a0224`.
- [Bu commit için başarılı CI kaydı](https://github.com/busrabuseucar/ortak-olay/actions/runs/38921030614).
- Doğrulanan otomatik kapsam: 54 backend + 4 tarayıcı akışı.
- Testlerin gerçek servis, veri veya donanım yerine taklit kullandığı noktalar aşağıda açıkça ayrılmıştır.

## Kurulum ve çalışma

Depo kökünde, README’deki çalışma zamanı sürümüyle:

```sh
python -m venv .venv
python -m pip install -c constraints-ai-py312.txt -r requirements-ai.txt
python -m pytest -q
python scripts/evaluate_matching.py --output evaluation/local-verification.json
```

Veri akışı: Bearer kimlikli FastAPI → SQLite sürümlü kararlar → isteğe bağlı yerel CPU embedding → insan kararı.

Yapılandırma: ORTAK_REVIEWERS değerleri sunucu ortamında; gizli anahtarları Git’e koyma. ORTAK_MODEL_CACHE yerel model önbelleğidir. Sites tatbikatı ayrı, statik ve tarayıcıda çalışan gösterimdir.

## Yayın ve geri dönüş

1. Temiz checkout ve kilitli bağımlılıklarla yukarıdaki kontrolleri çalıştır. İlgili CI başarısını commit SHA ile eşleştir.
2. Yayın paketine yalnızca çalışma zamanı dosyalarını koy. Secret, ham kullanıcı verisi, yerel veritabanı ve kişisel hazırlık notları pakete girmemeli.
3. Hedef proje, kaynak commit, ortam ve yayın sürümünü kaydet. Önceki çalışan sürüm kimliğini geri dönüş için koru.
4. Yayından sonra ana kullanıcı akışını, hata durumunu ve varsa kalıcılığı doğrula. Sunucu hatası/yanlış sonuçta yeni yazmaları durdur; önceki doğrulanmış yayını geri al.
5. Şema değiştiyse yalnızca kodu geri almak yeterli değildir. Yedekten ayrı ortamda doğrulama yapmadan canlı veri üzerine yazma.

## Veri saklama ve kurtarma

SQLite için tutarlı backup API kopyası al; dosyayı çalışan WAL veritabanından tek başına kopyalama. Yedeği ayrı ortamda açıp integrity_check, kayıt/bağlantı/karar sayımları ve yetkili okuma ile doğrula. Gerçek geri yükleme tatbikatı henüz yapılmadı.

## Gerçek servis, model ve cihaz doğrulaması

16 Ekim gerçek ONNX CPU modeli 18 sentetik örnekte yeniden çalıştırıldı: kontrollü semantic precision/recall 0.7778; 2 yanlış aday. evaluation/verification-2026-10-16.json tam sonuçtur. Bağımsız saha doğruluğu, kurum izolasyonu ve rol modeli henüz doğrulanmadı.

## Yayın sonrası gözlem

Önce küçük ve sentetik girdilerle temel akışı kontrol et. Beklenmeyen hata, boş ekran, yanlış hesap, yetkisiz erişim veya veri kaybında tarih, uygulama commit’i, ortam ve yeniden üretme adımlarını kaydet; kişisel veri ve secret ekleme. Statik araçlarda tarayıcı konsolu/ağ hatalarını; backend bulunan projelerde durum kodu, gecikme ve hata oranını incele. Bu belgede sürekli izleme veya otomatik geri dönüş kurulmuş olduğu iddia edilmez.

## Kabul kaydı

Her yeni sürümün kaydı; test komutu/sonucu, kaynak SHA, yayın sürümü, gerçek servis/model sürümü, cihaz/işletim sistemi, veri kümesi özeti ve geri dönüş denemesini içermeli. Erişim veya fiziksel donanım yoksa ilgili satır **çalıştırılmadı** olarak tutulur; otomatik test başarısı yerine geçirilmez.
