"""Test regresi dan kasus uji tambahan buatan kelompok."""
import pytest

from crud.lexer import LexError, Token, TokenType, tokenize
from crud import ast_nodes as ast
from crud.parser import parse_sql
from crud.resolver import Resolver
from crud.analyzer import analyze_statement


def test_lexer_komentar_blok():
    # Menguji komentar blok multi-baris
    sql_multi = "/* komentar baris 1\n   komentar baris 2 memuat karakter * bintang\n   baris 3 */ SELECT * FROM t"
    toks = tokenize(sql_multi)
    assert toks[0].type == TokenType.KEYWORD
    assert toks[0].value == "SELECT"
    assert toks[0].line == 3

    # Menguji error jika komentar blok tidak ditutup
    with pytest.raises(LexError) as exc_info:
        tokenize("/* komentar blok tidak ditutup sampai akhir input")
    assert "komentar blok tidak ditutup" in str(exc_info.value)
    assert exc_info.value.line == 1
    assert exc_info.value.col == 1


def test_lexer_keyword_case_insensitive():
    # Menguji variasi kapitalisasi keyword seperti 'SeLeCt', 'fRoM'
    toks = tokenize("SeLeCt id fRoM pelanggan WhErE aktif = 1")
    assert toks[0].type == TokenType.KEYWORD and toks[0].value == "SELECT"
    assert toks[1].type == TokenType.IDENT and toks[1].value == "id"
    assert toks[2].type == TokenType.KEYWORD and toks[2].value == "FROM"
    assert toks[3].type == TokenType.IDENT and toks[3].value == "pelanggan"
    assert toks[4].type == TokenType.KEYWORD and toks[4].value == "WHERE"
    assert toks[5].type == TokenType.IDENT and toks[5].value == "aktif"


def test_lexer_operator_tidak_sama_dengan():
    # Menguji tokenizing ekspresi a <> b
    toks = tokenize("a <> b")
    assert len(toks) == 4
    assert toks[0].type == TokenType.IDENT and toks[0].value == "a"
    assert toks[1].type == TokenType.OP and toks[1].value == "<>"
    assert toks[2].type == TokenType.IDENT and toks[2].value == "b"
    assert toks[3].type == TokenType.EOF


def test_lexer_escaped_quote_string():
    # Menguji string O''Brien terurai menjadi Token(STRING, "O'Brien")
    toks = tokenize("'O''Brien'")
    assert len(toks) == 2
    assert toks[0] == Token(TokenType.STRING, "O'Brien", 1, 1)


def test_parser_recovery_berhenti_di_titik_koma():
    # Bug: _synchronize membuang token sampai EOF, statement valid ikut hilang.
    script = parse_sql("SELECT FROM; DELETE FROM sesi;")
    assert len(script.errors) == 1
    assert len(script.statements) == 1
    assert isinstance(script.statements[0], ast.Delete)


def test_parser_left_outer_join():
    # Bug: LEFT langsung diikuti JOIN, OUTER opsional tidak dikenali.
    script = parse_sql("SELECT a.id FROM t a LEFT OUTER JOIN u b ON a.id = b.id")
    assert script.errors == []
    join = script.statements[0].joins[0]
    assert join.kind == "LEFT"


def test_parser_presedensi_and_lebih_tinggi_dari_or():
    # Bug: AND dan OR sama tingkat. Seharusnya x=1 OR (y=2 AND z=3).
    script = parse_sql("SELECT a FROM t WHERE x = 1 OR y = 2 AND z = 3")
    assert script.errors == []
    where = script.statements[0].where
    assert where.op == "OR"
    assert where.right.op == "AND"


def test_parser_insert_select_dengan_daftar_kolom():
    script = parse_sql("INSERT INTO arsip (id, total) SELECT id, total FROM pesanan")
    assert script.errors == []
    stmt = script.statements[0]
    assert isinstance(stmt, ast.Insert)
    assert stmt.values == []
    assert isinstance(stmt.query, ast.Select)


def test_parser_left_join_tanpa_outer_dan_huruf_kecil():
    for sql in (
        "SELECT a.id FROM t a LEFT JOIN u b ON a.id = b.id",
        "select a.id from t a left outer join u b on a.id = b.id",
    ):
        script = parse_sql(sql)
        assert script.errors == []
        assert script.statements[0].joins[0].kind == "LEFT"


def test_parser_dua_error_dengan_statement_valid_di_antaranya():
    script = parse_sql("SELECT FROM; DELETE FROM a; UPDATE SET; DELETE FROM b;")
    assert len(script.errors) == 2
    assert len(script.statements) == 2


def test_resolver_unqualified_single_table():
    # Memastikan kolom tanpa qualifier ter-resolve ke satu-satunya tabel di scope terdalam
    script = parse_sql("SELECT nama, email FROM pengguna WHERE aktif = 1")
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert diags == []
    cols = [n for n in ast.iter_nodes(script) if isinstance(n, ast.ColumnRef)]
    assert len(cols) == 3
    for col in cols:
        assert col.resolved == "pengguna"


def test_resolver_unqualified_ambiguous_warning():
    # Memastikan kolom tanpa qualifier pada query dengan multiple tabel di scope terdalam menghasilkan warning ambigu dan resolved tetap None
    script = parse_sql("SELECT nama FROM pelanggan p JOIN pesanan o ON p.id = o.pelanggan_id")
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert len(diags) == 1
    assert diags[0].level == "warning"
    assert "ambigu tanpa skema" in diags[0].message
    col_nama = [n for n in ast.iter_nodes(script) if isinstance(n, ast.ColumnRef) and n.name == "nama"][0]
    assert col_nama.resolved is None


def test_resolver_scope_chain_shadowing():
    # Memastikan alias tabel di subquery menutupi alias yang sama di query luar (innermost-to-outermost lookup)
    sql = "SELECT t.nama FROM pelanggan t WHERE t.id IN (SELECT t.id FROM pesanan t)"
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert diags == []
    outer_sel = script.statements[0]
    outer_col = outer_sel.columns[0].expr
    assert outer_col.resolved == "pelanggan"
    subquery = outer_sel.where.query
    inner_col = subquery.columns[0].expr
    assert inner_col.resolved == "pesanan"


def test_resolver_delete_scope_isolation():
    # Memastikan scope pada statement DELETE tidak bocor ke statement setelahnya
    resolver = Resolver()
    script = parse_sql("DELETE FROM pelanggan p WHERE p.id = 1; SELECT p.nama FROM pesanan o;")
    assert script.errors == []
    diags = resolver.resolve_script(script)
    assert any(d.level == "error" and "alias 'p' tidak terdefinisi" in d.message for d in diags)
    assert resolver.scope is None


def test_analyzer_update_subquery_is_read():
    # Memastikan tabel di dalam subquery pada klausa WHERE atau assignment UPDATE dicatat sebagai 'R', bukan 'U'
    sql = "UPDATE pelanggan SET total = (SELECT SUM(nilai) FROM pesanan) WHERE id IN (SELECT id FROM arsip)"
    script = parse_sql(sql)
    assert script.errors == []
    crud_result = analyze_statement(script.statements[0])
    assert crud_result["pelanggan"] == {"U"}
    assert crud_result["pesanan"] == {"R"}
    assert crud_result["arsip"] == {"R"}
