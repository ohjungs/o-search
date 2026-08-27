---
signal: GREEN
plan: normalize-gaps
mode: night
phase: 리뷰
step: 3/4
attempt: 0
iteration: 120
night_iterations: 3
night_red: 0
night_retries: 0
updated: 2026-08-28 (반복 120 · 019 테스트 2/4)
ctx: 67% / 200k
rules: 1411a37
---

# 현재 상태

**계획 019 `normalize-gaps` 스텝 2/4 테스트 완료 — 다음은 스텝 3/4 리뷰.**
브랜치 `loop/normalize-gaps` (기점 `33e531d` = 018 끝). 계획서 `docs/plan_normalize-gaps.md`.

**변이 5종이 전부 죽고 죽는 집합이 갈린다.** 무변이 기준선 386건 OK 를 먼저 잡았다.

| 변이 (이 줄을 안 썼다면) | 죽는 테스트 | 이 변이만의 보험 |
|---|---|---|
| M1 `_fold_dots` 호출 없음 | `dot_segments_fold` · `dots_do_not_climb` · `trailing_dot` | 앞 2건 |
| M2 끝 세그먼트 보정(`out.append("")`) 없음 | `trailing_dot` | 그 1건이 유일 보험 |
| M3 `lstrip("0")` 없음 | `leading_zero_does_not_make_a_new_server` | 유일. **점 변이들과 교집합 0** |
| M4 `posixpath.normpath` 로 대체 | `only_dot_segments_fold_nothing_else`(대조군) · **`non_empty_path_keeps_its_trailing_slash_as_is`(018 것)** · `trailing_dot` | 대조군 2건 |
| M5 `len(out) > 1` → `if out` | `dots_do_not_climb_above_the_root` | 그 1건이 유일 보험 |

**M4 가 018 의 기존 테스트를 죽인다** — `posixpath` 를 골랐으면 018 이 명시적으로
거부한 끝 슬래시 일반화를 되살렸을 것이고, 그것을 계획서의 주장이 아니라 **남의
테스트가 독립적으로** 잡았다.

**M5 는 `http://a.testp` 를 만든다** — `/../p` 에서 루트 위로 올라가면 경로가 `p` 가
돼 호스트에 들러붙는다. **018 리뷰가 잡은 탭 밀림과 같은 실패 유형**(조용히 다른
호스트가 된다)이고, 잡는 테스트는 하나뿐이다.

**갭 2건을 메웠다.** ① 멱등성 목록에 점 세그먼트·`:080` 을 넣었다 — 접기는 두 번
돌면 더 접힐 수 있는 유일한 규칙이다 ② `isdigit()` 은 `٠٨٠`·`²` 에도 참인데 `int()`
는 `²` 에서 던진다. 019 가 그은 새 가지가 "열쇠를 만들다 안 죽는다" 는 017 계약을
안 깨는지 `test_an_unreadable_port_does_not_raise` 에 넣었다(둘 다 자기 칸에 남는다).

## 다음 스텝 — 3/4 리뷰

백지 세션(diff·소스만, `docs/`·`git log` 차단). `rules/review.md`.

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
