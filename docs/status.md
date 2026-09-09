---
signal: DONE
phase: 계획
step: 0/0
attempt: 0
iteration: 494
updated: 2026-09-09
ctx: 46
night_iterations: 1
night_red: 0
night_retries: 0
plan: null
---

## 다음 반복이 읽을 것 — 탐색은 **여전히 막혀 있다.** 아침 할 일은 어제와 같은 둘

1. **패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch`
   (382줄 · 구현 + 단위 + e2e · `git apply --check` 통과). 계획 83 의 산출물이고
   야간이 적용하지 않은 이유는 「보안 관련 — 줄 수 무관 항상 보류」다.
   적용하면 바뀌는 계약: `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을
   준다(018 의 「보존」을 뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.
2. **다음 계획을 사람이 하나 열어 주는 것** — 8순위 전수를 **두 밤 연속** 돌았고
   근거가 0 이다. 막힌 자리는 아래에 이름으로 적어 뒀다.

## 이번 반복(494)이 한 것 — 짧은 경로 `archive-backlog`

탐색이 아니라 **DONE 처리 자신**이었다. `docs.md` 4절(계획을 마치면
`plan_<slug>.md` → `plan_history_<NNN>.md`)을 **강제하는 자가 0개였고 두 번
미끄러져 있었다** — 치우고, 그 자리를 재는 자를 얹었다.

- `design_recrawl.md` → `design_history_066.md`(계획 80) ·
  `plan_ethics-floor.md` → `plan_history_067.md`(계획 81) ·
  `tests/test_store.py:139` 의 인용도 아카이브 이름으로 옮겼다.
- **치우기만 하면 다음 계획이 또 미끄러진다** — `archive_gap` +
  `ArchiveBacklogTest`/`ArchiveGapTest`(`step_gap`·`strike_gap`·`verdict_gap` 과
  같은 실물/갈래 짝). 변이 3종 전부 잡힘: 이동 전 상태 되살리기 · `완료` 가드
  제거 · 완전 일치를 `startswith` 로 넓히기.
- **오탐 축이 실물에 산다** — `보류(패치)` 인 `plan_userinfo-leak.md` 는 제자리가
  맞다(중복 방지가 `docs/plan_*.md` 중 보류인 것을 읽는다). 「`완료` 만 문다」를
  지우는 변이가 **바로 그 파일을 물어** 승인 대기 중인 계획을 치우라고 시켰다.
- 단위 709 → **715건 OK**(rc 0, 맨몸). README 의 개수 못이 709→715 를 스스로 잡았다.
- 브랜치 `loop/archive-backlog` (커밋 `d05ea2a`). `main` 미병합.

## 반복 번호를 486 → 494 로 고쳤다

`3e19f28` 병합이 `status.md`·`metrics.md` 를 seed-tier1 쪽(486)에서 가져오면서
`history_current.md` 쪽(493)과 갈렸다. `IterationSyncTest` 는 status↔metrics 만
보므로 **둘이 나란히 틀린 것은 못 잡는다.** 493 이 실제 마지막 반복이라 이번을
494 로 잡았다 — 조용히 밀리는 것보다 낫다. digest `## 반복 실패` 에 등재했다.

## 탐색 결과(반복 494, 8순위 전수) — 어제와 같은 0

① 실패 테스트 0(**715 OK** rc=0) ② 린트·타입 도구 없음 ③ 코드 `TODO` 0
④ `docs/candidates.md` 없음 ⑤ 보류 절은 `userinfo-leak` 패치 하나뿐(보안·사람 판단)
⑥ 후보 절 5점 이상 **직접 세 건을 다시 열어 확인했고 셋 다 그대로 닫혀 있다** —
`[7]` 갱신 경로 `DELETE` 선형(여는 조건 「코퍼스 만 단위」 · 오늘 118문서) ·
`[high]` 옛 열쇠 행 통합(**마이그레이션이라 야간 금지**) · `[7]` OFFSET
페이지네이션(공개 API `?page=N` 을 커서로 바꾸는 건이라 사람이 정할 갈림길)
⑦ 반복 실패 — 아래 한 줄을 새로 등재 ⑧ `gh issue list` 0건.

**사양 축도 한 번 훑었다(1~8순위 밖 · 계획 43·77 의 전례).** 컨셉 판정 기준 중
재는 자가 없는 것은 **성능 3(수집→검색 10분)** 과 **경량 2(RSS 2GB)** 둘인데,
전자는 구조적으로 이미 만족한다(`store.py:76` WAL + `upsert` 마다 커밋이라
crawl 이 쓰는 동안 indexer 가 읽는다 · 증분 재실행은 계획 78 실측 10만 환산
29.5초)라 **남은 것은 문서 공백이지 코드 공백이 아니고**, 후자는 100만 문서가
있어야 잰다. 둘 다 오늘 밤 열 계획이 아니다.

## 새로 등재한 반복 실패

**「절차를 문서에만 적고 재는 자를 안 만든다」** — `docs.md` 4절이 오늘까지
2회 미끄러졌고 전수 709건이 그 상태로 초록이었다. 같은 밤 어제 친 취소선 둘
(`[9]` · digest 압축 줄)과 **같은 모양**이다: 기록은 닫혔다고 말하는데 기제가 없다.
이번엔 자를 함께 얹었으므로 이 항목은 처방까지 들어간 채로 등재한다.
