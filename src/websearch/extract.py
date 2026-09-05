"""HTML 에서 제목·본문 텍스트를 뽑고, meta robots 의 색인 거부 선언을 읽는다."""
import html.parser
import re

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

# `_INLINE_TAGS` 밖이지만 **문단 경계도 아닌** 태그 — 한 문단 *안에* 끼어든다.
# `_INLINE_TAGS` 로 옮기면 낱말이 붙어(`김치찌개된장찌개`) 색인 본문이 바뀌므로
# 재색인이지만, 여기는 `_separate(block=...)` 의 인자라 **`_BlockParser` 만 읽는다**
# — 색인 경로(`extract_text`)는 한 글자도 안 바뀐다(계획 48 리뷰 5).
_NON_BLOCK_TAGS = _SKIP_TAGS | {
    "br", "img", "picture", "source", "map", "area", "svg", "math",
    "del", "ins", "label", "font", "big", "strike", "tt",
    "button", "input", "select", "textarea", "output", "progress", "meter",
    "audio", "video", "canvas", "embed", "object", "iframe",
}

# HTML 에 **종료 태그가 없는** 요소. 여기로 숨김 영역을 열면 닫을 태그가 영영 안 와서
# 문서의 나머지를 통째로 삼킨다(설계 51 2절에서 깬 가정 — 네 모양 전부 3블록 → 1블록).
# void 요소는 텍스트를 담을 수 없으니 안 열어도 잃는 것이 없고, `aria-hidden="true"` 를
# 단 장식 `<img>` 는 실물에서 가장 흔한 모양이다.
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# **종료 태그 생략이 허용된** 요소 — 「어떤 시작 태그가 이것을 암묵적으로 닫는가」.
# 명세가 허용하는 정상 HTML 이라 «안 닫힌 컨테이너» 천장이 안 덮는다(리뷰 51 [R51-1]).
#
# **키는 명세의 「optional tags」 열여섯 전부다**(리뷰 51 [R51-5]: 여덟만 있어
# `<thead hidden>` 다음의 `<tbody>` 가 숨김을 못 걷었고 **보이는 문단이 통째로
# 사라졌다** — 오탐 방향). 값은 각 삽입 모드가 적은 목록을 그대로 옮긴다.
# **전부 닫힌 집합이다 — `p` 도 그렇다.** `p` 를 «인라인도 비블록도 아닌 것 전부» 로
# 쓰면(리뷰 2 [R51-3]) 술어가 열린 집합이 되고, 명세가 `<p>` 를 닫지 않는다고 적은
# 태그까지 닫아 그 뒤의 **숨은 텍스트가 근거 문단으로 샌다**(표준 태그 전수 대조에서
# 과잉 29 · 미달 0, 그리고 대시가 든 **커스텀 요소는 전부** 과잉이라 그쪽은 무한
# 집합이다). 여집합으로는 못 적는 이유가 그것이라 명세 목록을 그대로 옮겼다.
# 아래 `p` 목록은 파싱 알고리즘이 "close a p element" 를 부르는 시작 태그 전부다
# — 종료 태그 생략 목록(`address`…`ul`)보다 넓어 `li`·`dd`·`dt`·`summary`·`dialog`
# 도 든다 — 더하기 표 문맥에서 셀·행을 닫으며 `<p>` 를 함께 걷는 표 구조 태그.
# ponytail: 표 구조 태그(`tr`·`td`…)는 **표 밖에서도** 닫는다. 브라우저는 표 밖의
# 그것을 무시하므로 그 자리에서만 넓게 닫지만, 표 밖 `<td>` 는 깨진 입력이고
# 표 안의 안 닫힌 `<p>` 는 실물의 기본형이다(리뷰 51 [R51-1] 이 넣은 그 행).
# 표 구조 시작 태그 — 삽입 모드 「in cell」·「in row」·「in table body」·「in caption」이
# 전부 이 목록으로 열린 셀·행·구획을 걷는다. 빼는 쪽이 «자식으로 들어가는 것»이다:
# 셀은 행 **안**이라 `<td>` 는 `<tr>` 을 안 닫고, 행은 구획 안이라 `<tr>` 은 `<tbody>`
# 를 안 닫으며, `<col>` 은 `<colgroup>` 안이다. 그 뺄셈이 누출(과잉 닫기)을 막는다
_TABLE_PARTS = {"caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
                "thead", "tr"}
