# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No  | Keputusan                                                                                   | Alternatif yang ditolak                                              | Alasan                                                                                                                                           |
| --- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Parser yang menentukan arti `*` dari posisinya. Di awal `SELECT` artinya semua kolom, di dalam ekspresi artinya kali. | Lexer yang menentukan arti `*`. | Lexer tidak tahu konteks, parser tahu. Konsekuensinya `SELECT *, a` ditolak. |
| 2   | `OR` dan `AND` dipisah jadi dua fungsi: `_or_expr` memanggil `_and_expr`. | Satu fungsi untuk `AND` dan `OR`. | Satu fungsi sama dengan satu aturan grammar. `AND` yang di dalam otomatis lebih kuat dari `OR`. |
| 3   | `INSERT ... SELECT` memanggil ulang `_select()`. | Menulis fungsi SELECT baru khusus untuk INSERT. | Aturan SELECT-nya sama, jadi tidak perlu kode baru. |
| 4   | Urutan pencarian scope dari terdalam ke luar (Innermost to Outermost Scope Chain).          | Pencarian satu arah terluar ke terdalam atau flat global dictionary. | Memungkinkan shadowing alias lokal dan mendukung correlated subquery.                                                                            |
| 5   | Pembatasan resolusi kolom tanpa qualifier hanya pada scope terdalam (Innermost Scope Only). | Mencari kolom tanpa qualifier ke scope induk (outer scopes).         | Menghindari resolusi sembrono tanpa kepastian skema database fisik (schema-less static analyzer) dan konsisten dengan aturan SPESIFIKASI.md 4.3. |