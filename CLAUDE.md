# Claude için notlar

Bu repo kullanıcının TikTok foto-postlarını üretmek için. Kullanıcı Türkçe konuşuyor — Türkçe yanıt ver; post metinleri (caption) varsayılan olarak İngilizce, küçük harf ağırlıklı ve emojili (kullanıcı aksini söylemedikçe).

İş akışı: kullanıcı fotoğraf gönderdiğinde onları `photos/` altına kopyala, STYLE_GUIDE.md'deki kurallara göre `posts/<ad>.json` yaz, `python3 tiktok_post.py posts/<ad>.json` çalıştır, çıktıyı küçültüp kendin kontrol et (yazı yüze/ürüne denk geliyor mu, okunuyor mu), sonra `output/` dosyasını kullanıcıya gönder.

Yerleşim ipuçları: caption ve saati fotoğrafın boş/sade alanına koy; yüzleri ve logo/ürünleri kapatma; açık zeminlerde gölgeyi (`shadow`) artır.