_IMPLIED_END = {
    "li": {"li"},
    "dt": {"dt", "dd"}, "dd": {"dt", "dd"},
    "td": _TABLE_PARTS, "th": _TABLE_PARTS, "caption": _TABLE_PARTS,
    "tr": _TABLE_PARTS - {"td", "th"},
    "thead": _TABLE_PARTS - {"td", "th", "tr"},
    "tbody": _TABLE_PARTS - {"td", "th", "tr"},
    "tfoot": _TABLE_PARTS - {"td", "th", "tr"},
    "colgroup": _TABLE_PARTS - {"col"},
    # 「in select」 삽입 모드는 `<hr>` 에서도 열린 `option`·`optgroup` 을 걷는다
    # (명세가 `<select>` 안의 구분선으로 허용한 태그다 — 리뷰 4 [R4-1]: 빼면
    # `<optgroup hidden>` 뒤 `<hr>` 다음의 **보이는 항목이 통째로 사라진다**)
    "option": {"option", "optgroup", "hr"}, "optgroup": {"optgroup", "hr"},
    "rt": {"rt", "rp", "rb", "rtc"}, "rp": {"rt", "rp", "rb", "rtc"},
    "p": {
        "address", "article", "aside", "blockquote", "center", "details",
        "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure",
        "footer", "form", "header", "hgroup", "hr", "listing", "main", "menu",
        "nav", "ol", "p", "plaintext", "pre", "search", "section", "summary",
        "table", "ul", "xmp",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "dd", "dt",
        "caption", "colgroup", "tbody", "tfoot", "thead", "tr", "td", "th",
    },
}

# `font-size:0` 은 **부분문자열로 보면 안 된다** — `font-size:0.9em` 은 보이는 작은
# 글씨인데 그것이 문다. 이 판정에서 오탐이 가장 가까운 자리다
_ZERO_FONT = re.compile(r"font-size:0(?![.0-9])")


def _is_hidden(tag, attrs):
    """시작 태그 하나만 보고 «사람에게 안 보이는가» 를 답한다 — `_BlockParser` 전용.

    ponytail: HTML 한 장만 본다. 외부 스타일시트·클래스·`visibility:hidden`·
    `opacity:0`·화면 밖 좌표·`clip-path`·JS 로 감춘 것은 **못 본다** — CSS 파서를
    안 만든다. 올리려면 크롤러가 스타일시트까지 받아 와야 하고 그것은 다른 계획이다.
    `aria-hidden` 은 «화면» 이 아니라 «접근성 트리» 지만 그래도 뺀다: 근거 문단의
    계약은 «부르는 쪽이 사람에게 내보일 수 있는 텍스트» 이고, 접근성 트리에서 빠진
    텍스트는 모든 사용자에게 도달 가능하지 않다.
    """
    if tag == "template":  # 렌더되지 않는 조각
        return True
    attr = dict(attrs)
    if "hidden" in attr:  # 불리언 속성 — 값이 무엇이든 숨김
        return True
    if (attr.get("aria-hidden") or "").strip().lower() == "true":
        return True
    # 공백을 통째로 지운 뒤 부분문자열로 본다 — `display: none`·`DISPLAY:NONE`·
    # `;display:none!important` 가 한 규칙에 들어온다
    style = "".join((attr.get("style") or "").split()).lower()
    return "display:none" in style or _ZERO_FONT.search(style) is not None


