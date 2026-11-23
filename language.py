"""Tell Turkish questions from English ones, so they can be routed to
components that handle Turkish (see RERANK_MODEL_TR and CHAT_MODEL_TR).

The check is deliberately simple: letters that only Turkish uses, then
common function and question words. A question it cannot place stays on the
default (English) route, which still answers it, only without the Turkish
components."""

import re

LANGUAGES = ("en", "tr")
DEFAULT_LANGUAGE = "en"

# Letters Turkish has and English does not. ç, ö and ü are left out of this
# set because they also appear in German and French names; they count as a
# weaker hint below.
TURKISH_ONLY_LETTERS = frozenset("ğışĞİŞ")
TURKISH_HINT_LETTERS = frozenset("çöüÇÖÜ")

TURKISH_WORDS = frozenset(
    """
    ve veya ile için bir bu şu o da de ki mi mı mu mü midir mıdır mudur müdür
    ne nedir neler nelerdir hangi hangisi hangileri kaç kim kimdir kimler
    nasıl neden niçin nerede ne zaman göre olarak olan ise gibi kadar
    hakkında var yok değil sayılır edilir eder hâlinde halinde
    """.split()
)

ENGLISH_WORDS = frozenset(
    """
    the a an and or of to in on at by for with from is are was were be been
    what which who whom whose how why when where does do did can could should
    would will this that these those it its as
    """.split()
)

WORD = re.compile(r"\w+")


def detect_language(text: str) -> str:
    """"tr" for Turkish text, otherwise "en"."""

    if any(char in TURKISH_ONLY_LETTERS for char in text):
        return "tr"

    words = WORD.findall(_lower(text))
    turkish = sum(word in TURKISH_WORDS for word in words)
    english = sum(word in ENGLISH_WORDS for word in words)

    if any(char in TURKISH_HINT_LETTERS for char in text):
        turkish += 1

    return "tr" if turkish > english else DEFAULT_LANGUAGE


def _lower(text: str) -> str:
    # Turkish dotted and dotless I lowercase differently from English.
    return text.replace("I", "ı").replace("İ", "i").lower()
