# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Keyword Ditulis Huruf Kecil/Campuran Dianggap Identifier

**Ditemukan oleh:** Sulthan Faazaa Akbar Riyandoro · **Diperbaiki oleh:** Sulthan Faazaa Akbar Riyandoro

**Gejala.** SQL dengan keyword huruf kecil seperti `select id from t` menghasilkan token berjenis `IDENT`, bukan `KEYWORD`. Menurut SPESIFIKASI.md bagian 2.2, keyword bersifat tidak peka huruf besar/kecil (case-insensitive) dan nilainya harus selalu dinormalisasi ke huruf besar.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select id from t;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mengacu pada Crafting Interpreters Bab 4, lexer lama memeriksa keanggotaan kata ke tabel simbol statis secara sensitif terhadap kapitalisasi karakter tanpa melakukan normalisasi case terlebih dahulu. Hal ini menyebabkan kata kunci standar yang ditulis dengan huruf kecil atau campuran lolos dari pencocokan reserved words dan salah diklasifikasikan sebagai identifier biasa.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada fungsi _word() di crud/lexer.py, teks masukan dinormalisasi terlebih dahulu ke huruf besar. Jika upper in KEYWORDS, token disimpan sebagai TokenType.KEYWORD dengan nilai upper. Jika tidak, disimpan sebagai TokenType.IDENT dengan nilai teks asli text. Alternatif mengubah daftar KEYWORDS menjadi berisi semua kombinasi huruf kecil dan besar ditolak karena tidak efisien dan tidak skalabel.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_lexer_keyword_case_insensitive di tests/test_tambahan.py

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu mengimplementasikan normalisasi huruf kapital pada pengecekan set keyword. Diverifikasi melalui pengujian pytest dengan variasi kata kunci berhuruf campuran seperti SeLeCt, fRoM, dan WhErE.

---

## Bug 2: Operator Tidak Sama Dengan <> Terpecah Menjadi Dua Token Terpisah

**Ditemukan oleh:** Sulthan Faazaa Akbar Riyandoro · **Diperbaiki oleh:** Sulthan Faazaa Akbar Riyandoro

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).
Ekspresi perbandingan a <> b menghasilkan dua token operator terpisah OP('<') dan OP('>'). Akibatnya, parser gagal memproses perbandingan dan melempar ParseError. Menurut SPESIFIKASI.md bagian 2.5, lexer wajib mengambil operator terpanjang yang cocok (maximal munch), sehingga <> harus berupa satu token

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT id FROM t WHERE status <> 'AKTIF';
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mengacu pada konsep Maximal Munch, pemindai leksikal harus selalu mengonsumsi karakter sebanyak mungkin yang membentuk satu token valid sebelum memutuskan tipe token. Pada kode lama di _scan_token(), percabangan saat membaca karakter < hanya mengecek apakah karakter berikutnya adalah = (menghasilkan <=). Pemeriksaan karakter > terlewatkan, sehingga karakter > ditinggalkan di buffer input dan dibaca sebagai token mandiri pada iterasi berikutnya.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada metode _scan_token() di crud/lexer.py, saat mendeteksi karakter <, ditambahkan pengecekan self._match(">") setelah pengecekan self._match("="). Jika cocok, lexer menghasilkan satu token TokenType.OP dengan nilai "&lt;&gt;". Alternatif menangani penggabungan < dan > di level parser ditolak karena melanggar batasan arsitektur (tugas lexer adalah memancarkan unit leksikal terpanjang secara tuntas).

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_lexer_operator_tidak_sama_dengan di tests/test_tambahan.py.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menambahkan cabang self._match(">") pada blok kondisi leksikal. Diverifikasi dengan menjalankan pytest dan menguji statement pada file data/sample/laporan_penjualan.sql yang memuat catatan <> 'FROM rahasia'

---

## Bug 3: String Literal dengan Escaped Single Quote ('') Terpotong Prematur

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).
Literal string yang memuat dua tanda petik tunggal berturut-turut seperti 'O''Brien' terpotong menjadi token string 'O', sementara karakter 'Brien' sisanya memicu ParseError atau LexError. Menurut SPESIFIKASI.md bagian 2.4, dua petik tunggal berturut-turut di dalam string mewakili tepat satu karakter kutip di dalam nilai token.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT * FROM crm.pelanggan WHERE nama = 'O''Brien';
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mengacu pada Crafting Interpreters Bab 4, pemindai literal string harus membedakan antara tanda petik penutup string (delimiter) dengan tanda petik yang merupakan bagian dari data (escape sequence). Kode lama langsung mengeksekusi break begitu menemukan karakter ' pertama tanpa melihat satu karakter ke depan (lookahead), sehingga mengakhiri pemindaian string secara prematur.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada metode _string() di crud/lexer.py, saat menemukan karakter ', ditambahkan pemeriksaan karakter berikutnya dengan self._match("'"). Jika karakter berikutnya adalah petik tunggal, satu tanda kutip dimasukkan ke dalam buffer string (chars.append("'")) dan loop pemindaian tetap berjalan. Jika tidak diikuti petik, barulah loop dihentikan (break). Alternatif menggunakan regex kompleks ditolak karena parser/lexer dirancang berbasis loop manual imperatif yang efisien.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_lexer_escaped_quote_string di tests/test_tambahan.py.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu merestrukturisasi loop _string() agar melakukan penelusuran satu karakter ke depan untuk mendeteksi pasangan kutip. Diverifikasi dengan menjalankan query dari data/sample/pemeliharaan.sql yang memuat nama 'O''Brien'.

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
