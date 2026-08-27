---
signal: GREEN
plan: url-normalize
mode: night
phase: 테스트
step: 3
attempt: 0
iteration: 114
night_iterations: 25
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 114 · 018 스텝 2/5)
ctx: 71% / 200k
rules: 1411a37
---

# 현재 상태

**계획 018 `url-normalize` 착수.** 브랜치 `loop/url-normalize` (기점 `e08bc8f`).
계획서는 `docs/plan_url-normalize.md`. 출처는 `docs/digest.md ## 다음 계획 후보` `[5]`.

**017 이 닫은 것은 "어느 서버인가" 였고 URL 자체는 안 닫혔다.** 간격·in-flight·
`Crawl-delay` 는 `urls.domain_key` 로 한 칸이 됐지만 `Frontier._seen` 과
`store.pages.url` 은 여전히 문자열 그대로를 열쇠로 쓴다 — `http://a.test/p` ·
`http://A.test/p` · `http://a.test:80/p` 가 **각각 수집·저장·색인된다.**
윤리 위반은 아니지만 크롤 예산과 색인 크기가 표기 수만큼 낭비된다.

답은 **RFC 3986 6.2.2 가 인정하는 것만** URL 전체에 거는 것이다: 스킴/호스트 소문자 ·
스킴별 기본 포트 제거 · 빈 경로 `/` · 퍼센트 3연 hex 대문자. 앞의 셋은
`urls.domain_key` 가 이미 하므로 새로 쓰지 않고 **그것을 부른다**(단 `userinfo@` 는
도로 붙인다 — 뗀 채 재조립하면 요청 내용이 바뀐다).

**`urls.to_ascii` 는 안 건드린다.** "ASCII 는 한 글자도 안 바꾼다" 는 멱등성과
이중 인코딩(`%`→`%25`) 방지를 한 규칙으로 사는 계약이고 007 의 회귀 위험이 전부
거기 있다. 새 `urls.normalize` 가 그 위에 얹히고, 옛 계약을 재는 기존 테스트 4건이
**안 바뀐 채로** 회귀 탐지기로 남는다 (계획서 6절 대안 B 기각).

**설계 phase 는 건너뛴다 — 사유.** 트리거 중 하나(파일 3개: `urls.py`·`links.py`·
`crawl.py`)에 걸리지만 뒤의 둘은 **호출 한 단어 교체**이고, 갈림길(정규화를 어디서
하나 · 무엇까지 정규화하나)은 계획서 2·6절에서 근거와 함께 이미 닫혔다. 별도
문서를 만들면 6절 복사가 된다. 새 모듈 없음 · 데이터 구조 변경 없음 · 공개 계약
변경 없음(`to_ascii` 는 그대로). 014~017 도 같은 판단으로 설계를 안 만들었다.

## 다음에 할 일 — 스텝 3 (테스트 phase)

`rules/test.md` — 새로 쓰는 곳이 아니라 **빠뜨린 것을 찾고 전체를 돌리는** 곳.
계획서 5절의 변이 3종을 여기서 돌린다.

- 이미 한 것: **스텝 1·2 완료.** `urls.normalize` 신설 + 호출부 셋 배선
  (`links.py:33` · `crawl.py:91` 시드 · `crawl.py:175` 리다이렉트 최종 URL).
  **381건 OK**(전 354 → 368 → 381). 둘 다 커밋함
- **스텝 2 가 017 의 테스트 하나와 e2e 하나를 깼다 — 정상이고 기록이 남았다.**
  018 이 대소문자·기본 포트 표기를 **URL 이 태어나는 자리에서** 접으므로 그 표기는
  크롤 루프까지 오지 않는다. 017 이 재던 축이 사라진 것이다. 둘 다 **조용히
  통과하지 않고 "재려던 상황이 없다" 로 실패했다** — 긍정 짝을 심어 둔 값이다
  - `tests/test_crawl.py::test_one_server_paces_itself_across_spellings` 는
    **스킴 축**(`http`/`https` — 018 이 안 접는 유일한 살아 있는 축)으로 다시 썼다.
    017 의 접기는 없어진 게 아니라 **두 번째 방어선**이고 `TestDomainKey` 가 단위로 잰다
  - **`e2e/domain_key_e2e.py` 는 아직 안 고쳤다** — 스텝 5 에서 같이 고친다.
    실측 실패 문구: `세 표기가 다 도착하지 않았다: ['a.test']`
- 완료 기준: 갭 탐색 결과를 `history_current.md` 에 적고 전체 스위트 + 회귀 e2e
  (`crawl_delay`·`crawl_politeness`·`retry_interval`·`non_ascii`)를 돌린다

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합 ·
옛 표기로 저장된 기존 행의 마이그레이션(데이터 변경).
