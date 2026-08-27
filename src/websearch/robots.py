"""robots.txt 확인. 응답 실패(5xx 등)는 보수적으로 차단, 404는 전체 허용(관례)."""
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

from websearch import urls

USER_AGENT = "websearchbot/0.1"

# stdlib 은 정수 Crawl-delay 만 받는다(RobotFileParser 가 isdigit 으로 거른다).
# "Crawl-delay: 3.5" 를 조용히 버리면 기본 1초로 떨어져 **요청보다 빠르게** 때린다 —
# 컨셉 1순위인 크롤 윤리 위반이라, 그때만 아래 폴백이 본문을 직접 읽는다.
_NUMBER = re.compile(r"[0-9]*\.?[0-9]+")


def _seconds(value):
    """robots 의 값 문자열을 초로. 읽을 수 없으면 None.

    **느린 쪽으로만 틀린다**가 규칙이다: "1e3" 은 1000초지 1초가 아니고,
    "5s" 는 5초로 읽는다(1초로 떨어뜨리면 사이트 뜻보다 빨라진다).
    """
    try:
        seconds = float(value)
    except ValueError:
        found = _NUMBER.match(value)
        seconds = float(found.group()) if found else None
    return seconds if seconds is not None and seconds >= 0 else None


def _applicable_delay(body):
    """우리에게 적용되는 그룹의 Crawl-delay(초). 없으면 None.

    **남의 그룹 값을 집으면 안 된다** — 다른 봇에게 건 86400 을 우리 값으로 읽으면
    1.5초면 지킬 수 있는 사이트를 상한 초과로 통째로 버리게 된다(frontier.MAX_DELAY).
    우리 이름을 지목한 그룹이 있으면 그것만, 없으면 와일드카드(*)를 쓴다.
    """
    me = USER_AGENT.split("/")[0].lower()  # stdlib 과 같은 규칙 — 슬래시 앞까지 본다
    named, wildcard = [], []
    agents, in_body = [], False
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if in_body:  # 빈 줄이 아니라 "본문 뒤의 User-agent" 가 그룹 경계다
                agents, in_body = [], False
            agents.append(value.lower())
            continue
        in_body = True
        if key != "crawl-delay":
            continue
        seconds = _seconds(value)
        if seconds is None:
            continue
        if any(a and a != "*" and a in me for a in agents):
            named.append(seconds)
        elif "*" in agents:
            wildcard.append(seconds)
    group = named or wildcard
    return max(group) if group else None


def _base(url):
    """robots.txt 를 받아 둘 열쇠이자 그것을 받을 주소. **스킴별로 다른 문서다.**

    스킴도 호스트도 `urls` 의 **안 던지는** 파싱을 쓴다 — 여기서 날 `urlsplit` 을
    부르면 `http://[::1/x` 같은 링크 하나가 워커 예외 처리 경로(`crawl._store_result`
    의 `known_delay`)에서 **두 번째로** 던져 크롤 전체를 죽인다(백지 리뷰 지적).
    호스트 부분은 `urls.domain_key` 와 같은 자를 쓴다 — 대소문자만 다른 링크가
    같은 서버의 `robots.txt` 를 두 번 받게 하고(실측 2회), 그 두 번이 선언한
    간격을 지키지 않고 나간다.
    """
    return "%s://%s" % (urls.scheme_of(url), urls.domain_key(url))


class RobotsCache:
    def __init__(self):
        self._parsers = {}  # base -> RobotFileParser | None(차단)
        self._delays = {}   # base -> float(초). 지시가 없으면 키가 없다

    def allowed(self, url):
        parser = self._parser(url)
        if parser is None:
            return False
        try:
            return parser.can_fetch(USER_AGENT, url)
        except ValueError:
            # `can_fetch` 는 URL 을 **자기가 다시 파싱한다** — 닫히지 않은 IPv6
            # 리터럴이면 여기서 던진다. 우리가 열쇠를 안전하게 만든 것과 별개다.
            # 못 읽는 URL 은 **안 간다**: 허용 여부를 물을 수 없는 주소를 치는 것이
            # 예의 계약에서 더 나쁜 쪽이고, 예외를 올리면 크롤 전체가 죽는다
            return False

    def delay(self, url):
        """robots 가 요청한 도메인 간격(초). 지시가 없으면 None(호출부의 기본값을 쓴다).

        allowed() 와 **같은 캐시 한 번**을 쓴다 — robots.txt 를 두 번 받지 않는다.
        """
        self._parser(url)  # 아직 안 받았으면 여기서 받는다
        return self.known_delay(url)

    def known_delay(self, url):
        """**이미 받아 둔** robots 의 간격(초). 없으면 None.

        `delay()` 와 달리 **네트워크를 타지 않는다** — 메인 스레드가 불러도 되는 유일한
        조회다(동시화 계약 4: 메인 스레드는 네트워크를 안 한다). 워커가 `_load` 에서 쓰고
        메인이 여기서 읽지만, dict 의 단일 키 get/set 은 GIL 아래 원자적이라 락을 두지 않는다.

        **None 의 뜻은 둘이고 둘 다 호출부의 기본값이 답이다**: ① 아직 robots.txt 를
        못 읽었다 — 그러면 페이지 요청도 안 나갔다. ② 읽었는데 Crawl-delay 지시가 없다.
        "모르니까 느린 쪽" 이라며 큰 값을 지어내는 자리가 아니다.
        """
        return self._delays.get(_base(url))

    def _parser(self, url):
        base = _base(url)
        if base not in self._parsers:
            self._parsers[base] = self._load(base)
        return self._parsers[base]

    def _load(self, base):
        status, body = self._fetch_robots(base)
        if status == 200:
            parser = urllib.robotparser.RobotFileParser()
            parser.parse(body.splitlines())
            delay = parser.crawl_delay(USER_AGENT)
            if delay is None:
                delay = _applicable_delay(body)  # stdlib 이 버린 소수·지수 표기를 줍는다
            if delay is not None:
                self._delays[base] = float(delay)
            return parser
        if 400 <= status < 500:  # robots 없음 = 전체 허용
            parser = urllib.robotparser.RobotFileParser()
            parser.parse([])
            return parser
        return None  # 5xx·네트워크 실패 = 차단

    def _fetch_robots(self, base):
        req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except (urllib.error.URLError, OSError):
            return 599, ""
