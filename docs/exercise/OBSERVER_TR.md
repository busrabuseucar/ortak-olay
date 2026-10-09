# Gözlemci kurulum ve değerlendirme anahtarı

**Katılımcıya önceden gösterme.** Bu anahtar geliştirme ekibinin hazırladığı sentetik beklentilerdir; bağımsız uzman tarafından doğrulanmış altın etiketler değildir. Katılımcı gerekçeli başka bir yol önerirse aynen kaydet ve alan uzmanıyla değerlendir.

## Ortak kurulum

Her mesajı arayüzde elle gir. Dil Türkçe, kaynak “Sentetik tatbikat kaynağı”, mesaj türü ihtiyaç mesajlarında “İhtiyaç bildirimi”, teslimatta “Güncelleme” olsun. Olay zamanı için 1 Eylül 2026 kullan; kayıt sırasını izleyen dakika değerleri ver. Eski mesaj tekrarında ilk olay zamanını koru. Alınma zamanı uygulama tarafından otomatik verilir.

Konum etiketlerini aşağıdaki gibi birebir kullan. Grup alanında verilen kodu yaz; belirtilmeyen alan boş kalsın. Miktar girersen birimi birlikte gir. Önceden kurduğun ihtiyaçları gerekçeyle onayla; durum kapatmak için ilgili teslimat kaynağını önce bağla. Katılımcı görevini başlatmadan hazırlığı tamamla.

### Görev 1: Tatbikat A

Ön kayıt: “Çadır 12 için su gerekiyor.” Su kategorisi, grup tent-12; ayrı açık ihtiyaç oluştur.
Yeni kayıt: “Çadır 98 için su gerekiyor.” Su kategorisi, grup tent-98; henüz bağlama.

Beklenti: İki farklı grup ayrı kalır; yeni rapor kendi açık ihtiyacını oluşturur. Bilinen grup çatışmasında API birleşmeye izin vermemeli.
Kritik hata: Grupların aynı olaymış gibi değerlendirilmesi. Engellenen girişimi de gözlemle; API'nin engellemesi katılımcının doğru anladığını tek başına göstermez.

### Görev 2: Tatbikat B

Ön kayıt: “20 kişinin suya ihtiyacı var.” Su, grup boş, miktar 20, birim kişi; açık ihtiyaç oluştur.
Yeni kayıt: “Burada 30 kişinin suya ihtiyacı var.” Su, grup boş, miktar 30, birim kişi; henüz bağlama.

Beklenti: Çelişkiyi görmesi ve aynı grup bilgisini istemesi. Yeterli bilgi olmadığı için kesin bağlama/ayırma kararını ertelemesi kabul edilebilir. Arayüzde ayrı bir açıklama isteme işlemi yoktur; sözlü açıklama ve raporu beklemede bırakma kayıt altına alınır.
Kritik hata: 50 kişi sonucunu çıkarmak veya yalnızca yeni mesaj diye 30'u kesin doğru saymak.
Not: Doğru davranış burada mutlaka bir düğmeye basmak değildir.

### Görev 3: Tatbikat C

Aynı konum ve tent-12 için “Su gerekiyor.” ve “Bebek bezi gerekiyor.” mesajlarından iki ayrı açık ihtiyaç oluştur.
Teslimat kaydı: “Çadır 12'nin su ihtiyacı tamamen karşılandı. Bebek bezi hâlâ gerekli.” Su kategorisi, tent-12, güncelleme; henüz bağlama.

Beklenti: Teslimatı su ihtiyacına bağlamak, gerekçe ve kaynakla yalnızca suyu karşılandı yapmak. Bebek bezi açık kalmalı.
Kritik hata: Bebek bezini de kapatmak veya teslimatı kanıt göstermeden kapatma yapmak.
Not: Bu görev farklı ihtiyaç türlerini ayırır; aynı ihtiyaç içindeki kısmi miktar teslimatını ölçmez.

### Görev 4: Tatbikat D

tent-12 için “Çadır 12 için su gerekiyor.” mesajıyla ihtiyaç aç.
“Çadır 12'nin su ihtiyacı tamamen karşılandı.” güncellemesini aynı su ihtiyacına bağla ve kaynakla karşılandı yap.
İlk talebin metnini birebir tekrar gir; ilk olay zamanını ve tent-12 kodunu koru; bağlama.

Beklenti: Yeniden paylaşımı ve kapalı durumu fark etmek; yeni ihtiyaç kanıtı olmadan durumu açık yapmamak. Gerekçeyle aynı kayda bağlamak veya belirsizliği çözmek üzere bekletmek kabul edilebilir.
Kritik hata: Alınma zamanını yeni olay sanıp ihtiyacı otomatik yeniden açmak.

### Görev 5: Tatbikat E

Ön mesaj: “Su gerekiyor.” Su kategorisi, tent-12. Açık ihtiyaç oluştur. Bu grup etiketi kasıtlı yanlış anotasyondur.
Katılımcıya kaynak teyidinin tent-98 olduğunu bildir; özgün mesajı değiştirmesini isteme.

Beklenti: Grup alanını tent-98 yapmak; gerekçe ve bağlantıyı kaldırma onayı vermek. Rapor bağlantısız kuyruğa dönmeli, eski ihtiyaç yeniden inceleme gerekli diye işaretlenmeli. Katılımcı bu işaretin ne anlama geldiğini açıklamalı.
Eski kaydın tarihsel durumu/grup etiketi korunur. Otomatik düzeltilmiş veya kesin geçerli sayılmaz. Yeni rapor ayrı bir ihtiyaç olarak değerlendirilebilir.
Kritik hata: Kaynak metni yeniden yazmaya çalışmak veya eski kaydı hâlâ doğrulanmış sanmak.
Eski kaydın boş kalması ve bunu sonuçlandırma ihtiyacı ayrıca ürün geri bildirimi olarak kaydedilir.

### Görev 6: Tatbikat F

Ön mesaj: “Burada su gerekiyor.” Su kategorisi, grup boş; açık ihtiyaç oluştur.
Yeni mesaj: “Su talebimiz var.” Aynı konum/kategori, grup boş; bağlama. Aynı konum kuralı öneri üretir.

İlk karttaki sözlü teyit, arayüze henüz grup kodu olarak girilmemiş dış bilgidir.
Beklenti 1: Öneriyi gerekçeyle reddetmek; yenilemeden sonra ret görünür olmalı.
Sonra ikinci bilgi kartını göster.
Beklenti 2: Ret kararını gerekçeyle yeniden değerlendirmeye açmak; teyitli eşleşmeye bağlamak. Önceki ret ve geri alma geçmişte kalmalı.
Kritik hata: Önceki kararı silmek veya aktif reddi kaldırmadan bağlantı kurulduğunu sanmak.
Bu görev geri alma akışını sınar. Kaynak sürümü değişince reddin geçersizleşmesi ayrı teknik testlerle kontrol edilir; bu oturumdan o davranışın kullanıcı tarafından anlaşıldığı sonucu çıkarılmaz.

## Kayıt ilkeleri

Görev durumları: tamamlandı / kısmen tamamlandı / tamamlanmadı / katılımcı bıraktı / teknik engel.
Karar değerlendirmesi: anahtarla uyumlu / gerekçeli alternatif / hatalı / belirsiz.
Süreye müdahale etme; kesintileri ve yardımı ayrıca kaydet. Yardımlı başarıyı bağımsız başarı diye yazma.
Teknik olarak engellenen yanlış girişim ile kaydedilmiş yanlış nihai karar ayrı sütunlardır.
