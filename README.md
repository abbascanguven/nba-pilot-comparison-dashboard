# NBA Pilot Karşılaştırma Dashboard'u

Pilot ve NBA'in satış oranlarını, satış adetlerini ve olumlu yanıt oranlarını karşılaştıran bir Streamlit dashboard'u. Veriyi Oracle'daki tek bir tablodan okur.

- **Günlük Trend** (ana sayfa): Pilot ve NBA satış oranı ile satış adedinin gün gün seyri.
- **Dönem Karşılaştırması**: Seçilen dönem için aksiyon grup kodu bazında Pilot/NBA karşılaştırması.

---

## İçindekiler

1. [Gereksinimler](#1-gereksinimler)
2. [Kurulum (ilk sefer)](#2-kurulum-ilk-sefer)
3. [Bağlantı ayarları (.env)](#3-bağlantı-ayarları-env)
4. [Streamlit'i ayağa kaldırma](#4-streamliti-ayağa-kaldırma)
5. [Dashboard'u kullanma](#5-dashboardu-kullanma)
6. [Önemli ve hariç tutulan tarihleri girme](#6-önemli-ve-hariç-tutulan-tarihleri-girme)
7. [Hesaplamalar ve filtreler (detaylı)](#7-hesaplamalar-ve-filtreler-detaylı)
8. [Sorun giderme](#8-sorun-giderme)
9. [Proje yapısı](#9-proje-yapısı)

---

## 1. Gereksinimler

- **Python 3.11 veya üzeri.** Sürümü kontrol etmek için: `python --version`
- Oracle veritabanına ağ erişimi (şirket ağı veya VPN)
- Tabloyu okuma (`SELECT`) yetkisi olan bir Oracle kullanıcısı

Oracle Instant Client kurmanız **gerekmez**. Bağlantı `python-oracledb` kütüphanesinin *thin mode*'u ile yapılır.

---

## 2. Kurulum (ilk sefer)

Aşağıdaki komutları proje klasöründe (`nba-pilot-comparison-dashboard`) çalıştırın. Örnekler Windows PowerShell içindir.

**a) Sanal ortam oluşturun ve etkinleştirin.** İsteğe bağlı ama önerilir, projenin kütüphaneleri diğer Python projelerinizden ayrı kalır.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> PowerShell "running scripts is disabled" hatası verirse önce şunu bir kez çalıştırın:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Etkinleştirince komut satırının başında `(.venv)` yazısı görünür. Dashboard'u her başlattığınızda bu adımı tekrarlamanız gerekir.

**b) Kütüphaneleri kurun:**

```powershell
pip install -r requirements.txt
```

**c) Ayar dosyasını oluşturun:**

```powershell
Copy-Item .env.example .env
```

Ardından `.env` dosyasını bir metin editörüyle açıp doldurun (bkz. bir sonraki bölüm).

---

## 3. Bağlantı ayarları (.env)

`.env` dosyası şifre içerdiği için **git'e gönderilmez**. Her kullanıcı kendi bilgisayarında oluşturur.

### Oracle'dan okumak için

```ini
DATA_SOURCE=oracle
ORACLE_USER=kullanici_adi
ORACLE_PASSWORD=sifre
ORACLE_DSN=db-sunucu.sirket.local:1521/SERVIS_ADI
ORACLE_TABLE=SEMA_ADI.TABLO_ADI
```

| Alan | Açıklama |
|---|---|
| `ORACLE_DSN` | `host:port/service_name` biçiminde. SQL Developer'daki bağlantı ayarlarından (Hostname, Port, Service name) alınabilir. |
| `ORACLE_TABLE` | Şema adıyla birlikte tablo ya da view adı. |

### Oracle olmadan denemek için (örnek dosya)

```ini
DATA_SOURCE=file
SAMPLE_DATA_PATH=data/demo_timeseries.tsv
```

`data/demo_timeseries.tsv` dosyası **sentetik** (uydurma) bir test verisidir ve şu komutla üretilir:

```powershell
python scripts/make_demo_data.py
```

Bu komut `data/sample_data.tsv` dosyasındaki aksiyon gruplarını baz alır ve 30 günlük, 1 ve 7 günlük pencereli veri üretir. Bu veri gerçek değildir, sadece ekranları denemek içindir.

### Bağlantıyı test etme

Dashboard'u açmadan önce verinin okunabildiğini şu komutla kontrol edebilirsiniz:

```powershell
python -c "from nba_dashboard.data import load_data; df, src = load_data(); print(src, df.shape)"
```

Kaynak adı ve satır sayısı ekrana geliyorsa bağlantı çalışıyor demektir.

---

## 4. Streamlit'i ayağa kaldırma

### Başlatma

Sanal ortam etkinken proje klasöründe şunu çalıştırın:

```powershell
streamlit run app.py
```

Birkaç saniye sonra tarayıcı otomatik açılır. Açılmazsa terminalde yazan adrese kendiniz gidin:

```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

> `streamlit` komutu bulunamazsa aynı işi şu komut da yapar: `python -m streamlit run app.py`

### Diğer kullanıcıların erişmesi

Dashboard'u açan bilgisayar bir tür sunucu gibi çalışır. Aynı ağdaki diğer kişiler terminaldeki **Network URL** adresini (ör. `http://192.168.x.x:8501`) kendi tarayıcılarında açarak dashboard'u görebilir. Bunun için:

- Dashboard'u başlatan bilgisayar açık kalmalı ve terminal kapatılmamalı.
- Windows Güvenlik Duvarı ilk seferde Python için izin isteyebilir. **Özel ağlar** için izin verin.
- Sabit bir sunucuya taşımak isterseniz aynı adımlar o sunucuda uygulanır.

### Farklı port kullanma

8501 portu doluysa başka bir port seçebilirsiniz:

```powershell
streamlit run app.py --server.port 8502
```

### Durdurma

Dashboard'un çalıştığı terminalde `Ctrl + C` tuşlarına basın.

### Her gün kullanım için özet

```powershell
cd <proje klasörü>
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

---

## 5. Dashboard'u kullanma

### Veri ne zaman yükleniyor?

Veri, dashboard açıldıktan sonraki ilk ziyarette Oracle'dan **bir kez** okunur ve bellekte tutulur. Filtreleri değiştirmek Oracle'a tekrar gitmez, bu yüzden ekranlar hızlı çalışır. Tüm kullanıcılar aynı kopyayı görür.

Oracle'daki tablo güncellendiyse sol menüdeki **Veriyi yenile** butonuna basın.

### Ortak filtreler (sol menü, iki sayfada da geçerli)

| Filtre | Ne işe yarar |
|---|---|
| **Periyot** | 1 günlük veya 7 günlük hesaplama penceresi (`HESAPLAMA_GUN_SAYISI`). |
| **Hesaplama bazı** | *Tekil*: tekil müşteri sayıları. *Toplam*: toplam yanıt ve satış adetleri. |
| **Model durumu** | Tümü / Modelli (`MODEL_FLAG = 1`) / Modelsiz. |
| **Model** | Bir veya birden fazla model seçer. Boş bırakılırsa hepsi dahil olur. |
| **Aksiyon grup kodu** | `ACTION_GROUP_CODE` ile bir veya birden fazla aksiyon grubu seçer (ör. `1001 · Banka Kartı Satış`). Kod ya da açıklama yazılarak aranabilir. Boş bırakılırsa hepsi dahil olur. |
| **Hariç tutulan tarihleri çıkar** | Açıkken `config/haric_tutulan_tarihler.toml` dosyasındaki tarihlere denk gelen veriler tüm hesaplamalardan çıkarılır (bkz. [6.2](#62-hariç-tutulan-tarihler)). Yalnızca dosyada en az bir kayıt varsa görünür. Varsayılan: kapalı. |

Sayfa değiştirdiğinizde bu filtrelerin seçimleri korunur.

### Günlük Trend sayfası

- **Tarih aralığı:** Grafiklerde gösterilecek günleri seçer.
- **Karşılaştırma referansı:**
  - *Bir önceki gün*: Son günün değerleri bir önceki günle karşılaştırılır.
  - *Seçilen gün*: Açılan **Referans günü** listesinden istediğiniz günü seçersiniz. Özet kartlarındaki değişimler o güne göre hesaplanır ve o gün grafiklerde gri noktalı çizgiyle işaretlenir.
  - *Son günlerin ortalaması* (**varsayılan**): Son gün, kendisinden önceki N günün ortalamasıyla karşılaştırılır. N, **Ortalama alınacak gün sayısı** alanından seçilir (varsayılan 30). Referans aralığı grafiklerde gri bantla gösterilir. Hariç tutulan günler ortalamaya girmez.
- **Özet kartları:** Son günün Pilot/NBA satış oranı, satış lift ve satış adetleri. Kartın yanındaki **?** simgesinin üzerine gelince referans günün değeri görünür.
- **Grafikler:**
  - *Satış oranı*: Pilot ve NBA karşılaştırmalı.
  - *Satış adedi*: Pilot ve NBA karşılaştırmalı.
  - *Satış lift*: Açılır bölümde.
  - *Satış adet farkı (Pilot − NBA)*: Açılır bölümde. `Pilot satış − NBA satış` farkının günlük çizgi grafiği. 0'ın üstü (mavi nokta): Pilot daha fazla satmış, altı (turuncu nokta): NBA daha fazla satmış.
  - *Yanıtlayan adedi (Pilot ve NBA)*: Açılır bölümde. Seçili baza göre (Tekil / Toplam) günlük yanıtlayan sayıları. Satış oranlarının paydasıdır.

  Grafiklerde bir günün üzerine gelince o günün tüm değerleri görünür. Sağ üstteki araçlarla yakınlaştırabilir veya grafiği PNG olarak indirebilirsiniz.
- **Günlük değerler tablosu:** Açılır bölümde. **Excel için CSV indir** butonuyla dışa aktarılır.

> **7 günlük periyot hakkında:** Her nokta, o tarihte biten 7 günlük pencerenin toplamıdır. Ardışık günlerin pencereleri üst üste bindiği için eğri 1 günlük görünüme göre daha yumuşaktır.

### Dönem Karşılaştırması sayfası

- **Dönem:** Karşılaştırılacak pencereyi seçer. Varsayılan olarak en güncel dönem seçilidir.
- **Min. yanıtlayan:** Pilot veya NBA tarafında bu sayıdan az yanıtlayanı olan aksiyon grupları hariç tutulur. Çok küçük gruplardaki yanıltıcı lift değerlerini ayıklamak için kullanılır.
- **Sekmeler:**
  - *Aksiyon grupları*: Her grubun Pilot satış oranının NBA'ya göre yüzde farkı. Mavi: Pilot anlamlı olarak daha iyi, turuncu: NBA anlamlı olarak daha iyi, gri: fark istatistiksel olarak anlamlı değil.
  - *Pilot ve NBA oranları*: Her aksiyon grubu bir nokta. Kesikli çizginin üstünde kalan gruplarda Pilot daha iyi.
  - *AG grup kodu bazında*: Her aksiyon grup kodu için Pilot ve NBA satış oranları yan yana (grafik + tablo).
  - *Detay tablo*: Tüm metrikler. Sonuca göre filtrelenebilir ve CSV olarak indirilebilir.

---

## 6. Önemli ve hariç tutulan tarihleri girme

İki ayrı tarih listesi vardır:

| Dosya | Grafikte | Hesaplamaya etkisi |
|---|---|---|
| `config/onemli_tarihler.toml` | Mor kesikli çizgi + 📌 | Yok, sadece bilgi amaçlı |
| `config/haric_tutulan_tarihler.toml` | Kırmızı çizgi / kırmızı bant + ⛔ | Filtre açıkken bu tarihler hesaplamadan çıkarılır |

### 6.1 Önemli tarihler

Kampanya başlangıcı, model değişikliği gibi olayları trend grafiklerinde işaretlemek için [`config/onemli_tarihler.toml`](config/onemli_tarihler.toml) dosyasını düzenleyin. Her tarih için bir blok ekleyin:

```toml
[[tarih]]
gun = "01.09.2026"
baslik = "Kampanya başlangıcı"
aciklama = "Kredi kartı kampanyası tüm kanallarda yayına alındı."

[[tarih]]
gun = "15.09.2026"
baslik = "Model güncellemesi"
```

| Alan | Zorunlu mu? | Açıklama |
|---|---|---|
| `gun` | Evet | `GG.AA.YYYY` biçiminde tarih. |
| `baslik` | Evet | Kısa başlık. |
| `aciklama` | Hayır | Üzerine gelince görünen detay. |

- Grafiklerde her tarih mor kesikli çizgi ve 📌 simgesiyle işaretlenir. Simgenin veya o günün üzerine gelince başlık ve açıklama görünür.
- Grafiklerin altındaki **📌 Önemli tarihler** bölümü, seçili aralıktaki kayıtları liste olarak gösterir.
- Dosya her sayfa yenilemesinde tekrar okunur. Kaydettikten sonra tarayıcıyı yenilemeniz yeterlidir, dashboard'u yeniden başlatmanız gerekmez.
- Hatalı bir kayıt (yanlış tarih biçimi, eksik başlık) atlanır ve sayfada uyarı gösterilir.
- Metin içinde çift tırnak kullanmanız gerekirse tek tırnakla yazın: `baslik = 'Kampanya "Yaz"'`

### 6.2 Hariç tutulan tarihler

Sistem kesintisi, veri yükleme hatası gibi sonuçları bozan günleri [`config/haric_tutulan_tarihler.toml`](config/haric_tutulan_tarihler.toml) dosyasına girin. Her kayıt **tek bir gün** ya da **bir aralık** olabilir:

```toml
# Tek gün
[[haric]]
gun = "05.09.2026"
baslik = "Sistem kesintisi"
aciklama = "Kampanya motoru gün boyu çalışmadı."

# Aralık (başlangıç ve bitiş günleri dahil)
[[haric]]
baslangic = "10.09.2026"
bitis = "12.09.2026"
baslik = "Veri yükleme hatası"
```

| Alan | Zorunlu mu? | Açıklama |
|---|---|---|
| `gun` | Tek gün için | `GG.AA.YYYY` |
| `baslangic`, `bitis` | Aralık için | `GG.AA.YYYY`. İki gün de aralığa dahildir. `bitis`, `baslangic`'tan önce olamaz. |
| `baslik` | Evet | Kısa başlık |
| `aciklama` | Hayır | Üzerine gelince görünen detay |

**Grafiklerde görünüm:**
- Tek gün: kırmızı kesikli dikey çizgi.
- Aralık: kırmızı gölgeli bant, iki kenarında kırmızı kesikli çizgi.
- Üstteki ⛔ simgesinin üzerine gelince başlık, tarih(ler) ve açıklama görünür.
- İşaretler filtre açık da olsa kapalı da olsa her zaman gösterilir.

**Sol menüdeki "Hariç tutulan tarihleri çıkar" seçeneği:**
- **Açık:** Bu tarihlere denk gelen veriler özet kartlarından, grafiklerden, tablolardan ve Dönem Karşılaştırması sayfasından çıkarılır. Trend grafiklerinde bu günler **boşluk** olarak görünür, çizgi o günlerde kesilir. Seçeneğin altında kaç günün çıkarıldığı yazar.
- **Kapalı (varsayılan):** Veriler hesaplamaya dahil edilir. Kırmızı işaretler yine de görünür, üzerine gelince o günün değerlerinin yanında hariç tutma notu da çıkar.

> **7 günlük periyotta dikkat:** 7 günlük değerler Oracle'da hazır toplam olarak gelir, bir pencerenin içinden tek bir gün çıkarılamaz. Bu yüzden hariç tutulan bir günü **içeren tüm pencereler** çıkarılır. Örneğin 05.09 hariç tutulursa, 05.09–11.09 arasında biten 7 pencerenin hepsi hesaplamadan çıkar. 1 günlük periyotta ise yalnızca o gün çıkar.

- Dosya her sayfa yenilemesinde tekrar okunur, dashboard'u yeniden başlatmanız gerekmez.
- Hatalı bir kayıt (yanlış tarih biçimi, eksik başlık, ters aralık) atlanır ve sol menüde uyarı gösterilir.
- Grafiklerin altındaki **⛔ Hariç tutulan tarihler** bölümü, seçili aralıktaki kayıtları ve seçeneğin şu anki durumunu gösterir.

---

## 7. Hesaplamalar ve filtreler (detaylı)

Bu bölüm, dashboard'daki her sayının nereden geldiğini, hangi formülle hesaplandığını ve filtrelerin veriyi hangi sırayla daralttığını anlatır. Kodda nerede yapıldığı parantez içinde belirtilmiştir.

### 7.1 Veri hazırlama: Oracle tablosundan ekrana

Tablo okunduktan sonra (`nba_dashboard/data.py` → `_clean`) sırasıyla şu adımlar uygulanır:

| # | Adım | Ayrıntı |
|---|---|---|
| 1 | Kolon adlarını düzeltme | Türkçe karakterler ve boşluklar temizlenir, adlar büyük harfe çevrilir. Örnek: `Hesaplama Gün sayısı` → `HESAPLAMA_GUN_SAYISI`. |
| 2 | Toplam satırlarını atma | Sadece `SIRALAMA_DEGERI = 1` (aksiyon grubu detayı) satırları tutulur. `2` (MODEL_FLAG=1 toplamı) ve `3` (genel toplam) satırları kullanılmaz, çünkü toplamlar filtrelere göre yeniden hesaplanır (bkz. 7.3). |
| 3 | Boş kodları atma | `ACTION_GROUP_CODE` boş olan satırlar atılır. |
| 4 | Adetleri sayıya çevirme | 12 adet kolonu (`PILOT/NBA` × `TEKIL/TOPLAM` × `YANITLAYAN/OLUMLU/SATIS`) tam sayıya çevrilir. **Boş hücreler 0 kabul edilir.** Örneğin NBA tarafı tamamen boş olan bir aksiyon grubunda NBA yanıtlayan 0 olur ve bu grup "Karşılaştırma yok" sonucunu alır. |
| 5 | Tarihleri çevirme | `RUN_ALINAN_TARIH`, `FIRST_OFFER_DATE`, `LAST_OFFER_DATE` tarih tipine çevrilir (gün.ay.yıl). |
| 6 | Mükerrer çalıştırmaları eleme | Aynı pencere birden fazla kez çalıştırılmışsa yalnızca **en son `RUN_ALINAN_TARIH`** satırları tutulur. Bir pencereyi şu dört kolon birlikte tanımlar: `INJECTION_POINT_ID`, `FIRST_OFFER_DATE`, `LAST_OFFER_DATE`, `HESAPLAMA_GUN_SAYISI`. |
| 7 | Metinleri düzeltme | Kod ve açıklamadaki baştaki ve sondaki boşluklar silinir. `MEVCUT_MODEL_KIMLIGI` boşsa `(Model yok)` yazılır. |
| 8 | Dönem etiketi | Her satıra `DONEM` etiketi eklenir: `FIRST_OFFER_DATE – LAST_OFFER_DATE (N gün)`, ör. `16.09.2026 – 22.09.2026 (7 gün)`. |

> **Tablodaki hazır oran ve lift kolonları kullanılmaz.** `PILOT_TEKIL_SATIS_ORAN`, `TEKIL_SATIS_LIFT`, `ADET_LIFT`, `SATIS_ADET_FARKI` gibi kolonlar hesaplamalara girmez. Tüm oran, lift ve farklar 12 adet kolonundan yeniden hesaplanır. Böylece hangi filtre seçilirse seçilsin sonuçlar tutarlı kalır.

### 7.2 Hesaplama bazı: Tekil / Toplam

Sol menüdeki **Hesaplama bazı** satırları süzmez. Hesaplamada **hangi adet kolonlarının** kullanılacağını seçer:

| Seçim | Kullanılan kolonlar |
|---|---|
| **Tekil** | `PILOT_TEKIL_YANITLAYAN`, `PILOT_TEKIL_OLUMLU`, `PILOT_TEKIL_SATIS` ve NBA karşılıkları |
| **Toplam** | `PILOT_TOPLAM_YANITLAYAN`, `PILOT_TOPLAM_OLUMLU`, `PILOT_TOPLAM_SATIS` ve NBA karşılıkları |

Aşağıdaki formüllerde geçen "yanıtlayan", "olumlu" ve "satış" hep seçilen baza ait kolonlardır.

### 7.3 Toplama kuralı: önce adetler toplanır, sonra oran hesaplanır

Bir grafik noktası, özet kartı ya da tablo satırı birden fazla veri satırını kapsayabilir. Örneğin bir günün tüm aksiyon grupları ya da bir kodun tüm satırları. Bu durumda önce **adetler toplanır**, oranlar bu toplamlardan hesaplanır:

```
Pilot yanıtlayan = Σ PILOT_<BAZ>_YANITLAYAN
Pilot olumlu     = Σ PILOT_<BAZ>_OLUMLU
Pilot satış      = Σ PILOT_<BAZ>_SATIS
(NBA için aynı şekilde)
```

Oranların ortalaması **alınmaz**. Örnek (Tekil, iki aksiyon grubu):

| Aksiyon grubu | Pilot satış | Pilot yanıtlayan | Pilot satış oranı |
|---|---|---|---|
| 1001 Banka Kartı Satış | 191 | 37.842 | %0,505 |
| 1002 Banka Kartı Pin Belirleme | 1.596 | 31.158 | %5,122 |
| **Toplam (dashboard'un yöntemi)** | **1.787** | **69.000** | **%2,590** |
| Oranların basit ortalaması (kullanılmaz) | | | %2,814 |

Doğru sonuç %2,590'dır, çünkü bu yöntemde her müşteri eşit ağırlık taşır. Basit ortalama ise küçük bir grubu büyük bir grupla eşit sayar.

Bu yöntem Oracle'daki toplam satırlarıyla aynı sonucu verir. Örnek veride "MODEL FLAG = 1" satırındaki Tekil satış lift (1,1003) ve genel toplamdaki değer (1,0357), dashboard'un hesapladığı değerlerle birebir tutar.

> **Tekil sayılar hakkında:** Birden fazla aksiyon grubunun tekil yanıtlayanları toplandığında, birden fazla gruba yanıt veren bir müşteri her grupta ayrı sayılır. Oracle raporundaki toplam satırları da aynı şekilde hesaplandığı için iki kaynak birbiriyle tutarlıdır.

### 7.4 Metrik formülleri

Kodda `nba_dashboard/metrics.py` → `compare`. Aşağıda `P` Pilot, `N` NBA anlamına gelir.

| Metrik | Formül | Hesaplanamıyorsa |
|---|---|---|
| **Satış oranı** | `P satış oranı = P satış / P yanıtlayan`<br>`N satış oranı = N satış / N yanıtlayan` | Yanıtlayan 0 ise boş (–) |
| **Olumlu oranı** | `P olumlu oranı = P olumlu / P yanıtlayan`<br>`N olumlu oranı = N olumlu / N yanıtlayan` | Yanıtlayan 0 ise boş |
| **Satış lift** | `P satış oranı / N satış oranı` | NBA satış oranı 0 veya boşsa boş |
| **Olumlu yanıt lift** | `P olumlu oranı / N olumlu oranı` | NBA olumlu oranı 0 veya boşsa boş |
| **Adet farkı** | `P satış − N satış` | Her zaman hesaplanır |
| **Oran bazlı ek satış** | `P satış − (P yanıtlayan × N satış oranı)` | NBA satış oranı boşsa boş |
| **Oran farkı (puan)** | `(P satış oranı − N satış oranı) × 100` | İki oran da varsa hesaplanır |

**Nasıl yorumlanır:**
- **Lift = 1:** İki taraf eşit. **Lift > 1:** Pilot daha iyi. Örneğin lift 1,10, Pilot'un oranının NBA'dan %10 yüksek olduğu anlamına gelir.
- **Oran bazlı ek satış:** Pilot kitlesi NBA'nın oranıyla satsaydı ne kadar satış yapardı? Bu metrik, Pilot'un bunun üzerine kattığı satışı gösterir. Pilot ve NBA kitleleri farklı büyüklükteyse ham adet farkından daha adil bir göstergedir.

**Örnek 1: 1001 Banka Kartı Satış (Tekil, 5 günlük örnek veri)**

```
Pilot: 191 satış / 37.842 yanıtlayan  → satış oranı = %0,5047
NBA  : 162 satış / 40.934 yanıtlayan  → satış oranı = %0,3958
Satış lift          = 0,005047 / 0,003958           = 1,2753
Adet farkı          = 191 − 162                     = +29
Oran bazlı ek satış = 191 − 37.842 × 0,003958       = +41,2
Oran farkı          = (0,005047 − 0,003958) × 100   = +0,109 puan
```

**Örnek 2: Adet farkı neden yanıltabilir? (24071 Esnek Hesap Aktifleştirme)**

```
Pilot: 167 satış / 16.569 yanıtlayan  → %1,008
NBA  :  22 satış /    996 yanıtlayan  → %2,209
Adet farkı          = +145    ← Pilot çok daha iyi görünüyor
Satış lift          = 0,456   ← oranda Pilot, NBA'nın yarısı kadar
Oran bazlı ek satış = 167 − 16.569 × 0,02209 = −199
```

Pilot kitlesi NBA'nın yaklaşık 16 katı büyüklükte olduğu için ham adet farkı artı çıkıyor. Oysa oran bazlı ek satış eksi: Pilot, bu kitleye NBA'nın oranıyla satsaydı yapacağından yaklaşık 199 satış *az* yapmış.

### 7.5 Anlamlılık testi (iki oran z-testi)

Pilot ile NBA satış oranı arasındaki farkın tesadüf olup olmadığını ölçer. Seçili baza ait satış ve yanıtlayan adetleri kullanılır.

```
x₁ = P satış,  n₁ = P yanıtlayan,  p₁ = x₁ / n₁
x₂ = N satış,  n₂ = N yanıtlayan,  p₂ = x₂ / n₂

Ortak oran         p̂  = (x₁ + x₂) / (n₁ + n₂)
Standart hata      SE = √( p̂ × (1 − p̂) × (1/n₁ + 1/n₂) )
Test istatistiği   z  = (p₁ − p₂) / SE
p-değeri              = erfc( |z| / √2 )      (çift taraflı)

p-değeri < 0,05  →  fark anlamlı
```

- **Örnek 1 (1001 Banka Kartı Satış):** p̂ = 0,004481, SE = 0,000476, z = 2,29, **p = 0,022**. Fark anlamlı, Pilot daha iyi.
- **Küçük örneklem (23006 Emekli Bankacılığı Taahhüt Yenileme-Özel Kitle):** Pilot 6/490 (%1,22), NBA 2/546 (%0,37). Lift **3,34** ile çok yüksek görünüyor, ama z = 1,58 ve **p = 0,115**. Fark anlamlı **değil**, birkaç satışlık fark tesadüfle açıklanabilir.
- İki tarafta da satış 0 ise ya da yanıtlayan 0 ise test hesaplanamaz ve p-değeri boş kalır.

### 7.6 Sonuç etiketi

Her aksiyon grubu (ve her kod toplamı) aşağıdaki kurallarla **yukarıdan aşağı** sırayla etiketlenir. İlk uyan kural geçerlidir:

| Sıra | Koşul | Etiket | Renk |
|---|---|---|---|
| 1 | Pilot yanıtlayan = 0 **veya** NBA yanıtlayan = 0 | Karşılaştırma yok | – |
| 2 | Pilot satış + NBA satış = 0 | Satış yok | – |
| 3 | p-değeri ≥ 0,05 (veya hesaplanamadı) | Fark anlamlı değil | Gri |
| 4 | p-değeri < 0,05 ve Pilot satış oranı > NBA satış oranı | Pilot daha iyi | Mavi |
| 5 | p-değeri < 0,05 ve Pilot satış oranı < NBA satış oranı | NBA daha iyi | Turuncu |

### 7.7 Ortak filtreler (sol menü)

Filtreler `app.py` içinde **aşağıdaki sırayla** uygulanır. Her filtre bir öncekinin sonucunu daraltır ve tüm filtreler birlikte geçerlidir ("VE" mantığı).

| Sıra | Filtre | Nasıl çalışır |
|---|---|---|
| 1 | **Periyot** | `HESAPLAMA_GUN_SAYISI` seçilen değere (1 veya 7) eşit olan satırlar tutulur. Seçenekler tabloda bulunan değerlerden otomatik oluşur. |
| 2 | **Injection point** | Yalnızca veride birden fazla `INJECTION_POINT_ID` varsa görünür. Seçilenler tutulur. |
| 3 | **Hesaplama bazı** | Satır süzmez, kullanılacak kolonları seçer (bkz. 7.2). |
| 4 | **Model durumu** | *Tümü*: filtre yok. *Modelli*: `MODEL_FLAG = 1`. *Modelsiz*: `MODEL_FLAG ≠ 1` (boş olanlar dahil). |
| 5 | **Model** | Seçilen `MEVCUT_MODEL_KIMLIGI` değerleri tutulur. Liste, önceki adımlardan sonra kalan modellerden oluşur. Boş bırakılırsa filtre uygulanmaz. |
| 6 | **Aksiyon grup kodu** | Seçilen `ACTION_GROUP_CODE` değerleri tutulur. Liste, önceki adımlardan sonra kalan kodlardan oluşur ve sayısal sıralıdır (1001, 1002, 2004 …). Boş bırakılırsa filtre uygulanmaz. |
| 7 | **Hariç tutulan tarihleri çıkar** | Açıkken, hesaplama penceresi hariç tutulan bir tarihe değen satırlar atılır. Koşul: `FIRST_OFFER_DATE ≤ hariç bitiş` **ve** `LAST_OFFER_DATE ≥ hariç başlangıç`. `FIRST_OFFER_DATE` boşsa `LAST_OFFER_DATE` kullanılır. 1 günlük periyotta bu, günün kendisinin hariç olması demektir. 7 günlük periyotta o günü içeren tüm pencereler atılır. |

- **Filtre listeleri birbirine bağlıdır.** Örneğin *Modelli* seçiliyken Model ve Aksiyon grup kodu listelerinde yalnızca modeli olan kayıtlar çıkar.
- **Seçimler sayfalar arasında korunur.**
- Bu filtrelerden sonra kalan veri, her sayfanın kendi filtrelerine aktarılır.

### 7.8 Günlük Trend sayfası

**Tarih aralığı**
- `LAST_OFFER_DATE` (pencerenin bitiş günü) üzerinden süzer. Başlangıç ve bitiş günleri **dahildir**.
- Yalnızca başlangıç günü seçilip bitiş seçilmemişse, bitiş olarak verideki son gün kabul edilir.

**Günlük değerler**
- Kalan satırlar `LAST_OFFER_DATE`'e göre gruplanır. Her gün için 7.3'teki toplama kuralı ve 7.4'teki formüller uygulanır. Yani her nokta, o günün filtrelenmiş tüm aksiyon gruplarının toplamıdır.
- **1 günlük periyot:** Nokta, yalnızca o günün değeridir.
- **7 günlük periyot:** Nokta, o günde biten 7 günlük pencerenin (`FIRST_OFFER_DATE` → `LAST_OFFER_DATE`) toplamıdır. 7 günlük değerler Oracle'da hazır hesaplanır, dashboard bunları günlük değerleri toplayarak türetmez.

**Son gün ve referans günü**
- **Son gün:** Seçili tarih aralığındaki en son tarih. Verinin en son günü olmak zorunda değildir.
- **Referans adayları:** Son günden önceki, verisi olan tüm günler. Tarih aralığının dışında kalan günler de aday olabilir. Sol menüdeki diğer filtreler ise referans günü için de geçerlidir.
- **Bir önceki gün:** Son günden önceki, *verisi olan* en yakın gün. Takvimde bir gün eksikse ondan önceki gün alınır.
- **Seçilen gün:** Listeden seçilen gün.
- **Son günlerin ortalaması:** Son günden önceki N takvim günü (varsayılan 30). Örneğin son gün 22.09 ve N = 30 ise referans aralığı **23.08 – 21.09**'dur. Son gün aralığa dahil değildir. Referans değerleri şöyle hesaplanır:

  ```
  Referans aralığındaki satırlar  = LAST_OFFER_DATE, [son gün − N, son gün − 1] arasında olanlar
  G                               = bu aralıkta verisi olan gün sayısı
                                    (verisi olmayan ve hariç tutulan günler sayılmaz)

  Referans satış oranı  = Σ satış / Σ yanıtlayan          (ağırlıklı ortalama, bkz. 7.3)
  Referans satış lift   = Referans P satış oranı / Referans N satış oranı
  Referans satış adedi  = Σ satış / G                     (günlük ortalama adet)
  ```

  Oranlar günlük oranların basit ortalaması değildir. Aralıktaki toplam adetlerden hesaplanır, böylece kalabalık günler daha fazla ağırlık taşır. Referans lift de günlük lift değerlerinin ortalaması değildir, ortalama oranlardan hesaplanır.

  Örnek (sentetik test verisi, 1 günlük, Tekil, hariç tutma açık): referans aralığı 23.08 – 21.09, 25 günün verisi. Referans lift 1,066, son günün lift değeri 1,126, değişim **+0,060**. Referans günlük Pilot satış 4.545, son gün 5.177, değişim **+632**.

  > 7 günlük periyotta her gün zaten 7 günlük bir pencere olduğu için referans, son N günde biten pencerelerin ortalamasıdır. Adetler 7 günlük pencere toplamlarının ortalaması olur.

**Özet kartlarındaki değişimler:** Hepsi son gün ile referans günü arasındaki farktır.

| Kart | Gösterilen değer | Değişim formülü |
|---|---|---|
| Pilot satış oranı | Son günün oranı | `(son − referans) × 100` puan |
| NBA satış oranı | Son günün oranı | `(son − referans) × 100` puan |
| Satış lift | Son günün lift değeri | `son − referans` |
| Pilot satış | Son günün adedi | `son − referans` (adet) |
| NBA satış | Son günün adedi | `son − referans` (adet) |

- Değişim hesaplanamıyorsa (ör. lift boşsa) ok ve değer gösterilmez.
- Kartın yanındaki **?** simgesi, referans günündeki değeri gösterir.

**Grafik işaretleri**
- **Referans çizgisi (gri, noktalı):** Referans tek bir günse ve seçili tarih aralığındaysa çizilir.
- **Referans bandı (gri, "Referans (ort.)"):** "Son günlerin ortalaması" seçiliyken referans aralığını gösterir. Aralığın yalnızca grafikte görünen kısmı boyanır.
- **Önemli tarihler (mor, kesikli, 📌):** `config/onemli_tarihler.toml` dosyasındaki tarihler, grafikte gösterilen ilk ve son gün arasındaysa çizilir. Aynı güne ait birden fazla kayıt tek işarette birleşir.
- **Hariç tutulan tarihler (kırmızı, ⛔):** Tek gün kırmızı kesikli çizgi, aralık kırmızı gölgeli bant olarak çizilir. Seçenek açıksa bu günlerin değerleri boş bırakılır ve çizgi kesilir. Tarih aralığı seçicisi ve "son gün" hesabı hariç tutulan günleri de kapsar, ancak son gün ve referans günü yalnızca verisi olan günlerden seçilir.
- **Satış oranı grafiğinin** y ekseni veriye göre ölçeklenir ve 0'dan başlamaz, böylece küçük farklar görünür olur. **Satış adedi grafiği** 0'dan başlar.

### 7.9 Dönem Karşılaştırması sayfası

**Dönem seçimi**
- Liste, seçili periyottaki `DONEM` etiketlerinden oluşur ve `LAST_OFFER_DATE`'e göre yeniden eskiye sıralıdır. Varsayılan seçim en güncel dönemdir.

**Aksiyon grubu satırları**
- Seçilen dönemin satırları `ACTION_GROUP_CODE`, `ACTION_GROUP_DESC`, `MEVCUT_MODEL_KIMLIGI` ve `MODEL_FLAG` kolonlarına göre gruplanır. Her grup için 7.4'teki metrikler, 7.5'teki test ve 7.6'daki etiket hesaplanır.

**Min. yanıtlayan filtresi**
```
min_yanıtlayan = min(P yanıtlayan, N yanıtlayan)
Tutulan gruplar: min_yanıtlayan ≥ eşik
```
- Eşik 0'dan büyük seçildiğinde, bir tarafı 0 olan gruplar ("Karşılaştırma yok") da elenir.
- Bu filtre **özet kartlarını da etkiler.** Kartlar yalnızca eşiği geçen grupların toplamından hesaplanır.

**Özet kartları:** Kalan tüm grupların toplamından, 7.3'teki kurala göre hesaplanır.

| Kart | Değer | Alttaki değişim |
|---|---|---|
| Pilot satış oranı | P satış oranı | `(P satış oranı − N satış oranı) × 100` puan |
| NBA satış oranı | N satış oranı | – |
| Satış lift | P satış oranı / N satış oranı | `(lift − 1) × 100` % |
| Olumlu yanıt lift | P olumlu oranı / N olumlu oranı | `(lift − 1) × 100` % |
| Oran bazlı ek satış | Toplam adetlerden hesaplanır | Ham adet farkı **?** simgesinde gösterilir |

> **Not:** Toplamdaki oran bazlı ek satış, grupların tek tek ek satışlarının toplamına eşit **değildir**. Toplam değer tüm grupların birleşik NBA oranıyla hesaplanır, grup değerleri ise her grubun kendi NBA oranıyla.

**Sonuç sayaçları:** Kalan grupların 7.6'daki etiketlere göre dağılımıdır. "Satış / karşılaştırma yok" kutusu, "Satış yok" ve "Karşılaştırma yok" etiketlerinin toplamını gösterir.

**Sekmeler**

| Sekme | Nasıl hesaplanır |
|---|---|
| **Aksiyon grupları** | Her çubuk `(satış lift − 1) × 100` (%) değeridir. Lift'i boş olan gruplar (Karşılaştırma yok, Satış yok) gösterilmez. Pilot satışı 0, NBA satışı 0'dan büyük olan gruplar −%100'de görünür. Renk, 7.6'daki etikete göre verilir. |
| **Pilot ve NBA oranları** | x = NBA satış oranı, y = Pilot satış oranı, iki eksen de logaritmiktir. Oranlardan biri 0 olan gruplar log ölçekte gösterilemediği için dışarıda kalır. Nokta boyutu: `8 + 32 × √(P yanıtlayan + N yanıtlayan) / √(en büyük toplam)`. Kesikli çizgi y = x (eşit oran) çizgisidir. |
| **AG grup kodu bazında** | Her kod için Pilot ve NBA satış oranı yan yana. En çok Pilot yanıtlayanı olan kod üstte. Grafikteki etiketler 45 karakterde kesilir, tabloda tam açıklama görünür. |
| **Detay tablo** | Tüm metrikler. Üstteki **Sonuç** filtresi yalnızca bu tabloyu süzer, kartları ve grafikleri etkilemez. |

### 7.10 Biçimlendirme ve dışa aktarma

- **Sayılar:** Türkçe biçim, yani binlik ayırıcı nokta ve ondalık virgül (ör. `32.762`, `1,114`).
- **Oranlar:** Yüzde olarak, 3 ondalıkla (ör. `%0,577`).
- **Puan:** İki oran arasındaki fark, yüzde puan cinsinden (ör. %0,505 ile %0,396 arasındaki fark `+0,109 puan`).
- **CSV indirme:** Ayırıcı `;`, ondalık `,`, kodlama UTF-8 (BOM'lu). Bu sayede dosya Türkçe Excel'de çift tıklamayla doğru açılır. Oranlar CSV'de yüzde olarak değil, ondalık olarak yazılır (ör. `0,005047`).

---

## 8. Sorun giderme

| Belirti | Olası neden ve çözüm |
|---|---|
| `streamlit : The term 'streamlit' is not recognized` | Sanal ortam etkin değil. `.\.venv\Scripts\Activate.ps1` çalıştırın ya da `python -m streamlit run app.py` kullanın. |
| `Veri yüklenemedi: 'ORACLE_USER'` gibi bir hata | `.env` dosyası yok veya ilgili alan boş. |
| `DPY-6005` / bağlantı zaman aşımı | Veritabanına ağ erişimi yok. VPN'i ve `ORACLE_DSN` değerini kontrol edin. |
| `ORA-01017` | Kullanıcı adı veya şifre hatalı. |
| `ORA-00942` | Tablo adı yanlış ya da kullanıcının bu tabloyu okuma yetkisi yok. |
| `DPY-3001` / `DPY-3015` | Veritabanı *thin mode* ile uyumsuz (Native Network Encryption açık ya da sürüm 12.1'den eski). Oracle Instant Client kurulup *thick mode*'a geçilmesi gerekir. |
| `Veri yüklenemedi: 'PILOT_TEKIL_SATIS'` gibi bir kolon adı | Tablodaki kolon adları beklenenden farklı. Kolon adları örnek veridekilerle aynı olmalı. |
| Oracle'da veri güncellendi ama ekranda eski veri var | Sol menüdeki **Veriyi yenile** butonuna basın. |
| Diğer kullanıcılar dashboard'a erişemiyor | Başlatan bilgisayarın açık olduğundan, doğru **Network URL** adresinin kullanıldığından ve güvenlik duvarı izninden emin olun. |

---

## 9. Proje yapısı

```
app.py                         Giriş noktası: sayfa gezinmesi ve ortak filtreler
config/onemli_tarihler.toml    Grafiklerde işaretlenecek önemli tarihler
config/haric_tutulan_tarihler.toml  Kırmızı işaretlenen, istenirse hesaplamadan çıkarılan tarihler
nba_dashboard/
  data.py                      Oracle / dosyadan veri okuma ve temizleme
  metrics.py                   Oran, lift ve anlamlılık hesapları
  charts.py                    Plotly grafikleri
  events.py                    Önemli / hariç tutulan tarihleri okuma ve hariç tutma kuralı
  formatting.py                Türkçe sayı biçimleri
  views/trend.py               Günlük Trend sayfası
  views/comparison.py          Dönem Karşılaştırması sayfası
scripts/make_demo_data.py      Sentetik test verisi üretici
.env.example                   Ayar dosyası şablonu
requirements.txt               Python bağımlılıkları
```
