---
signal: GREEN
plan: null
phase: 계획
step: -
attempt: 0
iteration: 148
night_iterations: 31
night_red: 0
night_retries: 0
updated: 2026-08-29 23:55 (반복 148 · 30 readme-perf-audit 짧은 경로 DONE)
ctx: 40% / 200k
stopped: -
rules: 635d16c
mode: night (지시받은 것만 실행 · 다 하면 정지)
---

# 현재 상태

**30 `readme-perf-audit` DONE**(짧은 경로). 열린 계획 없음 · 보류 패치 0건.
단위 **429건 OK** · e2e **17종 전부 rc=0**.
브랜치 `loop/readme-perf-audit`(기점 `main` `4d8adac`) — 병합은 사용자 판단이다.

**설계는 건너뛰었다** — 새 모듈 없음 · 파일 2개(`README.md`·`tests/test_readme.py`) ·
데이터 구조 무관 · 되돌리기 쉬움 · 보안 무관.

## 반복 148 — 30 `readme-perf-audit` (짧은 경로)

- 무엇: README `## 품질 기준` 표 다섯 줄을 표가 지목한 명령으로 **직접 실측**했고,
  같은 문서의 `## 검증` 숫자가 낡은 것을 `tests/test_readme.py` 로 막았다.
  근거: `status.md` 다음 계획 후보 `[6]` ("README 성능 표 기준선을 안 쟀다", 최우선).
- 왜: 문서가 코드를 앞질러 가는 것이 이 저장소가 이틀 새 두 번 밟은 자리다
  (없는 `websearch.cli` 안내 · `단위 419건` 표기가 428 위에서 초록).
- 완료 기준: 표 다섯 줄이 전부 실측으로 참임을 보이고, 낡은 숫자는 테스트가 죽는다.
- 이미 한 것: 전부. 아래가 실측값이다.

**표 다섯 줄은 전부 참이었다** — 고칠 것이 없었다(2026-08-29 실측, 로컬만·외부 무접속):

| README 기준 | 측정 명령 | 실측 | 여유 |
|---|---|---|---|
| recall@10 ≥ 80% | `quality_eval.py` | ko 20/20 · en 19/20 = **97.5%** | +17.5%p |
| p95 ≤ 300ms | `perf_search.py` | **9.16ms** (3000문서·1000요청) | 예산의 3.1% |
| ≥ 5 docs/s | `perf_crawl.py` | **10.22/s** (열림) · 10.23/s (차단) | 2배 |
| JS ≤ 50KB gzip | `design_check.py` | **0 B** (인라인 0자·외부 0개) | 서버 렌더 |
| 명암비 ≥ 4.5:1 | 〃 | 최저 **4.87:1** (`--fg-url` 라이트) | +0.37 |

**표는 참인데 같은 README 의 다른 숫자는 거짓이었다** — `## 검증` 이 `단위 419건`
이라고 적은 자리의 실제는 **428건**. 419 는 28(`readme-commands`)이 README 를 고칠 때의
값이고 그날 밤 29 가 6건을 더했다. **손으로 적는 숫자는 고친 그날부터 낡는다.**
28 이 만든 `tests/test_readme.py`(문서를 입력으로 읽는 유일한 검사)에 단언 하나를 더해
README 가 안내한 그 명령으로 직접 센다 — `defaultTestLoader.discover` 와 `e2e/*.py` glob.
추상도 새 파일도 안 늘렸다(사다리 2칸: 이미 있는 자리에 얹기).

**변이 3종 전부 잡힘**: `419`(원래 값) → FAILED · `e2e 17종`→`16종` → FAILED ·
`# 단위 429건` 주석 통째 삭제 → FAILED. **BSD sed 를 안 썼다**(`digest [8]`) —
치환은 파이썬으로 하고 원문 복원까지 스크립트가 단언한다.

**곁가지는 안 건드렸다.** 표에 실측값 열을 README 에 박는 것은 하지 않았다 —
그 열에는 지금 이 숫자들을 지킬 검사가 없어서, 막 고친 것과 같은 종류의 낡을 숫자를
하나 더 만드는 일이다. 기준선은 `project.md` 와 이 파일이 갖는다.

## 다음 계획 후보 (근거는 `digest.md`)

`[4]` `--port 0`(임의 포트) 단위 무커버 — e2e 넷만 덮는다 ·
`[8]` **변이가 실제로 심어졌는지 먼저 단언한다**(BSD sed 거짓 초록 — 룰 쪽) ·
`[7]` 살아남은 변이가 등가인지 실측 · `[4]` `int_max_str_digits`
(3.9.6 이라 도달 불가, 유지 판단) · `[6]` `serve.do_GET` 넓은 `try`(확신 낮음).

**집안일 예약 아님, 실측**: `history_current.md` 가 이 항목으로 300줄을 넘으면
`docs.md` 3절 방아쇠가 켜진다 — 그때 25~30 을 `history_009.md` 로 뺀다.

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL `pages.url` PK ·
CI · `docs/specs/` 채우기.
