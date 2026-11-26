# TikTok Post Atölyesi

Fotoğraflarını referans "day in my life" stiline göre düzenleyen küçük araç. Stil detayları: [STYLE_GUIDE.md](STYLE_GUIDE.md).

## Nasıl çalışır
1. Fotoğrafları `photos/` klasörüne koy (veya sohbette Claude'a gönder).
2. Her slayt için `posts/` içinde bir JSON yaz (örnekler: `ornek_kapak.json`, `ornek_sabah.json`, `ornek_ikili.json`).
3. Çalıştır:
   ```bash
   python3 tiktok_post.py posts/*.json
   ```
4. Sonuçlar `output/` klasörüne 1080×1440 JPG olarak düşer.

> `photos/` ve `output/` git'e eklenmez (kişisel fotoğraflar). Örnek JSON'lar `photos/demo_*.jpg` dosyalarını bekler; kendi fotoğraflarınla değiştir.

## JSON alanları
- `layout`: `full` | `stack2` | `top_split` | `stack3` (üç yatay bant, `splits: [0.28, 0.44, 0.28]`); `split`: bölme oranı (0.5)
- `keystone`: her foto için perspektif düzeltme — eğik çekilmiş dikdörtgen nesnenin köşeleri `[[sol-üst],[sağ-üst],[sağ-alt],[sol-alt]]` (piksel) ya da `null`
- `crop`: her foto için `[l,t,r,b]` (0–1) ya da `null` — ör. üstte istenmeyen ayna yansımasını kesmek için
- `rotate`: her foto için düzeltme açısı (derece, eğik nesneyi düzeltmek için; ör. `[-7, 0]`)
- `photos`: dosya yolları; `focus`: her foto için kırpma merkezi `[x, y]` (0–1)
- `grade`: `brightness`, `contrast`, `saturation`, `warmth`, `fade`
- `elements` (x, y ve size hep 0–1 arası oran):
  - `caption` — `text`, `align`, `width`, `size`
  - `script` — `text` (satırlar `\n`), `font` (`script`/`script2`/`script3`/`script4`), `offsets`, `rotate`, `color`
  - `label` — küçük ince yazı ("one", "6 am - 10 pm")
  - `clock` — `time: "08:22"`, `style: glass` (varsayılan: buzlu cam, şeffaf) `| solid`, `color`
  - `star` — `style: white | yellow | polka | twinkle` (4 köşeli parıltı + ışıma), `rotate`
  - `pill` — konum/ay hapı, `icon: true/false`, `align: left` (x = sol kenar)
- `insets`: ana fotoğrafın üstüne polaroid kart(lar) — `photo, x, y, w, aspect, rotate, crop [l,t,r,b], focus, frame (polaroid | rounded | plain)`
  - `emoji` — tek emoji sticker: `text`, `size`, `rotate`
  - `bubble` — iMessage mesaj balonu (`text`, `top` emojiler, `tail`)
  - `crayon` — krem mum boya çizim: `shape: star | bow | heart`
  - `tag` — pembe vurgu etiketi "[ ... ]"; `search` — arama çubuğu; `folder` — pembe klasör ikonu + etiket
  - `title` — büyük pembe sans başlık (`font: sans_bold`, `color: white` ile stil C) (`text` satırları `\n`, `size`, `color`)
  - `hand` — el yazısı not (`text`, `size`, `rotate`, `align`); `checklist: true` ile kutucuklu liste
  - `doodle` — `shape: arrow | heart | sparkle | underline | circle | swirl`, `size`, `rotate`, `color`
  - `clock` + `style: plain` — "8:45 am" gibi sade saat yazısı

Fontlar `fonts/` içinde (Google Fonts, OFL lisansı; Inter de OFL).
