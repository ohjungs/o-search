"""HTML 에서 제목·본문 텍스트를 뽑고, meta robots 의 색인 거부 선언을 읽는다."""
import html.parser

_SKIP_TAGS = {"script", "style", "noscript"}

# 인라인(phrasing) 태그는 단어 안에 끼어든다 — 경계에 공백을 넣으면 Kim<b>chi</b> 가
# "Kim chi" 로 쪼개져 검색이 안 된다. <br> 은 줄바꿈이므로 일부러 뺐다.
_INLINE_TAGS = {
    "a", "abbr", "b", "bdi", "bdo", "cite", "code", "data", "dfn", "em", "i",
    "kbd", "mark", "q", "rp", "rt", "ruby", "s", "samp", "small", "span",
    "strong", "sub", "sup", "time", "u", "var", "wbr",
}

# 신뢰 경계: 크롤한 콘텐츠에 섞인 터미널 제어열(ANSI)·NUL 을 지운다.
# 공백류 제어문자는 아래 split() 이 이미 처리하므로 정규화 뒤에 태운다.
_CONTROL = dict.fromkeys(list(range(0x20)) + [0x7F] + list(range(0x80, 0xA0)))


class _TextParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def _separate(self):
        target = self.title_parts if self._in_title else self.text_parts
        target.append(" ")

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
            return
        if tag in _INLINE_TAGS:
            return
        # 인라인이 아닌 태그가 나왔으면 닫히지 않은 <title> 이 끝난 것으로 본다 (깨진 HTML)
        self._in_title = False
        self._separate()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _INLINE_TAGS:
            return
        if tag == "title":
            self._in_title = False
        elif tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        self._separate()

    def handle_data(self, data):
        if self._skip_depth:
            return
        target = self.title_parts if self._in_title else self.text_parts
        target.append(data)


def _normalize(parts):
    return " ".join("".join(parts).split()).translate(_CONTROL)


class _MetaRobotsParser(html.parser.HTMLParser):
    """<meta name="robots"> 의 content 만 모은다. 태그명·속성명은 HTMLParser 가 소문자로 준다."""

    def __init__(self):
        super().__init__()
        self.directives = []

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attr = dict(attrs)
        if (attr.get("name") or "").strip().lower() == "robots":
            self.directives.append(attr.get("content") or "")


def is_noindex(html_text):
    """<meta name="robots"> 가 noindex 또는 none 을 선언하면 True (색인 거부)."""
    # ponytail: 원문에 'robots' 가 없으면 파싱조차 안 한다. 천장 — name 을 엔티티로
    #           인코딩한 문서(&#114;obots)는 놓친다. 실물에서 보이면 필터를 뺀다
    if "robots" not in html_text.lower():
        return False
    parser = _MetaRobotsParser()
    parser.feed(html_text)
    parser.close()
    for content in parser.directives:
        # 구분자는 쉼표와 공백 둘 다다 — content="noindex nofollow" 도 유효한 표기
        if {"noindex", "none"} & set(content.lower().replace(",", " ").split()):
            return True
    return False


def extract_text(html_text):
    """(title, text) 를 돌려준다. 제목이 없으면 빈 문자열."""
    parser = _TextParser()
    parser.feed(html_text)
    parser.close()
    return _normalize(parser.title_parts), _normalize(parser.text_parts)
