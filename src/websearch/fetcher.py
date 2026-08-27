"""URL 하나를 받아 HTML 을 가져온다. 타임아웃 10s, 재시도 2회, text/html 만."""
import http.client
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


def fetch(url, before_send=None, retries=RETRIES):
    """`before_send` 는 **시도 하나하나 앞에서** 불린다 — 재시도 앞에서도 불린다.

    도메인 간격을 지키며 재우는 것도, 발신 시각을 재는 것도 **호출부의 몫**이다.
    `fetcher` 는 간격이라는 개념을 모른다 (docs/design_crawl-politeness.md 2-1절).
    훅이 뒤가 아니라 앞에서 불려야 호출부가 재는 것이 응답이 아니라 **발신**이 된다.

    `retries=0` 은 "간격을 지킬 수 없는 도메인이니 다시 보내지 않는다" 는 뜻이다(설계 2-4절).
    `Request()` 생성이 실패하면 훅은 한 번도 안 불린다 — 나가지도 않은 요청으로
    도메인 시계를 걸면 안 된다.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    except ValueError:  # 스킴 없음 등 — CLI 시드는 신뢰 경계다
        return FetchResult(0, None, None)
    for attempt in range(1 + retries):
        if before_send is not None:
            before_send()
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
        except (UnicodeError, http.client.InvalidURL):
            # URL 자체가 틀렸다(비ASCII·공백·제어문자·숫자 아닌 포트) — 몇 번 보내도 같다
            return FetchResult(0, None, None)
        except (urllib.error.URLError, OSError, http.client.HTTPException):
            continue  # 타임아웃·연결 실패·응답 파손 — 재시도
    return FetchResult(0, None, None)
