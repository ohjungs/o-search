"""robots.txt 확인. 응답 실패(5xx 등)는 보수적으로 차단, 404는 전체 허용(관례)."""
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = "websearchbot/0.1"


class RobotsCache:
    def __init__(self):
        self._parsers = {}  # base -> RobotFileParser | None(차단)

    def allowed(self, url):
        base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
        if base not in self._parsers:
            self._parsers[base] = self._load(base)
        parser = self._parsers[base]
        if parser is None:
            return False
        return parser.can_fetch(USER_AGENT, url)

    def _load(self, base):
        status, body = self._fetch_robots(base)
        if status == 200:
            parser = urllib.robotparser.RobotFileParser()
            parser.parse(body.splitlines())
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
