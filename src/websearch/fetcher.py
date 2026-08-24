"""URL 하나를 받아 HTML 을 가져온다. 타임아웃 10s, 재시도 2회, text/html 만."""
import urllib.error
import urllib.request
from typing import NamedTuple, Optional

from websearch.robots import USER_AGENT

TIMEOUT = 10
RETRIES = 2
MAX_BYTES = 2_000_000  # ponytail: 페이지 상한 2MB 고정, 대형 문서가 필요해지면 조정


class FetchResult(NamedTuple):
    status: int  # 0 = 네트워크 실패·잘못된 URL
    html: Optional[str]
    url: Optional[str] = None  # 리다이렉트 후 최종 URL — 저장 키·링크 base 로 쓴다


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    except ValueError:  # 스킴 없음 등 — CLI 시드는 신뢰 경계다
        return FetchResult(0, None, None)
    for attempt in range(1 + RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                final_url = resp.geturl()
                ctype = resp.headers.get("Content-Type", "")
                if not ctype.startswith("text/html"):
                    return FetchResult(resp.status, None, final_url)
                charset = resp.headers.get_content_charset() or "utf-8"
                body = resp.read(MAX_BYTES)
                try:
                    text = body.decode(charset, errors="replace")
                except LookupError:  # 선언된 charset 을 모름 — utf-8 로 폴백
                    text = body.decode("utf-8", errors="replace")
                return FetchResult(resp.status, text, final_url)
        except urllib.error.HTTPError as e:
            return FetchResult(e.code, None, url)  # 확정 응답 — 재시도 무의미
        except (urllib.error.URLError, OSError):
            continue  # 타임아웃·연결 실패 — 재시도
    return FetchResult(0, None, None)
