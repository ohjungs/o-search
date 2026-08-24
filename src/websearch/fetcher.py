"""URL 하나를 받아 HTML 을 가져온다. 타임아웃 10s, 재시도 2회, text/html 만."""
import urllib.error
import urllib.request
from typing import NamedTuple, Optional

from websearch.robots import USER_AGENT

TIMEOUT = 10
RETRIES = 2


class FetchResult(NamedTuple):
    status: int  # 0 = 네트워크 실패
    html: Optional[str]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1 + RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                ctype = resp.headers.get("Content-Type", "") if hasattr(resp.headers, "get") else ""
                if not ctype.startswith("text/html"):
                    return FetchResult(resp.status, None)
                return FetchResult(resp.status, resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            return FetchResult(e.code, None)  # 확정 응답 — 재시도 무의미
        except (urllib.error.URLError, OSError):
            continue  # 타임아웃·연결 실패 — 재시도
    return FetchResult(0, None)
