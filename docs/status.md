---
signal: GREEN
plan: null
phase: 계획
step: -
attempt: 0
iteration: 146
night_iterations: 29
night_red: 0
night_retries: 0
updated: 2026-08-29 22:40 (반복 146 · 29 seed-scheme-guard 짧은 경로 DONE)
ctx: 71% / 200k
stopped: -
rules: 635d16c
mode: night (지시받은 것만 실행 · 다 하면 정지)
---

# 현재 상태

**28 `readme-commands` · 29 `seed-scheme-guard` DONE**(둘 다 짧은 경로).
열린 계획 없음 · 보류 패치 0건. 단위 **428건 OK** · e2e **17종 전부 rc=0**.
브랜치 `loop/readme-commands`(기점 `main` `8224207`) 병합은 사용자 판단이다.

**지시받은 세 스텝을 다 했다.** 새 계획을 찾지 않고 여기서 정지한다(무인 모드 규약).

**설계는 둘 다 건너뛰었다** — 새 모듈 없음 · 파일 2개 · 데이터 구조 무관 ·
되돌리기 쉬움. 29 는 보안에 **닿지만 넓히는 쪽이 아니라 좁히는 쪽**이다
(`file://`·`javascript:` 시드가 이제 안 들어간다). 24·26·27 과 같은 부류라 짧게 썼다.

집안일: `history_current.md` **284줄**(상한 300) — **다음 스텝은 회전 먼저** 한다.
25~29 를 `history_009.md` 로 빼면 된다.

## 반복 145 — 28 `readme-commands`

**내가 저지른 오류를 되돌렸다.** README 첫 명령 세 줄이 `python -m websearch.cli ...`
였는데 그 모듈은 25 리뷰가 `flags.py` 로 개명해 없다. **`flags.py` docstring 이 그
사실을 이미 적어 두고도 README 는 안 고쳐져 있었다** — 알고 있다는 기록은 고쳐졌다는
뜻이 아니다.

로컬 `http.server` 로 crawl→indexer→serve 를 끝까지 돌려 다시 썼다(외부 네트워크 안 침).
곁가지 둘: `python` 은 이 환경에 없고, `PYTHONPATH=src` 가 빠져 있었다 — README 의
`unittest` 줄도 같은 두 오류였다.

깨진 것이 코드가 아니라 **코드와 문서 사이**라 소스만 보는 테스트로는 안 잡힌다.
`tests/test_readme.py` 가 README 를 입력으로 읽어 `find_spec` 으로 본다. 변이 3종 잡힘.

## 반복 146 — 29 `seed-scheme-guard`

`crawl example.com --max 1` 이 `unknown url type` 을 stderr 에 남기고 rc **0**.
**실측이 앞 세션 권고("0페이지면 rc 1")를 갈랐고 실측을 따랐다** — `nonexistent.invalid`
는 robots 를 못 받아 차단 처리되어 0페이지 rc 0 인데, 그 갈래를 택하면 **robots 가
정당하게 막은 사이트가 오류가 된다**. 크롤 윤리를 오작동으로 보고하는 쪽이라 버렸다.

골라 든 것은 **시드 스킴 화이트리스트(rc 2)**. `links.py:30` 이 발견된 링크에 이미
거는 조건이라 새 계약이 아니라 **있는 계약의 구멍**이었다. 경계는 양쪽에서 고정했다 —
`https://nope.com/` 은 404 로 0페이지지만 거절이 아니다(rc 0).

**변이 M2 가 형제 구멍을 냈다**: `crawl --max 1` 은 플래그가 `len(argv) < 2` 를 채워
usage 를 통과하고 시드 0건으로 rc 0 이었다. 같은 자리에서 함께 막았다. 변이 6종 잡힘.

## 다음 계획 후보 (근거는 `digest.md`)

`[8]` **변이가 실제로 심어졌는지 먼저 단언한다**(이번에 BSD sed 가 거짓 초록을 냈다 —
룰 쪽 관찰이라 코드 계획은 아니다) · `[7]` 살아남은 변이가 등가인지 실측한다 ·
`[6]` README 성능 표의 기준선 숫자가 지금 `perf_*` 출력과 맞는지 안 쟀다 ·
`[4]` `--port 0` 단위 무커버 · `[4]` `int_max_str_digits`(3.9.6 이라 도달 불가, 유지 판단) ·
`[6]` `serve.do_GET` 넓은 `try`(확신 낮음).

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL `pages.url` PK ·
CI · `docs/specs/` 채우기.