class _Parser(html.parser.HTMLParser):
    """`html.parser` 가 크롤 HTML 에서 **예외로 나가는** 자리 하나를 막는다.

    `_markupbase` 는 `<![cdata[`·`<![if` 처럼 아는 키워드가 아닌 marked section
    (`<![foo]>`)을 만나면 `error()` 를 부르고, `HTMLParser` 는 그것을 안 덮어
    **`NotImplementedError` 가 `feed()` 밖으로 나간다.** 크롤 HTML 은 남이 쓴
    입력이라 페이지 한 장이 `index_pages()` 전체를 세우고(커밋이 루프 끝에 있어
    그 실행의 색인이 통째로 날아간다) `/passages` 는 500 이 된다 — 아무나 만들 수
    있는 여덟 글자다. HTML 명세는 아는 선언이 아닌 `<!` 를 **bogus comment** 로
    읽어 다음 `>` 까지 버리므로 브라우저와 같은 쪽으로 떨어뜨린다.
    ponytail: 키워드 목록을 여기 베끼지 않는다 — stdlib 이 아는 것은 stdlib 이
    처리하게 두고 **터지는 가지만** 받는다. 버전이 예외 종류를 바꿔도(3.13 은
    `AssertionError`) 같은 자리로 떨어지도록 둘 다 받는다
    """

    def parse_marked_section(self, i, report=1):
        try:
            return super().parse_marked_section(i, report)
        except (NotImplementedError, AssertionError):
            return self.parse_bogus_comment(i)


