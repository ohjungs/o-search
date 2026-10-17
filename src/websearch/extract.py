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
    # ponytail: 원문에 'robots' 도 문자참조도 없으면 파싱조차 안 한다. `&#` 갈래가
    #           엔티티로 인코딩한 name(&#114;obots·&#x72;obots)을 파서까지 데려간다 —
    #           속성값 언이스케이프는 HTMLParser 가 이미 한다. 천장 — 명명 엔티티로는
    #           'r' 을 못 쓰므로 `&#` 이면 충분하다. 오탐은 안 는다(판정은 파서가 한다)
    lowered = html_text.lower()
    if "robots" not in lowered and "&#" not in lowered:
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
        # 열려 있는 **모든** 비-void 요소 — `(태그, 숨김인가, 링크 안인가)`.
        # 꼭대기의 두 번째 칸이 「지금 숨김 안인가」, 세 번째가 「지금 `<a>` 안인가」다
        # (둘 다 전파해 두므로 O(1)). 셋째 칸을 쓰는 곳은 `handle_data` 의 산문 판정
        # 하나뿐이고, 거기서 `_els` 를 훑으면 **가장 뜨거운 경로가 O(깊이)** 가 된다 —
        # 리뷰 51 [R51-2] 가 같은 클래스에서 깊이² 비용을 이미 한 번 잡았다.
        # **숨긴 태그만 담으면 안 된다** — 닫을 때 이름으로 찾는데 성긴 스택이면
        # 숨김 컨테이너 안의 **같은 이름 자식**이 바깥 숨김을 함께 풀어 버린다
        # (테스트 51 실측: `<div hidden><div>속</div><p>숨은</p></div>` 가 샜다).
        # `_open` 이 같은 관용구로 안전한 것은 그쪽이 빈틈없는 스택이기 때문이다.
        self._els = []
        # 직전에 `</a>` 가 닫혔고 그 뒤로 **공백 아닌 글자가 없는가** — 내비·목차처럼
        # 링크가 연달아 오는 모양을 가른다. `<a>` 가 `_INLINE_TAGS` 라 링크 텍스트가
        # 공백 없이 한 블록으로 붙고, 그 블록의 점수가 **링크 수의 합**이 돼 본문 한
        # 문단이 구조적으로 진다(계획 115 · `indexer.passages` 의 `score`).
        # **«인접» 이 범위의 전부다** — 문단 안에 하나 낀 링크(`<p>가<a>나</a>다</p>`)
        # 와 링크 사이에 글자가 든 산문(`<p><a>가</a>그리고<a>나</a></p>`)은 안 끊는다.
        # ponytail: 안 닫힌 `<a>` 는 안 센다(`<nav><a>가<a>나</nav>`) — 브라우저는
        # 중첩 링크를 금지해 앞엣것을 닫지만 `html.parser` 는 안 닫는다. 방향이
        # «덜 끊는다» 라 계약을 어기지 않고, 실물에서 세지면 `_els` 에 `a` 가 열려
        # 있는지를 함께 보면 된다
        # **천장 ⓐ 는 닫혔다 — 계획 116 이 앞쪽, 계획 118 이 뒤쪽이다.**
        # **단 `<a>` 가 제대로 닫힌 모양에서다**(리뷰 118 [A-3] 실측): 중첩·미닫힘
        # (`<p><a>가</a><a>나<a>다</a> 에서 …</p>`)은 바깥 `a` 가 `_els` 에 남아
        # 뒤따르는 산문이 **산문으로 안 잡히고**, 그래서 두 트리가 같게 끊는다.
        # 아래 `ponytail:` 이 적은 「안 닫힌 `<a>` 는 안 센다」의 뒷면이다 —
        # `digest` 후보로 등재했다.
        # 깃발은 **앞으로만** 흐르므로 계획 116 은 산문이 링크 **뒤** 에 오는 모양
        # (`<p><a>레시피</a><a>영상</a> 에서 김치찌개를…</p>`)을 못 닫았다 — 끊긴 뒤에
        # 올 글자를 스트리밍 파서가 미리 볼 수 없다(리뷰 116 [R116-3] 이 그 선을 쟀고
        # 계획 117 이 실물 **46문서 4.6%** · 블록 301/307,951 로 빈도를 쟀다).
        # **계획 118 이 끊김을 블록 끝으로 미뤘다** — 경계는 `_cuts` 표식으로만 쌓이고
        # 판정은 `_flush` 한 곳이다. 실물 1,000문서에서 끊김 자리 **422/3,481(12.1%)**
        # 이 사라졌고(블록 307,951 → 307,825 · 바뀐 문서 43) **새로 끊는 자리는 0**
        # 이다 — 표식은 버릴 수만 있고 새로 만들 길이 없다
        # (설계 `docs/design_history_093.md`). 앞쪽 반쪽은 아래다 —  「산문 속 인접 링크도 끊는다」가
        # `ohse.de/uwe/software/lrzsz.html` 의 근거를 279자(score 2) → **212자
        # 조각(score 1)** 으로 떨어뜨렸다. 그래서 경계는 이제 **링크 밖 글자가 아직
        # 안 쌓인 블록에서만** 선다(아래 `_prose`). **실물 520문서를 두 트리로 재서
        # 끊김 자리 2,259 가 사라졌다**(블록 223,167 → 220,908 · 1.0% · 블록 수가
        # 바뀐 문서 166/520 = 31.9%). 내비 모양은 그대로 끊긴다 — 설계 census 에서
        # `section` 끊김 821 중 산문이 **0** 이었다. 근거 문단은 110문서에서
        # **동일 94 · 길어짐 1 · 짧아짐 0 · 자리만 15** 로 **나빠진 것이 없다**
        # — 설계 `docs/design_history_091.md` · 결과
        # `docs/e2e/prose-link-boundary/result.md`.
        # **천장 ⓑ 는 남아 있다 — 리뷰 115 가 실물에서 쟀다.** 「인접만 끊는다」의
        # 직접 결과라 결함이 아니고, 고치려면 설계가 갈린다(사람 몫 · `digest` 후보 `[6]`):
        # ⓑ **구분자가 끼면 안 끊는다** — `<a>가</a> | <a>나</a>` · `<a>가</a><br><a>나</a>`
        #   · `<a>가</a><img><a>나</a>` 는 한 블록으로 남는다(글자·시작 태그가 깃발을
        #   내린다). 빵부스러기·아이콘 내비가 그 모양이라 「링크 수의 합」이 거기 남아
        #   있다 — 실물 110문서에서 블록이 30.9% 움직였는데 근거는 2건만 바뀐 이유다
        self._after_link = False
        # **이 블록에 링크 «밖» 글자가 쌓였나** — 쌓였으면 산문이라 인접 링크로 안
        # 끊는다(계획 116 · 천장 ⓐ). **블록마다 새로 판정한다** — `_flush` 에서 안
        # 내리면 첫 문단 뒤의 모든 내비가 안 끊긴다. 계획 118 부터 이 깃발을 **블록
        # 끝에서** 읽으므로 뜻이 「아직 안 쌓였나」가 아니라 「이 블록에 있었나」다
        self._prose = False
        # 인접 링크 경계가 설 **자리**(`text_parts` 인덱스)만 모은다 — 끊는 것은
        # `_flush` 다. `_prose` 와 같은 자리에서 비워야 한다(안 비우면 다음 블록이
        # 남의 오프셋으로 잘린다 · 설계 `## 계약` 4). 조각마다 다른 이름표를 달지
        # 않는 근거는 실물 1,000문서에서 **끊는 자리와 블록 끝의 이름표 불일치 0**
        # 이다(설계 `## 가정` · 백지 패스가 20만 문서로 다시 쟀고 역시 0).
        # **이 오프셋은 「`text_parts` 가 `_flush` 밖에서 줄지 않는다」에 기댄다**
        # (리뷰 118 [A-6]) — 지금은 참이고(부모는 append 만 한다) 강제하는 자는
        # 없다. 누가 여기에 상한을 걸거나 앞을 자르면 **조용히** 어긋난다
        self._cuts = []

    def _flush(self):
        label = self._open[-1] if self._open else ""
        # **표식은 산문이 없는 블록에서만 경계가 된다.** 끊김을 그 자리에서 내지 않고
        # 여기까지 미뤘기 때문에 산문이 링크 **뒤** 에 와도 보인다 — 계획 116 은
        # 깃발이 앞으로만 흘러 그 반쪽을 못 닫았다(천장 ⓐ-b · 실물 46문서 4.6%).
        # **미루는 쪽이 아니면 바이트가 달라진다** — 조각을 나중에 이어 붙이는 쪽은
        # 링크 사이 원문 공백을 되살릴 수 없다(합쳐질 블록 97 중 **96** 이 공백 한 칸을
        # 잃는다 · 설계 `docs/design_history_093.md` `## 대안 비교` B).
        # **비용은 공짜가 아니다 — 잰 대로 적는다**(리뷰 118 [A-2]). 표식이 없어도
        # `extract_blocks` 전구간이 **+2.7~7.8%**(백지 패스 min-of-12 · 잡음 0.4%) ·
        # 같은 자리 다른 판에서 **+17%**(문단 10만 세 판 중앙 0.615 → 0.722s) 느리다.
        # **원인 귀속은 미증명이다** — `label` 을 다시 게으르게 돌리는 판과 갈래를
        # 둘로 가르는 판을 둘 다 재 봤는데 회복이 없었다(그래서 짧은 쪽을 남겼다).
        # 예산 대비로 적는다: `passage_eval` p95 **1.70ms** / 컨셉 성능 5 의 **500ms**.
        # 표식이 서는 블록은 실물에서 3,481/307,951 = **1.1%** 다
        if self._prose or not self._cuts:
            segments = (self.text_parts,)
        else:
            edges = [0] + self._cuts + [len(self.text_parts)]
            segments = [self.text_parts[a:b] for a, b in zip(edges, edges[1:])]
        for parts in segments:
            block = _normalize(parts)
            if block:
                self.blocks.append((label, block))
        del self.text_parts[:]
        del self._cuts[:]
        self._prose = False

    def handle_starttag(self, tag, attrs):
        # 블록에 **자기를 낸 태그**를 붙여 준다. 부모가 먼저 이전 블록을 끊으므로
        # 스택은 그 뒤에 쌓는다 — 끊기는 블록의 주인은 아직 앞 태그다.
        # 문단 안에 끼어드는 태그(`<img>`·`<script>`)는 주인이 아니라 지나간다
        # 인접한 링크 사이는 문단 경계다 — `super()` 가 `<a>` 를 인라인으로 보고
        # early-return 하므로 **그보다 앞에서** 끊어야 앞 링크의 텍스트가 산다
        if tag == "a" and self._after_link and not self._prose:
            self._cuts.append(len(self.text_parts))
        self._after_link = False
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
                              or _is_hidden(tag, attrs),
                              tag == "a" or bool(self._els and self._els[-1][2])))
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
        # **숨김·스킵 안에서 닫힌 링크는 안 센다** — 깃발이 거기서 서면 다음 `<a>` 가
        # 블록을 끊는데, 그때 끊기는 것은 숨은 글자가 아니라 **그 앞의 보이는 문단**이다
        # (`<p>본문은<span style=display:none><a>광고</a><a>제휴</a></span> 이어진다</p>`
        # 이 다섯 글자 조각을 근거로 냈다). 위 docstring 이 `<br>` 을 `_NON_BLOCK_TAGS`
        # 로 뺀 이유와 **같은 자리**다 — 조각이 근거 자리를 이긴다(계획 48 리뷰 4).
        # 실물 1,600문서 실측: 이 깃발이 숨김 안에서 서던 자리가 **688문서·4,130회**인데
        # 블록이 바뀐 문서는 **0건**이었다(전부 빈 `text_parts` 라 `_flush` 가 no-op).
        # 오늘은 무해하지만 앞에 보이는 글자 한 조각만 있으면 조각이 나온다 — 그래서
        # 「실물에 없다」가 아니라 「경계가 숨김을 봐야 한다」로 닫는다 (리뷰 115 [R115-2])
        self._after_link = (tag == "a" and not self._skip_depth
                            and not (self._els and self._els[-1][1]))

    def handle_data(self, data):
        # 숨김 영역 안의 텍스트는 **애초에 안 담는다** — 블록을 사후에 버리면
        # 컨테이너 중첩(`<div hidden><p>…</p></div>`)에서 자식 `<p>` 가 새 블록을
        # 열어 그대로 빠져나가고, 문단 안 인라인 숨김은 문단을 통째로 죽인다.
        # ponytail: 안 닫힌 숨김 컨테이너는 그 뒤를 전부 삼킨다(`MAX_PASSAGE_HTML`
        # 로 잘린 자리 포함) — 방향이 «문단을 덜 낸다» 라 계약을 어기지 않는다
        if self._els and self._els[-1][1]:
            return
        super().handle_data(data)
        # 공백만이면 여전히 «인접» 이다 — 실물 내비는 링크 사이에 줄바꿈이 있다.
        # 숨김 영역이면 위에서 돌아가 이 줄에 **안 온다.** 그래도 남은 깃발이 보이는
        # 문단을 끊는 일은 없다 — `handle_endtag` 가 숨김 안에서는 깃발을 애초에
        # 안 세운다(아래 그 자리). 처음 판은 여기 「끊는 쪽이 맞다」고 적었는데,
        # 끊기는 것이 숨은 글자가 아니라 **보이는 문단**이라 거짓이었다 ([R115-2])
        if data.strip():
            self._after_link = False
            # 링크 **밖** 글자가 이 블록에 담겼으면 산문이다. `_in_title`·`_skip_depth`
            # 면 부모가 `text_parts` 에 **안 담았으므로** 둘을 함께 본다 — 제목·스크립트
            # 글자로 깃발이 서면 그 뒤 내비가 안 끊긴다.
            # **「담겼나」가 아니라 「뜻 있는 글자가 담겼나」다** — 리뷰 116 이 둘을
            # 실측으로 갈랐다([R116-1]·[R116-2]): ① 불릿 하나(`<li>· <a>…</a>×8`)가
            # 앞에 있으면 내비가 한 블록으로 뭉쳐 「링크 수의 합」이 본문을 **8:1 로**
            # 이긴다 — 계획 115 가 막으려던 그 모양이 되살아난다 ② `\x00`·ANSI 같은
            # 비가시 문자는 `_CONTROL` 이 출력에서 지우므로 **결과 텍스트에 흔적도
            # 없이** 분할만 바꾼다(크롤 HTML 은 신뢰 경계 밖이다 — 이 파일 머리가
            # 선언한 그 글자다). 그래서 `str.isalnum()` 으로 **낱말 글자**를 요구한다 —
            # 유니코드라 한글·한자·키릴이 다 들고, 불릿·`|`·제어문자는 안 든다.
            # `any` 는 첫 글자에서 끊어 비용이 `data.strip()` 과 같은 자리다
            if (not self._in_title and not self._skip_depth
                    and not (self._els and self._els[-1][2])
                    and any(ch.isalnum() for ch in data)):
                self._prose = True

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
    # 예외 **넷** — 앞의 둘은 **깨진 입력에서만** 갈리고 정상 HTML 에서는 같다.
    # 넷째(인접 링크 경계)는 계획 115 가 만들었고 `test_adjacent_links_are_the
    # _fourth_exception_to_the_join_invariant` 가 못박는다 — 리뷰 116 [R116-4] 가
    # 이 수가 셋에 멈춰 있던 것을 잡았다. 계획 116 이 **위반 횟수는 줄였고**
    # (산문 앞 케이스는 이제 불변식을 지킨다) **계획 118 이 산문 뒤 케이스에서 또**
    # **줄였다** — 그래도 예외 자체는 그대로 있다(내비는 여전히 끊는다).
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
