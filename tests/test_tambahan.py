"""Test regresi dan kasus uji tambahan buatan kelompok."""
import pytest

from crud.lexer import LexError, Token, TokenType, tokenize
from crud import ast_nodes as ast
from crud.parser import parse_sql


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