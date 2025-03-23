"""
(for now) LaTex accented characters to UTF-8 char mapper.
"""

from typing import Dict

LATEX_ACCENTS: Dict[str, str] = {
    "\\'e": "é", "\\'a": "á", "\\'i": "í", "\\'o": "ó", "\\'u": "ú",
    '\\"u': "ü", '\\"o': "ö", '\\"a': "ä",
    "\\`e": "è", "\\`a": "à",
    "\\^e": "ê", "\\^a": "â", "\\^o": "ô",
    "\\~n": "ñ", "\\c{c}": "ç",
    "\\'E": "É", "\\'A": "Á", "\\'I": "Í", "\\'O": "Ó", "\\'U": "Ú",
    '\\"e': "ë", '\\"i': "ï", '\\"E': "Ë", '\\"O': "Ö", '\\"U': "Ü",
    "\\`i": "ì", "\\`o": "ò", "\\`u": "ù",
    "\\^i": "î", "\\^u": "û",
    "\\~N": "Ñ", "\\c{C}": "Ç",
    "\\={a}": "ā", "\\={A}": "Ā",
    "\\.{i}": "ı̇",
    "\\v{c}": "č", "\\v{C}": "Č",
    "\\H{o}": "ő", "\\H{O}": "Ő",
    "\\u{g}": "ğ", "\\u{G}": "Ğ",
}


def convert_latex_accents(text: str) -> str:
    """Converts arXiv permitted Latex char expression to UTF-8 """
    for latex, utf8 in LATEX_ACCENTS.items():
        if '\\' not in text:
            break
        text = text.replace(latex, utf8)
    return text
