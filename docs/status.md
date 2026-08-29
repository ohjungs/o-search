---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 154
updated: 2026-08-29
ctx: 30
night_iterations: 37
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 33 `clock-injection` 을 정식 경로로 열었다.** 반복 152 의 `탐색 막힘` 을
사람이 (c) 중 하나를 골라 해소한 것이다 — 그 반복의 "사람이 정해야 할 것 2번" 이 곧
이 계획이다. `src` **0줄** · 열린 계획 **1** · 보류 패치 0 · RED 0.
단위 **431건 OK** (2026-08-29 20:2x 실행 확인). 작업 트리 깨끗.

브랜치 `loop/clock-injection`, 기점 **`de28dfb`**(`loop/readme-perf-audit`).
`main` 은 `f888518` 그대로 — 건드리지 않았다.

## 설계 완료 — `docs/design_clock-injection.md`

**대안 B(정공법)를 골랐다: `sleep` 을 `now` 옆에 기본값 있는 인자로 추가한다.**

```python
def _fetch_one(url, robots, now, floor, sleep=time.sleep): ...
def crawl(seeds, max_pages, db_path="data/crawl.db", robots_cache=None,
          now=time.monotonic, workers=WORKERS, deadline=None, sleep=time.sleep): ...
```

`now` 가 이미 그 모양이라 **새 구조가 아니라 빠져 있던 짝을 채우는 것**이다
(사다리 2번). 아무것도 안 넘기면 오늘 동작 그대로 — 기본값이 곧 꺼진 플래그다.
버린 둘: **A(테스트 전용 가짜 시계)** 는 중복만 줄이고 막힌 것을 그대로 두며,
**C(시계 객체)** 는 `now=` 쓰는 19곳을 전부 고치게 만드는 추측성 추상화다.

**설계 중 잰 것이 선택을 갈랐다 — 지금의 몽키패치는 사정거리가 프로세스 전역이다.**
`mock.patch("websearch.crawl.time.sleep")` 의 `time` 은 공유된 stdlib 모듈 객체라,
그 10개 테스트가 도는 동안 **모든 모듈·모든 스레드의 `time.sleep` 이 가짜**다(실측 확인).
`crawl` 은 워커를 띄우므로 그 안의 누구든 `time.sleep` 을 쓰기 시작하면 가짜 시계가
조용히 흘러 **간격 단언이 거짓이 된다.** 컨셉 갈림길 1순위가 크롤 윤리이고
도메인 1초 간격은 "어기면 RED" 인 전제 조건인데, 그것을 재는 장치가 그 상태였다.

## 다음에 할 일 — 개발 스텝 1 (TDD)

`docs/design_clock-injection.md` 의 **「계약」 6개를 먼저 읽는다.** 특히:
① 인자는 **뒤에** 붙인다(위치 인자 순서를 바꾸면 `_fetch_one` 을 직접 부르는 테스트
7곳이 조용히 어긋난다) · ② 두 대기 자리가 **같은 하나**를 쓴다 · ③ 규약은
`time.sleep` 과 동일(초 하나, 반환값 안 봄) · ⑥ **간격 기대값을 고치면 안 된다.**

스텝 1 = `tests/test_crawl.py` 에 실패 테스트 2건을 쓰고 **빨간불을 눈으로 확인**한다
(`dev.md` 0절). ① `sleep=fake` 를 넘기면 `fake` 가 불리고 전역 `time.sleep` 은
안 불린다 ② 안 넘기면 기본값이 `time.sleep` 이다.

## 계획 33 요약 (상세는 `docs/plan_clock-injection.md`)

- **문제**: 시각 읽기는 **인자**(`now`), 잠들기는 **모듈 전역**(`time.sleep`)이다.
  그 비대칭 때문에 `tests/test_crawl.py` 가 `websearch.crawl.time.sleep` 을
  **10곳**에서 몽키패치한다. 이 저장소가 크롤 간격을 초 단위로 단언하는 근거가 전부 거기다.
- **막고 있는 것**: 워커까지 Ctrl-C 를 넣으려면 `crawl.py:74` 가 `Event.wait` 가 돼야
  하는데 그러면 10곳이 한꺼번에 눈이 먼다. `digest.md:156` 이 우회로("`stop` 이 `None`
  이면 `time.sleep`")를 이미 검토하고 버렸다 — 테스트 경로와 제품 경로가 갈린다.
- **실측 정정**: digest 는 **9곳**이라고 적어 뒀지만 실제로 **10곳**이다
  (65·622·672·742·787·843·948·1023·1096·1325, 전부 `tests/test_crawl.py`. `e2e/` 는 0곳).
  계획 종료 시 `digest.md:156` 을 고친다.
- **스텝 5개**, 전부 일렬 의존. 완료 기준의 핵심 두 개:
  `grep -c 'crawl\.time\.sleep' tests/test_crawl.py` = **0** ·
  **기존 간격 기대값(`[1.0]`·`[5.0]`·`[1.0, 1.0]`)을 하나도 안 고친다.**
  기대값을 고쳐야 통과한다면 이음매가 틀린 것이니 설계로 되돌아간다.
- **e2e 는 "달라진 게 없다" 를 증명하는 자리다** — 가짜 시계가 초록인데 진짜 대기가
  사라지는 것이 유일한 실제 위험이고, 그것은 서버 시각을 재는 `crawl_delay_e2e.py` ·
  `perf_crawl.py` · `deadline_e2e.py` 만 볼 수 있다.

## 아직 남은 후보 (반복 152 의 분류 — (c) 첫 항목만 빠졌다)

**(a) 사람 승인 대기 — 무인 모드가 손대지 않는다**
`[8]` indexer 증분이 갱신을 반영 안 함(**스키마 변경**) · `[high]` `store.has` 가 상태
불문 스킵 = 재크롤 정책(**사람 판단**) · URL userinfo 가 `pages.url` PK 이자 검색 결과에
렌더됨(**보안 경계**) · `[5]` `X-Robots-Tag` http-equiv(**스키마**) · `loop/*` 병합 여부.

**(b) 도달 불가 — 고치면 오히려 정상값을 거절한다**
`[4]` `int_max_str_digits`(파이썬 3.9.6, 유지 판단 완료) · `[4]` `quality_eval` 의
`limit=100` 절단(실물 최대 28건) · `[4]` `fixture_defects` 가 ko·en 만 셈(코퍼스 동결이라
`ja` 질의가 생길 수 없다). 셋 다 **지금 짜면 죽은 코드**다.

**(c) 정식 계획 크기 — 설계 트리거에 걸린다**
~~`[6]` 가짜 시계 이음매~~ → **계획 33 으로 열렸다.** 남은 둘:
`[4]` 간격 시계가 발신이 아니라 pop 시각에서 시작 · `[7]` 요청 사이 색인 변경 시
OFFSET 페이지네이션 드리프트. 둘 다 40줄을 넘고 대안이 갈려 **야간 자동 적용 밖**이다.

## 사람이 정해야 할 것

1. **브랜치 병합** — `loop/readme-perf-audit`(푸시 완료)과 이제 `loop/clock-injection`
   을 `main` 에 남길지. 무인 모드는 `main` 에 커밋하지 않는다.
2. **(a) 의 스키마·보안 건**을 열지 — 열면 무인 금지가 풀린다.

## 미결

`data/crawl.db` 는 URL 을 `pages.url` PK 로 쓴다 · CI 없음 · `docs/specs/` 는 동결이다.
