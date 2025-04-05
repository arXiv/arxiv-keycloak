"""
(for now) LaTex accented characters to UTF-8 char mapper.
"""
from arxiv.util.tex2utf import tex2utf

def convert_latex_accents(text: str) -> str:
    """Converts arXiv permitted Latex char expression to UTF-8 """
    return tex2utf(text)
