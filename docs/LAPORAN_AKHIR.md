# Laporan Akhir

## 1. Hasil evaluasi

Keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi:

![Hasil evaluate.py](img/evaluate.png)

## 2. Tiga kasus di mana regex salah

1. **Komentar dianggap perintah.** `laporan_penjualan.sql` baris 2: `-- DELETE FROM pelanggan`.
   Regex melaporkan `pelanggan,D` padahal itu komentar. Lexer membuang komentar sebelum parser bekerja, jadi parser tidak pernah melihat kata `DELETE` itu.
2. **Isi string dianggap SQL.** `laporan_penjualan.sql` baris 6: `'FROM rahasia'`.
   Regex melaporkan `rahasia,R`. Lexer menjadikan seluruh string satu token `STRING`, jadi `FROM` di dalamnya bukan keyword.
3. **Statement yang gagal parse tetap dihitung.** `campuran_error.sql` baris 4: `SELECT id nama, FROM pesanan;`.
   Regex melaporkan `pesanan,R`. Parser menolak statement rusak itu dan melanjutkan ke statement berikutnya (error recovery), sehingga tidak dihitung.

## 3. Batas pendekatan kami

1. **Kolom tanpa qualifier pada JOIN.** `SELECT nama FROM a JOIN b ON a.id = b.id` menghasilkan warning `kolom 'nama' ambigu tanpa skema`.
   Akibatnya kolom itu tidak bisa dikaitkan ke tabel. Dibutuhkan skema database (daftar kolom tiap tabel).
2. **Sintaks di luar grammar.** `WITH ... SELECT` dan `UNION` ditolak sebagai error sintaks.
   Akibatnya statement itu hilang dari CRUD matrix. Dibutuhkan perluasan grammar.
3. **View, trigger, dan SQL dinamis.** `SELECT * FROM v_laporan` dianggap tabel biasa `v_laporan,R`.
   Tabel asli di balik view tidak terlihat. Dibutuhkan definisi view dan trigger dari katalog database.

## 4. Pembagian kerja

| Tahap | Dikerjakan oleh |
| --- | --- |
| Lexer (komentar blok, keyword huruf besar/kecil, `<>`, string `''`) | Sulthan |
| Parser (INSERT...SELECT, error recovery, `LEFT OUTER JOIN`, presedensi AND/OR) | Syahid |
| Resolver dan analyzer (TODO T2, scope, DELETE, UPDATE subquery) | Sulthan |
| Label ground truth `audit.sql` dan `pemeliharaan.sql`, serta `evaluate.py` | Syahid |
| Laporan, kartu desain, dan log AI | Bersama |

Pembagian ini bisa dicek di riwayat commit Git. Agar keduanya paham seluruh kode, kami saling menjelaskan modul yang dikerjakan partner sebelum demo.