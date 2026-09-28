# Crash notları

Sebebi henüz bulunamamış çökmeler. Oyun bu dosyayı okumaz; sadece not.

---

## 1. Teutonic Order (TEU) seçilince çökme (2026-09-28, şimdilik kenarda)

**Belirti**
- 1512 kampanya kaydında (`mp_ita_1512_10_18_4ae7b32e-…eu5`, Steam bulutunda; kayıt adı "yeterlidur ADAS") Teutonic seçilince oyun çöküyor.
- İki yoldan da oluyor: kayıt açılırken haritadan Teutonic'e tıklayınca ve debug modunda ülke değiştirirken.
- Diğer ülkelerde sorun yok. Livonya Tarikatı, cumhuriyetler ve 20-25 farklı ülke denendi, hepsi açılıyor. Tek ülkeye özgü bir sorun.
- Arkadaşım aynı çökmeyi Workshop sürümüyle de gördü.
- **Aynı kampanyanın 32 yıl önceki kaydında (1480) Teutonic sorunsuz açılıyor.** Yani 1480 ile 1512 arasında Teutonic'te bir şey oluşuyor ya da bir şey onu tetikliyor.
- Her seferinde çökmüyor; bir kez açıldı, sonra yine çöktü.

**Modla ilişkisi**
- Mod tamamen kapalıyken de çöktü. 28 Eylül'deki iki crash raporunda mod listesi boş, çökme yeri aynı.
- Yani sebep kaydın içindeki Teutonic verisi ile oyunun kendi hatası; güncel mod dosyaları tek başına çöktürmüyor.
- Ama kampanya Balance ile oynandığı için bu verinin oyun sırasında modun bir şeyiyle oluşmuş olması hâlâ mümkün.
- Test olarak mod koloni işlerinden önceki 25 Eylül hâline ve 25 Ağustos hâline de döndürüldü; ikisinde de çöktü.

**Crash raporundaki imza** (`Documents\Paradox Interactive\Europa Universalis V\crashes\` altındaki `exception.txt` ve `minidump.dmp`)
- `Unhandled Exception C0000005` (boş gösterici okuma; `rcx = 0`).
- Çöken adres: `eu5.exe+0x79373f` (bazen `+0x7937a7`).
- Çağrı zinciri:
  1. Oyunun komut işleyicisi (`ingame_idler_logic` HandleMessage, `eu5.exe+0x44c5f8f`)
  2. Oyuncu ülkesi değişimi (`gamestate`, `eu5.exe+0x4108534`; yanında "OBSERVER", "Getting player in synchronous state" yazıları)
  3. Bir veritabanı erişimi (`eu5.exe+0x45dcadc`; yanında "Invalid Element Index", "Nonexistent event key")
  4. Çöken fonksiyon
- Çok oyunculu kontrol komutları kodunda (`jomini/.../controlcommands.cpp`, satır 458).
- Hata kaydına (`error.log`) çökme anında hiçbir şey yazılmıyor.
- `exception.txt`'teki fonksiyon adları (`AK::Monitor::PostCodeVaList`, `ffxFsr2ResourceIsNull`…) yanıltıcı: bunlar en yakın dışa açık sembol, asıl yer yukarıdaki adresler.

**1512 kaydında elenenler** (Teutonic, Livonya ile ve kayıttaki 2.472 ülkenin hepsiyle karşılaştırıldı)
- Tanımlar: Teutonic'in ülke tanımı, hükümdarları, başlangıç ayarları. Mod bunlara dokunmuyor.
- Hükümet: yasalar, reformlar, ayrıcalıklar, toplumsal değerler, kültürler.
- Zümreler ve isyancılar: Teutonic'in 3 zümre isyancısı var, hepsi geçerli ve pop'ları yerinde.
- Diğer kayıtlar: kabine eylemleri, planlanmış olaylar, görev ağacı, yapay zeka hafızası, binalar.
- Oyuncu geçmişi: Teutonic bu çok oyunculu oyunda hiç bir oyuncunun ülkesi olmamış.
- Teutonic'e özgü çıkanların hepsi oyunun kendi içeriği:
  - `kulm_law`
  - `agrarian_constitution` (foreign_cultural_law)
  - `teu_*` ilerlemeleri
  - `recently_requested_aid` bekleme süresi
  - `kulm_law_revised` değişkeni

**Sonra bakmak için**
- 1480 kaydı (çalışıyor) ile 1512 kaydı (çöküyor) arasında Teutonic'in verisindeki farklar.

---

## 2. Cheat Menu Pro ile birlikte açınca bazen çökme

- İmza: `eu5.exe+0x2a0cc2f` (bir kez `+0x2a0cc2c`).
- Mod kapalıyken de bir kez oldu, yani oyunun kendisinden olabilir.
- Modun eski 25 Ağustos sürümünde Cheat Menu'nün bina seçicisi var olmayan binaları arıyordu (`korean_barracks`, `provincial_garrison`, `sofa_stockade`; `sakuya_building_picker_sgui.txt`). Mod oyunun bina dosyalarını eski hâlleriyle değiştirdiği için bu binalar yoktu.
- Güncel sürümde Cheat Menu'nün aradığı bütün binalar, mallar ve birimler mevcut.
- Cheat Menu Pro, **Community Mod Framework**'e bağımlı. Framework sette yoksa sadece Cheat Menu'nün ayar kaydı eksik kalıyor; çökme sebebi değil.
- İki mod arasında aynı isimde tanım yok.

---

## Çökme olunca

- Crash penceresi açıkken **Send'e basmadan önce** `crashes\` klasöründeki son klasörü (`exception.txt`, `minidump.dmp`, `logs\`) bir kenara kopyala; gönderince siliniyor.
- Oyunu yeniden açma: `logs\` klasörü her açılışta sıfırlanıyor.
- `meta.yml`'deki `Mod_` satırları o oturumda hangi modların yüklü olduğunu gösterir.
