"""robots.txt 확인. 응답 실패(5xx 등)는 보수적으로 차단, 404는 전체 허용(관례)."""
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = "websearchbot/0.1"

# stdlib 은 정수 Crawl-delay 만 받는다(RobotFileParser 가 isdigit 으로 거른다).
# "Crawl-delay: 3.5" 를 조용히 버리면 기본 1초로 떨어져 **요청보다 빠르게** 때린다 —
# 컨셉 1순위인 크롤 윤리 위반이라, 그때만 본문에서 직접 긁는다.
# 값의 앞부분 숫자만 본다("5s" → 5.0) — 규칙은 하나다, **느린 쪽으로만 틀린다.**
_DELAY_LINE = re.compile(r"^[ \t]*crawl-delay[ \t]*:[ \t]*([0-9]*\.?[0-9]+)", re.I | re.M)


def _base(url):
    return "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))


class RobotsCache:
    def __init__(self):
        self._parsers = {}  # base -> RobotFileParser | None(차단)
        self._delays = {}   # base -> float(초). 지시가 없으면 키가 없다

    def allowed(self, url):
        parser = self._parser(url)
        if parser is None:
            return False
        return parser.can_fetch(USER_AGENT, url)

    def delay(self, url):
        """robots 가 요청한 도메인 간격(초). 지시가 없으면 None(호출부의 기본값을 쓴다).

        allowed() 와 **같은 캐시 한 번**을 쓴다 — robots.txt 를 두 번 받지 않는다.
        """
        self._parser(url)  # 아직 안 받았으면 여기서 받는다
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
                # ponytail: UA 그룹을 구분하지 않는다 — 남의 그룹 값을 집어 더 느려질 수 있다.
                #           느린 쪽으로만 틀리는 오류라 허용한다. 실물에서 문제가 되면 그때 나눈다
                found = [float(m) for m in _DELAY_LINE.findall(body)]
                delay = max(found) if found else None
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
