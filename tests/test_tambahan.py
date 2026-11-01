"""Test regresi dan kasus uji tambahan buatan kelompok."""
import pytest

from crud.lexer import LexError, Token, TokenType, tokenize


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
