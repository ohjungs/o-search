# e2e 결과: non-ascii-url — 통과 (2026-08-26 야간)

명령: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 e2e/non_ascii_e2e.py` (이 계획에서 신설, 2.6s)

로컬 HTTP 서버에 시드 2개(`/` + 서로게이트가 든 URL)로 진짜 `crawl.crawl()` 을 자식
프로세스에서 돌린다. 서버는 `/` 에서 같은 한글 페이지를 **두 표기**(`href="/가.html"` ·
`href="/%EA%B0%80.html"`)로 걸고 ASCII 페이지 하나를 더 건다.

| 시나리오 (plan_history_007.md `## e2e 시나리오`) | 결과 |
|---|---|
| 1. 한글 경로 링크를 따라가는 크롤 → 저장되고 **크롤이 중단되지 않는다** | 통과 — `수집 3 페이지` · exit 0 · `pages` 에 `http://127.0.0.1:PORT/%EA%B0%80.html` 1행(status 200, html 있음) |
| 2. 한글 표기·퍼센트 표기 두 링크 → `pages` **1행** | 통과 — 1행. 더해서 **서버가 받은 요청도 1건** |
| 3. 정규화로 못 살리는 시드(서로게이트)를 섞는다 → 그것만 건너뛰고 나머지 전부 수집 | 통과 — stderr `…\ud800.html: URL 로 읽을 수 없는 시드 — 건너뛴다`, 나머지 3페이지 전부 수집, exit 0 |

DB 에 비ASCII URL 이 한 건도 없다는 것(`u.isascii()`)과 서버 요청 집합이 정확히
`{/robots.txt, /, /%EA%B0%80.html, /ok.html}` 라는 것을 같이 본다 — 건너뛴 시드가
네트워크까지 새어 나가지 않았다는 증거다.

## 예상과 달랐던 것

**시나리오 2 는 DB 행 수만으로는 덜 잰다.** `pages` 1행은 `store.has()` 가 뒤에서
막아줘도 성립한다 — 그러면 서버는 같은 페이지를 두 번 맞는다. 정규화가 `seen` **앞**에
있다는 계약(`links.py:30`)은 **서버 수신 1건**으로만 확인된다. 그래서 검증을 하나 더 걸었다.

**시나리오 3 의 실패 모드가 예상보다 앞이었다.** 시드 정규화를 빼면(변이 A) 크롤이
`fetcher.fetch` 가 아니라 그 **전에** 죽는다 — `store.has(url)` 이 서로게이트를 SQLite
파라미터로 넘기면서 `UnicodeEncodeError` 가 난다. `fetcher` 의 방어만으로는 이 시드를
막을 수 없다는 뜻이고, `crawl.py:19` 의 시드 정규화가 실제로 짐을 지고 있다.

## 변이 검사 — 잡는 것과 도는 것은 다르다

네 곳을 변이시켜 돌렸다. **두 개는 잡고 두 개는 못 잡는다.** 못 잡는 쪽을 그대로 적는다.

| 변이 | 결과 |
|---|---|
| A `crawl.py:19` → `normalized = seed` (시드 정규화 제거) | **잡는다** exit 1 — `store.has` 에서 `UnicodeEncodeError` 로 크롤이 죽는다 (시나리오 3) |
| B `links.py:30` → `absolute = absolute` (링크 정규화 제거) | **잡는다** exit 1 — `수집 2 페이지` (한글 페이지가 통째로 빠진다, 시나리오 1·2) |
| C `crawl.py:44` → `page_url = result.url or url` (저장 키 정규화 제거) | **못 잡는다** — 통과 |
| D `fetcher.py:41` → `except (UnicodeError,)` (`InvalidURL` 제외) | **못 잡는다** — 통과 |

C·D 는 **이 시나리오가 못 재는 것이 아니라 이 시나리오가 닿지 않는 경로**다.

- **C**: `crawl.py:44` 는 리다이렉트 뒤 최종 URL(`resp.geturl()`)을 다시 정규화한다.
  프런티어에서 나온 `url` 은 이미 ASCII 고 이 서버는 리다이렉트를 하지 않으니, 여기는
  **`Location:` 이 비ASCII 로 오는 서버**에서만 발화한다. 재려면 서버에 302 를 추가해야 한다
- **D**: `links.py` 가 앞에서 전부 ASCII 로 바꾸므로 비ASCII URL 은 `fetch` 까지 오지
  않는다. `fetcher` 의 `except` 는 **다중 방어**지 이 경로의 1차 방어가 아니다.
  단위 테스트(`tests/test_fetcher.py`)가 직접 `fetch()` 를 불러 잡는 몫이다

둘 다 e2e 를 늘려 덮을 자리가 아니라고 봤다 — 302 시나리오는 이 계획의
`## 하지 않을 것`(URL 정규화 일반) 과 붙어 있고, D 는 단위 테스트가 이미 담당한다.
**다음 반복이 판단하도록 적어만 둔다.**

## 소스 버그

없다. `src/` 를 0줄 건드렸다 (변이는 전부 `git checkout -- src/` 로 되돌렸고,
`git status` 로 깨끗함을 확인했다).

## e2e 앞 관문

- 단위 테스트 **199/199 OK** (`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover tests`, 1.59s)
- 기존 e2e 5개 + 품질·성능 회귀 없음, 전부 종료 0:
  crawl(수집 15·차단 0·최소 간격 1.000s) / crawl-delay(6페이지·최소 2.00s·하한 1.00s) /
  indexer(3문서·증분 0) / noindex(4수집 2색인) / search-api(15문서·페이지네이션·400/404/501) /
  quality-eval(ko 85%·en 90%, 합격선 80% 통과)
- 린트·타입체크 없음(`project.md`). **신규 의존성 0** — stdlib 만
  (`http.server`·`sqlite3`·`subprocess`·`tempfile`·`threading`)
- **전체 테스트 명령과 겹치지 않는다** — `unittest discover tests` 는 `tests/` 만 훑고
  새 파일은 `e2e/` 에 있다. `rules/e2e.md` 1절의 "1회만" 이 지켜진다
- 만든 파일 2개(`rules/e2e.md` 5절 예외 범위): `e2e/non_ascii_e2e.py` · 이 문서

## 품질 기준 대조 (docs/specs/concept.md)

- **크롤 윤리(1순위)**: `e2e/crawl_delay_e2e.py` 통과. 이 e2e 자체도 도메인 1초 간격을
  그대로 받는다 — 3페이지에 2.6s 걸리는 이유가 그것이다(정상)
- **성능**: `e2e/perf_search.py` p95 **6.76ms** (기준선 6.71ms 와 같은 자리, 예산 300ms 의 2.3%).
  이 계획은 크롤 경로만 건드렸으니 예상대로지만 확인은 했다
- **검색 품질**: ko 85% · en 90% — 기준선 그대로, 회귀 없음
- **경량(JS 50KB)·디자인**: 측정 명령이 `없음` 이다 → **검증되지 않았다.** 통과가 아니다
