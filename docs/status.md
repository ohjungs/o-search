---
signal: GREEN
plan: normalize-gaps
mode: night
phase: e2e
step: 4/4
attempt: 0
iteration: 121
night_iterations: 4
night_red: 0
night_retries: 0
updated: 2026-08-28 (반복 121 · 019 리뷰 3/4)
ctx: 67% / 200k
rules: 1411a37
---

# 현재 상태

**계획 019 `normalize-gaps` 스텝 3/4 리뷰 완료 — 다음은 스텝 4/4 e2e.**
브랜치 `loop/normalize-gaps` (기점 `33e531d` = 018 끝). 계획서 `docs/plan_normalize-gaps.md`.

**백지 리뷰가 019 자신이 만든 회귀 1건을 잡았다.** 지적 7건 중 4건 반영, 3건은 기록.

**반영 [자동수정]**
1. **`:0` 이 기본 포트로 합쳐졌다** — `lstrip("0")` 이 `"0"` 을 통째로 먹어 빈 포트가
   되고, 빈 포트는 기본 포트다. 실측 `domain_key('http://b.test:0/p')` 가
   **착수 전 `b.test:0` → 019 가 `b.test`**. `:0` 은 80 이 아니라 **요청이 다른 포트로
   나간다** — `normalize` 가 userinfo 를 안 떼는 것과 같은 이유로 틀렸다.
   `port.lstrip("0") or "0"` 로 닫았다
2. `isdigit()` 은 `٠٨٠`·`²` 에도 참이라 RFC 3.2.3 의 `DIGIT` 보다 넓다 →
   `port.isascii() and port.isdigit()`. **동작은 안 바뀐다**(변이 M7 이 아무것도 안
   죽인다 — 말과 코드를 맞춘 것이지 버그 수정이 아니다)
3. 테스트 공백 — `..` 가 **빈 세그먼트를 pop** 하는 경우가 두 계약("점만 접는다" /
   "빈 세그먼트는 그대로")이 부딪히는 유일한 입력인데 못 박혀 있지 않았다
4. `mark` 를 8줄 간격으로 두 뜻에 쓰던 것 → `sep`

**새 변이로 재확인.** M6(`or "0"` 없음) → `test_port_zero_is_not_the_default_port` 만
죽는다. M8(빈 세그먼트를 pop 대상에서 뺌) → `test_dots_pop_an_empty_segment_like_any_other`
만 죽는다. **388건 OK.**

**리뷰어의 독립 검증**: `_fold_dots` 를 RFC 5.2.4 레퍼런스와 세그먼트 전수 공간
3905개로 대조 — **불일치 0**, 멱등성 퍼징 실패 0, 정크 6만 건에 예외 0.

**기록만 (안 고침)**: `links.extract` 의 `urljoin` 이 RFC 보다 넓게 접어 231개 모양이
갈린다 → `digest.md ## 판단 필요` 새 `[4]`. 기존 DB 재키잉은 이미 아래 판단 필요 1번.

## 다음 스텝 — 4/4 e2e

`e2e/url_normalize_e2e.py` 에 축 추가(계획서 4절 시나리오 4개). 새 파일 안 만든다.

## 판단 필요` `[4]`·`[2]`).
같은 병이고 고치는 파일이 하나라 묶었다:

1. **점 세그먼트를 안 접는다** — `normalize('http://b.com/a/../p')` 가 그대로다(실측).
   절대 href 는 `urljoin` 이 안 접는다
2. **`:080` 을 안 접는다** — `domain_key` 가 `'080' != '80'` 문자열 비교라
   `b.com:080` 이 남는다(실측). 예의를 세는 칸이라 **간격 계약이 샌다**

**설계는 안 쓴다** — `design.md` 1절 트리거 0건(새 모듈 없음·시그니처 불변·저장 형태
불변·파일 2개). 접는 방법 셋은 *갈림길이 아니다*: `posixpath.normpath` 는 `/a//b`·`/a/b/`
까지 접어 **RFC 가 동치로 안 보는 것을 합치고**, `urljoin` 왕복은 빈 질의 `?` 를 삼킨다.
셋을 같은 입력에 돌린 실측 표가 계획서 2절에 있다.

## 다음 스텝 — 1/4 개발

`tests/test_urls.py` 에 기대 결과 6건을 **먼저 빨갛게** 넣고(`dev.md` 0절),
`src/websearch/urls.py` 에 `_fold_dots` 신설 + `normalize` 경로에만 배선 +
`domain_key` 에 `if port.isdigit(): port = port.lstrip("0")`.
`normalize` 독스트링의 "점 세그먼트는 안 접는다" 문장도 같이 고친다.

## 판단 필요 — 사람에게 묻는다 (018 에서 이월, 019 가 안 건드린다)

1. **기존 `data/crawl.db` 의 옛 열쇠 행 통합** — 마이그레이션이라 야간 금지.
   019 도 **새 DB 에서만 목적을 달성한다**
2. **URL 자격증명이 `pages.url` PK 이자 검색 결과 링크** — 보안 경계, 줄 수 무관 야간 금지
3. `loop/*` 브랜치 **머지 판단** (16개가 한 줄로 쌓여 있다)
4. **`project.md` 의 기본 브랜치 `main` 이 저장소에 없다.** 실제 이력은 `loop/*` 팁이
   줄줄이 달린 한 줄이다. 019 는 관례를 따르고 문서를 안 고쳤다 — 사람이 정한다

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합 ·
옛 표기로 저장된 기존 행의 마이그레이션 · 끝 슬래시 일반화 · 퍼센트 디코딩 ·
`to_ascii` 수정 · userinfo 처리
