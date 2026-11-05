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
Pada metode _scan_token() di crud/lexer.py, saat mendeteksi karakter <, ditambahkan pengecekan self._match(">") setelah pengecekan self._match("="). Jika cocok, lexer menghasilkan satu token TokenType.OP dengan nilai "<>". Alternatif menangani penggabungan < dan > di level parser ditolak karena melanggar batasan arsitektur (tugas lexer adalah memancarkan unit leksikal terpanjang secara tuntas).

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

## Bug 4: Rantai Scope Terbalik pada _lookup

**Ditemukan oleh:** Sulthan Faazaa Akbar Riyandoro · **Diperbaiki oleh:** Sulthan Faazaa Akbar Riyandoro

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).
Pada query bersarang (subquery) di mana alias tabel pada subquery sama dengan alias pada query luar, resolusi kolom di dalam subquery salah terhubung ke tabel pada scope terluar alih-alih tabel lokal subquery. Menurut SPESIFIKASI.md bagian 4.3, qualifier kolom wajib dicari mulai dari scope terdalam ke luar sehingga alias di subquery menutupi (shadowing) alias yang sama di luar dan mendukung correlated subquery.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT t.nama FROM pelanggan t WHERE t.id IN (SELECT t.id FROM pesanan t);
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mengacu pada Crafting Interpreters Bab 11 (Resolving and Binding), penelusuran lingkungan leksikal (lexical scope chain lookup) harus bergerak dari lingkungan saat ini (innermost scope) merambat keluar menuju lingkungan pembungkusnya (parent/enclosing scope) hingga mencapai root environment. Pada fungsi `_lookup()` di `crud/resolver.py`, kode lama mengumpulkan rantai scope dari `self.scope` ke `parent` ke dalam list `chain`, namun kemudian mengiterasinya dengan `reversed(chain)` (dari scope terluar ke terdalam). Akibatnya, deklarasi pada outer scope selalu diprioritaskan dan menutupi deklarasi pada inner scope, yang membalik aturan shadowing dan melanggar prinsip dasar lexical scoping.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada fungsi `_lookup()` di `crud/resolver.py`, list `chain` dan pembalikan `reversed(chain)` dihapus. Logika diganti dengan traversal langsung mulai dari `self.scope` berjalan ke `scope.parent` menggunakan loop `while scope is not None:`. Jika `name` ditemukan di `scope.entries`, fungsi langsung mengembalikan entri tersebut (innermost-to-outermost). Alternatif mempertahankan pengumpulan rantai list tanpa memanggil `reversed()` ditolak karena iterasi langsung pointer `parent` lebih sederhana, efisien, dan hemat alokasi memori.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_resolver_scope_chain_shadowing di tests/test_tambahan.py.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menganalisis kesalahan urutan iterasi list rantai scope pada fungsi _lookup dan menyederhanakannya menjadi traversal while loop langsung. Diverifikasi dengan menjalankan unit test shadowing dan memeriksa apakah resolved target dari subquery menunjuk ke tabel pesanan, bukan pelanggan.

---

## Bug 5: Scope Leak pada Statement DELETE

**Ditemukan oleh:** Sulthan Faazaa Akbar Riyandoro · **Diperbaiki oleh:** Sulthan Faazaa Akbar Riyandoro

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).
Setelah eksekusi statement DELETE selesai diproses oleh resolver, scope lokal milik statement DELETE tidak dihancurkan sehingga tabel dan aliasnya tetap bertahan dan dapat diakses oleh statement berikutnya. Menurut SPESIFIKASI.md bagian 4.5, setiap statement harus berdiri sendiri dan setelah satu statement selesai di-resolve tidak boleh ada scope tersisa.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM pelanggan p WHERE p.id = 1;
SELECT p.nama FROM pesanan o;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mengacu pada Crafting Interpreters Bab 11 (Resolving and Binding - Scope Lifecycle), setiap blok yang membuka lingkup leksikal lokal melalui operasi `push()` wajib menutup dan menghancurkan lingkup tersebut melalui operasi `pop()` ketika keluar dari blok lingkup tersebut. Pada fungsi `_delete()` di `crud/resolver.py`, `self._push()` dipanggil untuk mendaftarkan target tabel DELETE, namun fungsi berakhir tanpa memanggil `self._pop()`. Ketiadaan `self._pop()` ini menyebabkan scope leak di mana scope lokal DELETE tetap aktif sebagai scope teratas pada resolver dan mencemari environment statement SQL selanjutnya.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada fungsi `_delete()` di `crud/resolver.py`, ditambahkan pemanggilan `self._pop()` di baris akhir fungsi setelah traversal `self._expr(dele.where)`. Alternatif tidak membuat scope baru untuk DELETE (menghapus `_push()`) ditolak karena klausa WHERE pada DELETE dapat memuat ekspresi kolom yang membutuhkan resolusi alias serta correlated subquery.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_resolver_delete_scope_isolation di tests/test_tambahan.py.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu mengidentifikasi ketiadaan pemanggilan _pop() pada siklus hidup scope di fungsi _delete. Diverifikasi dengan menjalankan test multi-statement yang memastikan alias dari statement DELETE tidak dapat diakses oleh statement berikutnya dan memastikan atribut resolver.scope kembali bernilai None.

---

## Bug 6: Subquery pada UPDATE Ditandai sebagai Operasi 'U'

**Ditemukan oleh:** Sulthan Faazaa Akbar Riyandoro · **Diperbaiki oleh:** Sulthan Faazaa Akbar Riyandoro

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).
Tabel yang diakses melalui subquery di dalam ekspresi assignment nilai (klausa SET) maupun klausa WHERE pada statement UPDATE dicatat dengan operasi 'U' (Update). Menurut SPESIFIKASI.md bagian 5, tabel target UPDATE mendapat operasi 'U', sedangkan membaca tabel melalui subquery selalu merupakan operasi 'R' (Read), apa pun jenis statement luarnya.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
UPDATE pelanggan SET total = (SELECT SUM(nilai) FROM pesanan) WHERE id = 1;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Terjadi pelanggaran invarian semantik CRUD yang diatur pada SPESIFIKASI.md bagian 5. Pada fungsi `analyze_statement()` di `crud/analyzer.py` dalam blok penanganan `ast.Update`, pemanggilan fungsi `_collect()` untuk ekspresi assignment (`assignment.value`) dan ekspresi WHERE (`stmt.where`) secara keliru meneruskan string operasi `"U"`, yaitu `_collect(assignment.value, usage, "U")` dan `_collect(stmt.where, usage, "U")`. Karena subquery pada ekspresi hanya melakukan evaluasi pembacaan data, tabel di dalam subquery seharusnya ditandai dengan operasi "R", bukan "U".

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada fungsi `analyze_statement()` di `crud/analyzer.py`, parameter operasi pada pemanggilan `_collect(assignment.value, usage, "U")` dan `_collect(stmt.where, usage, "U")` diubah menjadi `_collect(assignment.value, usage, "R")` dan `_collect(stmt.where, usage, "R")`. Alternatif mengoreksi operasi secara retroaktif setelah pengumpulan ditolak karena memperbaiki argumen operasi saat traversal AST lebih bersih dan mematuhi prinsip traversal semantik.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_analyzer_update_subquery_is_read di tests/test_tambahan.py.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menelusuri penandaan operasi 'U' pada koleksi ekspresi subquery statement UPDATE di crud/analyzer.py. Diverifikasi dengan menjalankan unit test analyzer dan memeriksa hasil matriks CRUD pada skrip pengujian.

---

## Bug 7: (judul singkat)

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