class _TextParser(_Parser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def _separate(self, block=True):
        # `block` 은 «이 자리가 **문단** 경계인가» 다 — `_NON_BLOCK_TAGS` 는 아니다.
        # 색인 경로는 둘을 똑같이 공백 한 칸으로 보므로 여기서는 안 읽는다.
        # 읽는 것은 `_BlockParser` 뿐이고, 그것이 `<br>` 을 문단으로 끊던 자리다
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
        self._separate(tag not in _NON_BLOCK_TAGS)
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _INLINE_TAGS:
            return
        if tag == "title":
            self._in_title = False
        elif tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        self._separate(tag not in _NON_BLOCK_TAGS)

    def handle_data(self, data):
        if self._skip_depth:
            return
        target = self.title_parts if self._in_title else self.text_parts
        target.append(data)


def _normalize(parts):
    return " ".join("".join(parts).split()).translate(_CONTROL)


class _MetaRobotsParser(_Parser):
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


class _BlockParser(_TextParser):
    """`_TextParser` 가 **이미 부르고 있는** `_separate()` 자리에서 본문을 끊는다.

    **부모가 부르는 자리가 전부 문단 경계인 것은 아니다** — `<br>` 은 줄바꿈이라
    `_INLINE_TAGS` 에서 일부러 빠져 있고(위 주석), 색인엔 공백 한 칸이지만 여기서는
    문단 경계로 읽혔다. 한 문단이 낱말 조각으로 흩어지면 4자짜리 조각이 근거 자리를
    이긴다(계획 48 리뷰 4 실측). 그래서 부모가 `block` 으로 그 하나를 갈라 준다.
    **색인 경로(`extract_text`)는 여전히 지나가지 않는다.**
    """

    def __init__(self):
        super().__init__()
        self.blocks = []
        self._open = []  # 열려 있는 블록 태그 — 꼭대기가 이름표다
        # 열려 있는 **모든** 비-void 요소 — `(태그, 조상 중 하나라도 숨김인가)`.
        # 꼭대기의 두 번째 칸이 「지금 숨김 안인가」다(전파해 두므로 O(1)).
        # **숨긴 태그만 담으면 안 된다** — 닫을 때 이름으로 찾는데 성긴 스택이면
        # 숨김 컨테이너 안의 **같은 이름 자식**이 바깥 숨김을 함께 풀어 버린다
        # (테스트 51 실측: `<div hidden><div>속</div><p>숨은</p></div>` 가 샜다).
        # `_open` 이 같은 관용구로 안전한 것은 그쪽이 빈틈없는 스택이기 때문이다.
        self._els = []

    def _flush(self):
        block = _normalize(self.text_parts)
        if block:
            self.blocks.append((self._open[-1] if self._open else "", block))
        del self.text_parts[:]

    def handle_starttag(self, tag, attrs):
        # 블록에 **자기를 낸 태그**를 붙여 준다. 부모가 먼저 이전 블록을 끊으므로
        # 스택은 그 뒤에 쌓는다 — 끊기는 블록의 주인은 아직 앞 태그다.
        # 문단 안에 끼어드는 태그(`<img>`·`<script>`)는 주인이 아니라 지나간다
        super().handle_starttag(tag, attrs)
        # 브라우저처럼 **암묵적으로 닫는다** — `html.parser` 는 안 닫아서 `<li hidden>`
        # 의 숨김이 **다음 형제로 샜다**(리뷰 51 [R51-1]: 보이는 문단이 조용히 사라진다).
        # 꼭대기만 본다 — 닫히는 것은 형제뿐이고 숨긴 요소의 **자식**은 숨김 그대로다.
        # **이름표 스택도 함께 걷는다** — 암묵적 닫기는 `</p>` 와 같은 사건이라 여기서
        # 안 걷으면 그 뒤 텍스트가 이미 끝난 태그의 이름표를 달고 나가고(테스트 3),
        # `_open` 이 «안 닫힌 `<p>` 수» 만큼 쌓여 아래 닫기 비용이 깊이²로 간다
        # (실측 `<p>가<span>나</span>` × 1,250 · 캡 35,000자: `_open` 최대 **1250 → 1**
        # · 0.422 → **0.304ms/1000자**. 이름표는 제품이 아직 안 읽지만 비용은 실물이다)
        while self._els and tag in _IMPLIED_END.get(self._els[-1][0], ()):
            if self._open and self._open[-1] == self._els[-1][0]:
                self._open.pop()
            self._els.pop()
        # 숨김은 **부모가 앞 블록을 끊은 뒤에** 연다 — 먼저 열면 직전 블록의 꼬리가
        # 사라진다. 인라인·비블록 태그도 숨길 수 있어 아래 early-return 보다 앞이다
        if tag not in _VOID_TAGS:
            self._els.append((tag, (self._els and self._els[-1][1])
                              or _is_hidden(tag, attrs)))
        # `<title>` 은 부모가 블록을 **안 끊고** 돌아간다 — 안 끊었으면 주인도 안 바뀐다
        # (리뷰 6 [R6-2]: `<p>김치<title>제목</title>` 의 이름표가 `title` 로 샜다)
        if self._in_title or tag in _INLINE_TAGS or tag in _NON_BLOCK_TAGS:
            return
        self._open.append(tag)

    def handle_endtag(self, tag):
        # 닫는 태그는 주인을 **바깥 태그로 되돌린다** — `</p>` 뒤의 꼬리 텍스트는
        # `<p>` 가 아니라 그것을 감싼 `<article>` 것이다(리뷰 6 [R6-2]).
        # 열린 적 없는 닫는 태그는 버린다. 같은 이름이 겹쳐 있으면 안쪽부터 닫는다
        super().handle_endtag(tag)
        if tag in self._open:
            del self._open[len(self._open) - self._open[::-1].index(tag) - 1:]
        # 요소 스택도 **뒤에서 찾아 자른다** — 깊이 카운터는 짝이 안 맞는 닫는 태그에서
        # 어긋나고, 그러면 그 뒤의 본문이 통째로 사라진다. 이쪽은 빈틈이 없으므로
        # 이름으로 찾아도 바깥 숨김이 안 풀린다. 다만 `_open` 의 관용구(이름 리스트를
        # 떠서 뒤집는다)를 그대로 쓰면 안 된다 — `_els` 는 **모든 비-void 요소**를
        # 담아 닫는 태그마다 리스트를 새로 만들면 비용이 깊이²다(리뷰 51 [R51-2]:
        # 캡 35,000자 안 최악 11.5배). 제자리에서 뒤에서부터 훑으면 같은 답이 싸다
        for i in range(len(self._els) - 1, -1, -1):
            if self._els[i][0] == tag:
                del self._els[i:]
                break

    def handle_data(self, data):
        # 숨김 영역 안의 텍스트는 **애초에 안 담는다** — 블록을 사후에 버리면
        # 컨테이너 중첩(`<div hidden><p>…</p></div>`)에서 자식 `<p>` 가 새 블록을
        # 열어 그대로 빠져나가고, 문단 안 인라인 숨김은 문단을 통째로 죽인다.
        # ponytail: 안 닫힌 숨김 컨테이너는 그 뒤를 전부 삼킨다(`MAX_PASSAGE_HTML`
        # 로 잘린 자리 포함) — 방향이 «문단을 덜 낸다» 라 계약을 어기지 않는다
        if self._els and self._els[-1][1]:
            return
        super().handle_data(data)

    def _separate(self, block=True):
        if self._in_title or not block:
            # 제목은 블록이 아니고, `<br>` 은 **줄바꿈이지 문단이 아니다**. 둘 다
            # 부모 그대로 공백 한 칸이라 색인과 같은 텍스트가 나온다 — 불변식이 산다
            super()._separate()
        else:
            self._flush()

    def close(self):
        # **어디까지가 온전한지는 파서에게 묻는다.** 안 닫힌 주석·선언·인용된 속성값은
        # 자기 안에 `>` 를 담을 수 있어(`<!-- a>`·`title="a > b"`) 문자열 규칙으로는
        # 끝을 못 찾는다. `feed()` 가 삼키지 못하고 남긴 꼬리가 곧 그 답이고,
        # `close()` 는 그것을 **데이터로 흘려** 소비자에게 마크업 조각을 준다.
        # `<` 로 시작할 때만 버린다 — 잘린 엔티티(`&am`)는 평문이라 마크업으로 안 새고,
        # `convert_charrefs` 가 앞 텍스트까지 붙들고 있어 버리면 문단이 통째로 사라진다.
        if self.rawdata.startswith("<"):
            self.rawdata = ""
        super().close()
        # 닫히지 않은 마지막 블록(`<p>가<p>나<div>다`)은 여기서만 나온다
        self._flush()


def extract_blocks(html_text):
    """본문을 블록(문단) 단위로 끊어 `(태그, 텍스트)` 로 돌려준다. 빈 블록은 안 낸다.

    태그는 **열려 있는 가장 안쪽 블록 태그**다. **오늘 이것을 읽는 소비자는 없다** —
    `/passages` 응답은 `{url,title,position,text}` 뿐이고 `passages()` 는 `_tag` 로
    버린다(리뷰 7 실측 · 지우는 판단은 `digest.md ## 다음 계획 후보`).
    근거를 고르는 자가 안 읽는 이유는 계획 48 갈림길 6 이다:
    이름표는 컨테이너를 못 봐서 `<footer><p>ⓒ…</p></footer>` 가 `p` 로 나오고,
    실물에서 가장 흔한 `<p>` 대 `<p>` 동점을 못 가른다(리뷰 6 재측 12/19 · 길이 15/19).
    그 갈림길은 손잡이가 아니라 **실물 크롤 코퍼스**로 닫힌다.

    **화면에 안 보이는 텍스트는 블록으로 안 낸다**(계획 51) — `<template>`·`hidden`·
    `aria-hidden="true"`·`display:none`·`font-size:0` 다섯 모양(`_is_hidden`).
    색인 본문(`extract_text`)은 그대로라 그 문서는 검색 결과에 계속 나온다.

    불변식: `" ".join(t for _tag, t in extract_blocks(h)) == extract_text(h)[1]`
    # 예외 셋 — 앞의 둘은 **깨진 입력에서만** 갈리고 정상 HTML 에서는 같다.
    # ① EOF 에 남은 안 닫힌 마크업: 색인 경로는 그것을 데이터로 흘리고
    #    (색인은 통짜 본문이라 상관없다) 블록 쪽은 버린다. 문단은 사람이 읽는
    #    텍스트여야 하고 소비자가 기계라 마크업 조각을 주면 안 된다.
    # ② ponytail: **블록 전체가 제어문자**면 통짜 쪽은 겹공백(`'가  나'`)을 남기고
    #    블록 쪽은 그 블록을 버린다. 천장을 여기 적고 고치지 않는다: 맞추려면 `_normalize` 를
    # 바꿔야 하고 그것이 **색인 본문을 바꾼다**. 현 동작은 테스트에 고정돼 있다
    # ③ **숨은 텍스트가 있는 HTML** — 앞의 둘과 달리 정상 입력에서 갈린다. 색인은
    #    담고 블록은 뺀다. 바뀌는 것은 근거 후보뿐이고 방향은 «덜 낸다» 쪽이다
    """
    parser = _BlockParser()
    parser.feed(html_text)
    parser.close()
    return parser.blocks
