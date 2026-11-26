# Claude için notlar

Bu repo kullanıcının TikTok foto-postlarını üretmek için. Kullanıcı Türkçe konuşuyor — Türkçe yanıt ver; post metinleri (caption) varsayılan olarak İngilizce, küçük harf ağırlıklı ve emojili (kullanıcı aksini söylemedikçe).

İş akışı: kullanıcı fotoğraf gönderdiğinde onları `photos/` altına kopyala, STYLE_GUIDE.md'deki kurallara göre `posts/<ad>.json` yaz, `python3 tiktok_post.py posts/<ad>.json` çalıştır, çıktıyı küçültüp kendin kontrol et (yazı yüze/ürüne denk geliyor mu, okunuyor mu), sonra `output/` dosyasını kullanıcıya gönder.

Emoji: caption'larda artık emoji YOK (kullanıcı 26 Kasım'da kaldırttı; okunurluk için kalın + backdrop + outline kullan). Eski not: caption sonunda en fazla 1 emoji (kullanıcı yazı yanındaki emojileri azaltmak istedi); süs olarak fotoğrafın içine `star` + `style: twinkle` parıltılar (3–4 adet, logo/yüz üstüne değil). Yerleşim ipuçları: el yazısı notları (`hand`) eğik değil düz yaz (rotate 0). Kullanıcı yazıların bol emojili ve kenara değil göz hizasına (karenin üst üçte biri–ortası) yakın olmasını seviyor; caption ve saati fotoğrafın boş/sade alanına koy; yüzleri ve logo/ürünleri kapatma; açık zeminlerde gölgeyi (`shadow`) artır.

Üç stil var (STYLE_GUIDE.md): A = script başlık + şeffaf flip-saat; B = pembe sans başlık, el yazısı notlar, checklist, sade saat, doodle; C = beyaz kalın başlık, pembe [etiket], arama çubuğu, photo dump klasörü, beyaz yıldızlar. Kullanıcı B öğelerini postlarına eklemeyi istedi; uygun slaytlarda ikisini karıştırabilirsin.

Düzen: varsayılan tek tam fotoğraf; ikinci foto için polaroid `insets`; `stack2` yalnızca birbirine uyan ikililer için (kullanıcı her şeyi alt alta koymayı sevmedi).

Süs: kullanıcı en çok krem/altın mum boya çizimlerini (`crayon`: star, bow, heart) seviyor — slayt başına 2–4 tane kullan. Düğme sticker'ı sevmedi, kullanma.

Güncel varsayılan (26 Kasım): STYLE_GUIDE §12 — insets/polaroid yok; bantlar + sola yaslı caption + büyük harf pin.
