---
signal: GREEN
plan: null
phase: 계획
step: -
attempt: 0
iteration: 143
night_iterations: 26
night_red: 0
night_retries: 0
updated: 2026-08-29 20:50 (반복 143 · 26 crawl-max-guard 짧은 경로 DONE)
ctx: 71% / 200k
stopped: -
rules: 1411a37
mode: night (지시받은 것만 실행 · 다 하면 정지)
---

# 현재 상태

**26 `crawl-max-guard` DONE**(짧은 경로). 열린 계획 없음 · 보류 패치 0건.
단위 **416건 OK** · e2e **17종 전부 rc=0**.
브랜치 `loop/crawl-max-guard`(기점 `d2337fb`) — 병합은 사용자 판단이다.

## 이번 반복 (143) — `loop/crawl-max-guard`

**`--max 0` 의 가드 비대칭을 닫았다.** 앞 세션이 판단 대기로 남긴 `digest.md` 후보 `[5]`.
실측: `--max 0` → 요청 **0건** · `수집 0 페이지` · **rc 0**. `--workers 0`·`--deadline 0`
은 진작 rc 2 였다. **rc 2 로 거절하는 쪽으로 정했다** — 가르는 것은 대칭이 아니라
결과의 모양이다. `수집 0 페이지` + rc 0 은 **크롤이 아무것도 못 찾은 것과 구별되지
않는 성공**이고, 이 저장소가 두 번 닫은 실패 유형이다(21 · 25).

**0 을 일괄 금지하지 않았다** — `serve --port 0` 은 "임의 포트" 라는 뜻이 있어 그대로
받는다. 하한은 파서가 아니라 **플래그의 뜻**이 정하므로 `flags.number_flag` 는 범위를
여전히 안 본다(설계 019 결정 유지). 가드는 호출부 한 줄이다.

**설계를 건너뛴 사유**: 새 모듈 없음 · 파일 2개(`crawl.py` 가드 한 줄 + `flags.py`
독스트링) · 데이터 구조 무관 · 되돌리기 쉬움(한 줄) · 보안 무관. 계획 24
(`serve-port-guard`)와 같은 부류라 같은 경로를 썼다.

**변이 3종 전부 잡힘**(사본 · `PYTHONDONTWRITEBYTECODE=1` · 기준선 416 OK):
M1 하한 제거 · M2 하한 `< 0` · **M3 하한 `< 2`**. M3 는 **하한 자체를 재는 대조군**
(`--max 1` → `crawl(..., 1)`)이 있어서 잡혔다 — 기존 `--max=3` 단언은 못 본다.

## 집안일

`history_current.md` 293줄(상한 300)이라 **회전 먼저** 했다 — 계획 21~24 를
`history_008.md` 로 밀어내고 `digest.md ## 완료` 에 한 줄로 압축(293 → 176줄).

## 다음 계획 후보 (근거는 `digest.md`)

`[5]` **URL 뒤에 붙은 플래그가 시드로 샌다**(`--max 3` 뒤의 `--max 5` — 뽑기가
첫 것만 본다) · `[5]` **README 가 없는 `python -m websearch.cli` 를 안내한다**(25 는
직교 편집이라 안 고쳤다) · `[4]` `--port 0` 단위 무커버 · `[4]` `int_max_str_digits`
(3.9.6 이라 도달 불가) · `[6]` `serve.do_GET` 의 넓은 `try`.

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL userinfo 가 `pages.url` PK
이자 검색 결과에 렌더되는 것(보안 경계) · `recrawl`(`fetched_at` 스키마) ·
`X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합 · 의존성 추가·업그레이드 · CI 도입 ·
`docs/specs/` 쓰기 · git 사용자 이메일 설정 변경.
