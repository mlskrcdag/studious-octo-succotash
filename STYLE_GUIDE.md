# TikTok Post Stil Rehberi — "Day in my Life" estetiği

Referans: 5 örnek slayt (kapak, 06:20 sabah rutini, 08:22 matcha, kahvaltı kolajı, 13:00 masa başı).
Genel his: **sıcak, yumuşak, günlük/vlog**; fotoğraf ön planda, yazılar küçük ve zarif, aralara serpiştirilmiş sticker'lar.

## 1. Format
| | |
|---|---|
| Oran | **3:4 dikey** (TikTok foto modu) — varsayılan 1080×1440 |
| Slayt sırası | Kapak → saat saat akış (06:20, 08:22, 13:00 …) → kapanış |
| Fotoğraf | Doğal ışık, üstten çekim (flat-lay) veya göz hizası; nesneler net, arka plan sade |

## 2. Yazı tipleri
| Kullanım | Örnekteki görünüm | Bizim font (`fonts/`) | Alternatif (CapCut/Canva/Instagram) |
|---|---|---|---|
| Büyük başlık ("Day in my Life") | İnce, uzun kuyruklu kaligrafi, krem renk | **Pinyon Script** | Canva: *Pinyon Script*, *Monsieur La Doulaise*; CapCut: "Elegance" tarzı script |
| Yemek/mekan etiketi ("breakfast platter", "avocado toast") | Beyaz, daha yuvarlak el yazısı | **Great Vibes** (veya Allura, Parisienne) | Canva: *Great Vibes*, *Allura* |
| Caption / açıklama | Beyaz, sade sans-serif, küçük punto, hafif gölge | **Inter Regular** (iOS SF Pro hissi) | Instagram/TikTok "Classic" / "Modern"; Canva: *Inter*, *Helvetica Neue* |
| Küçük etiket ("one", "6 am - 10 pm") | İnce sans, açık pembe | **Inter Light** | Canva: *Inter Light* |
| Saat rakamları | Medium sans, karolar içinde | **Inter Medium** | — |

**Kurallar:** Caption'lar küçük harf ağırlıklı ("morning routine: shower, makeup…"). Script başlıklar 2–3 satıra bölünür, satırlar hafif kaydırılır (merdiven) ve ~5–10° eğilir. Her caption 1–3 emoji ile biter (✨🫧🧘🏻‍♀️ 🍵💚 🥹🫶).

## 3. Renkler
| Ad | Hex | Nerede |
|---|---|---|
| cream | `#F6F1DE` | Büyük script başlık |
| white | `#FFFFFF` | Caption, yemek etiketi, yıldızlar |
| blush | `#F2C6D3` | "one", saat aralığı gibi ikincil etiketler |
| clock_bg | `#F2F2F2` (~%88 opak) | Flip-saat karoları |
| clock_ink | `#4A4A4A` | Saat rakamı (nötr) |
| clock_pink | `#EC6F9A` | Saat rakamı (pembe varyant — pembe tonlu fotoğraflarda) |
| star_yellow | `#FFD34E` | ⭐ sticker |

Fotoğraflar canlı ama sıcak; vurgu renkleri: pembe, kobalt mavi, matcha yeşili, turuncu.

## 4. İmza öğeler
1. **Flip-clock saat damgası** — 4 ayrı yuvarlak köşeli karo, ortadan geçen ince çizgi. **Kullanıcı tercihi: şeffaf/buzlu cam karolar + beyaz rakam (varsayılan `glass`)**, pembe kullanma. Kapak hariç her slaytta; genelde caption'ın hemen altında veya fotoğrafın boş köşesinde.
2. **Caption** — ortalanmış (veya bölünmüş slaytta sola yaslı), genişliğin ~%40–60'ı, fotoğrafın boş/koyu alanına.
3. **Yıldız sticker'ları** — küçük beyaz dolu yıldızlar, bir adet büyük puantiyeli (polka) yıldız, sarı ⭐ emoji. 2–4 adet, köşelere dağınık.
4. **Konum hapı** — yarı saydam beyaz yuvarlak kutu + pin ikonu + BÜYÜK HARF metin (kapakta "FEBRUARY").
5. **Kolaj düzenleri** — `full` (tek foto), `stack2` (üst/alt ikiye bölünmüş), `top_split` (üstte bir, altta yan yana iki). Kenar boşluğu yok, fotoğraflar birbirine dayalı.
6. (İsteğe bağlı) Piksel el imleci 👉 gibi küçük ironik sticker'lar.

## 5. Kapak şablonu
(Kullanıcı tercihi: başlık Türkçe "Benimle / bir / Gün", düz/eğiksiz, "one" ve saat aralığı yok, hapta Türkçe tarih ör. "22 Kasım".)
- Ayna selfie / tam boy outfit fotoğrafı
- Sol üst: "one" (blush, ince)
- Ortada çapraz: **Day / in my / Life** (Pinyon Script, krem, dev boy)
- Script'in sağ üstünde: "6 am - 10 pm"
- Altta: "as a full time … in <şehir>" (küçük beyaz caption)
- En altta: konum/ay hapı

## 6. Renk düzenleme (grade) önerisi
Hafif sıcak ve mat: parlaklık +3%, sıcaklık +5, siyahları biraz kaldır (fade 10–15), doygunluk aynı veya +5%. Telefonla: Pozlama +5, Sıcaklık +8, Siyah Nokta −10, Kontrast −5.

## 7. Stil B — "office day" / el yazısı notlar (2. referans seti)
Kullanıcının sonradan beğendiği iki referanstan çıkanlar; postlara karıştırılarak kullanılabilir.

| Öğe | Görünüm | Araçtaki karşılığı |
|---|---|---|
| Büyük başlık | Pembe (`pop_pink` `#F7A1B9`), düz sans, küçük harf, dev boy, satırlar sıkışık ("day / in my / life"), iki fotoğrafın birleşim çizgisine ortalı | `title` (Inter, `line_height` 0.86) |
| Üst/alt mini etiket | Beyaz küçük sans: "office day edition" üstte, "as an experience designer" altta | `label` + `font: "sans"`, `color: "white"`, `align: "center"` |
| Sade saat | "8:45 am" — beyaz düz sans, iki fotoğrafın birleşim çizgisinde | `clock` + `style: "plain"` |
| El yazısı notlar | Beyaz kalemle yazılmış gibi, hafif eğik: "double shot please!", "my morning fuel" | `hand` (Caveat; Türkçe karakter destekli), `rotate` |
| Checklist | El yazısı başlık (":" ile biter) + titrek el çizimi kutucuklu maddeler | `hand` + `checklist: true`; "- " ile başlayan satır önceki maddenin devamı |
| Doodle'lar | Elle çizilmiş meyve/ok/kalp illüstrasyonları | `doodle` (`arrow`, `heart`, `sparkle`, `underline`, `circle`, `swirl`); meyve vb. için `emoji` |

Not: Referanstaki el yazısı daha "kalem çiziği" gibi; Türkçe karakterleri (ş, ğ, İ) eksiksiz destekleyen en yakın font Caveat olduğu için o seçildi.
