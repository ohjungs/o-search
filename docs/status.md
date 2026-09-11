---
signal: GREEN
phase: 리뷰
step: 2/2
attempt: 0
plan: docs-delete-rowid
iteration: 549
updated: 2026-09-12
mode: night
night_iterations: 1
night_red: 0
night_retries: 0
night_self_amendments: 0
ctx: 미상 (.context-state.json 43분 경과 — statusLine 꺼짐, 반복 상한에만 의존)
note: 테스트 phase 통과 — 전수 763 OK · 변이 3판 재현 · 8점 이상 갭 0건
---

# 현재 상태

계획 **96 `docs-delete-rowid`** 개발 **2/2 완료** — 갱신 경로의 세 `DELETE FROM docs` 가
`WHERE url = ?`(FTS5 전수 스캔)에서 `WHERE rowid = ?` 로 바뀌었고, 그 값을 1천·1만·4만
문서에서 **두 열쇠 모두** 쟀다(`docs/e2e/docs-delete-rowid/result.md`).

| N | 옛 `url` | 새 `rowid` | 배수 |
|---|---|---|---|
| 1,000 | 0.164ms/건 | **0.012** | 14배 |
| 10,000 | 2.693 | **0.012** | 220배 |
| 40,000 | 11.950 | **0.014** | 881배 |

판정 ① 새 열쇠 4만/1천 **1.17배**(무관) · ② 옛 열쇠 **72.9배**(선형 재현). 둘 다 참.

**크롤은 끝났다**(2026-09-12 확인 · `pgrep -f websearch.crawl` 비었음). `pages` 가
37,704 → **52,172** 로 올랐고 **그 색인이 이 코드를 썼다** — e2e 가 실물에서 잴 대상이다.

## 테스트 phase (2026-09-12 · 반복 549)

전수 **763 OK**(21.3s). 변이 3판으로 단언이 무는 자리를 재현했다 — 세 `DELETE` 열쇠를
각각 `url` 로 되돌리면 404(`indexer.py:288`) **생존** · noindex(295) **생존** · 갱신(303)
**사망**. 스텝 1 의 docstring 이 적어 둔 천장 그대로다.

**갭 탐색 6종에서 8점 이상 0건 — 새 테스트를 쓰지 않았다**(`test.md` 4절).

- ⑥ 404·noindex 열쇠가 상태로 구별 안 됨 — **4점**. 한 url 의 `docs` 행들은 `pages` 행이
  하나라 조인에 **전부 들어오거나 전부 빠진다**. 두 열쇠의 상태 차이가 원리적으로 없고
  갈리는 것은 값뿐이다(값은 e2e `result.md` 가 잰다). 테스트로 못 박을 수 있는 갭이 아니다.
- ⑦ 다문서 배치의 **rowid 재사용** — **3점**. FTS5 가 최고 rowid 를 재사용하는 것은 실측
  확인했으나, `_insert_doc` 시점에 미처리 행이 전부 현존하므로 새 rowid = max+1 > 모든
  미처리 rowid 라 충돌이 불가능하다. `docs.rowid` 를 참조하는 다른 테이블도 없다(전수 grep).

## 다음 행동

**리뷰 phase**(백지) → e2e. e2e 시나리오는 계획서에 적혀 있다:
실물 `data/crawl.db` **사본**에서 색인을 한 번 돌려 `docs` 행 수와 `GET /search` 응답이
변경 전과 같은지 본다 — **바꾼 것은 값이지 결과가 아니다**를 실물에서 확인한다.

## 설계

**생략** — 기존 함수의 질의 한 줄에 `d.rowid` 를 얹고 `WHERE` 열쇠를 바꿨다. 새 파일·공개
인터페이스·스키마 변경 없음 (`design.md` 1절 트리거 해당 없음).

## 규모 축 (2026-09-11)

색인 **10,461** · pages **37,704** · 1.37GB · 전수 **763 OK**. **병합은 손으로 조립하지
않는다** — `scripts/merge-to-main.sh` (전수가 초록일 때만 민다).

## 사람 결정 대기

- **`docs/patches/userinfo-leak-refuse-credentials.patch`** — URL 자격증명이 크롤·저장·렌더로
  새는 건. 구현·테스트까지 초록 확인 후 패치로 뽑아 뒀다. **보안 경계**라 적용 보류.
- **`~/.claude/settings.json`** 미커밋 — 내 변경이 아니고(`model: opus → opus[1m]` + `allow`
  자리 정렬 · 권한 상향 아님을 diff 로 확인) 코어층 가드가 막았다. 승인하면 `--no-verify`.
- **`~/.claude/hooks/ojeong-guard.cjs`** — `RUNNER` 가 `^python3` 로 앞머리를 고정해 **환경변수로
  시작하는 이 저장소의 정식 테스트 명령을 검증으로 한 번도 안 센다.** 고칠 내용은
  `~/.claude/hooks/guard.test.js` 가 명세한다. 분류기가 그 파일 쓰기를 막아 내가 못 고친다 —
  나를 제약하는 가드를 내가 푸는 것은 권한 상향이라 우회하지 않는다.

## 정지 사유

**컨텍스트 85% 이상** (`.context-state.json` 실측 85 · 경계값은 정지 쪽). 실패가 아니다 —
스텝 경계에서 끊었고 기록·보고서를 남겼다. 이어서 하려면 같은 명령을 다시 부른다.
(`docs/digest.md` 208줄 — 상한 200 초과. 다음 짧은 경로 후보다)
