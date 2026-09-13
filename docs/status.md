---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
plan: robots-nonascii
iteration: 581
updated: 2026-09-13
mode: night
night_iterations: 12
night_red: 0
night_retries: 0
night_self_amendments: 0
ctx: 측정 불가 — 게이트 ⑦ **열두 번째 재현**(state 의 `session_id` 가 내 슬러그에 없다).
  statusLine 꺼진 것과 동일 취급 — 반복 상한에만 의존한다. 5h 30 · 7d 55 만 유효하다(둘 다 85 미만)
note: **계획 100 `robots-nonascii` 를 세웠다 — 이 밤의 셋째이자 마지막 계획.**
  근거는 digest 6순위 `[7]` 이고 **오늘 다시 쟀다**: 비ASCII 호스트가 `RobotsCache.allowed`/
  `delay` 에서 `UnicodeEncodeError` 로 샌다. 설계는 건너뛴다(트리거 0 — 공유 함수 `except`
  한 줄). 다음 반복은 **개발 스텝 1/1**.
---

# 현재 상태

**계획 100 `robots-nonascii` 개발 대기 — 이 밤의 셋째 계획(상한).**
계획서 `docs/plan_robots-nonascii.md` · 브랜치 `loop/robots-nonascii`(기점 `064fe56`).

**근거(오늘 실측)**: `RobotsCache().allowed("http://한글.invalid/페이지")` 가
`UnicodeEncodeError` 로 죽는다. `delay()` 도 같다. 퓨니코드 호스트는 정상(`False`/`None`).
그 예외는 `ValueError` 의 자손이라 `_fetch_robots` 의 `except (URLError, OSError)` 가
못 잡고, `allowed` 안의 `except ValueError` 는 `can_fetch` 만 감싸 **한 칸 옆**이다.

- **오늘 크롤 경로에서는 도달 불가다** — 씨앗(`crawl.py:195`)도 링크(`links.py:34`)도
  `urls.normalize` 를 거쳐 퓨니코드로 바뀐다. 「지금 죽는 버그」가 아니라 **관문이 입력
  하나에 죽는다**는 문제로 적었다. 처방 방향은 기존 `except ValueError` 와 같은 값(차단)이다.
- **설계 생략 사유**: 공유 함수 `_fetch_robots` 의 `except` 한 줄 — `design.md` 1절
  트리거(새 모듈·공개 인터페이스·데이터 구조·3파일·되돌리기 어려움·대안 갈림) 0개.

**계획 99 는 `main` 에 들어갔다**(`064fe56`) — e2e 2종 통과 · 변이 9판 전부 잡힘 ·
전수 779 OK. 병합 첫 판은 `StepSyncTest`·`IterationSyncTest` 가 **RED 로 막았고**
(`plan` 이 빈칸인데 `step` 1/1 · metrics 579 ≠ status 580) 고쳐서 밀었다.

**게이트 ⑪ 은 반복 575 에 닫혔다** — 자동 스냅샷과 리뷰 커밋의 **트리가 같아서** 강제 푸시도
되감기도 필요 없었다. 계획 98 은 전수 770 OK 위에서 `main` 에 들어갔다(`b8f0bb1`).

## 빈손 대조 핀 — 기준 트리 `064fe56`

계획 99 가 `main` 에 들어갔으므로 규칙대로 **기준을 새 `main` 으로 옮긴다**.

```bash
git diff --stat 064fe56..HEAD -- src tests e2e scripts docs/digest.md docs/candidates.md docs/specs
gh issue list --state open --limit 20     # 트리 밖 — 항상 돌린다
```

**핀은 «코드»의 함수지 «환경»의 함수가 아니다** — 파이썬·OS 가 움직이면 같은 트리가 다른
결과를 낸다. 그래서 전수는 밤마다 돌린다(**779 OK** · 18.7s · Python 3.9.6).

## 사람 결정 대기 — 하나를 열어야 이어진다

근거·재현·처방은 갖춰졌고 막는 것은 판단뿐이다. **서술은 닫혔다 — 상세는 괄호 안 반복 번호에 있다.**

- **① 동시 색인이 만드는 중복 `docs` 행** — 반복 550 리뷰 보류. 고치는 자리는 `index_pages`
  의 트랜잭션 경계(`BEGIN IMMEDIATE`)이고 재구축 갈래의 `BEGIN`(`indexer.py:217`)과 중첩을
  함께 풀어야 한다. **자기 계획 크기**이고 레이스 컨디션이라 밤이 안 연다. 승인하면 바로 계획.
- **② `perf_crawl.py` 기준선 여유 0.5%**(digest 후보 8점) — ①재기준선 ②[열림] 대비 비율
  ③참고용 강등 **셋 중 택1**. 밤이 못 고르는 이유는 셋 다 「통과시키려고 시나리오를 낮추는
  것」과 겉모양이 같아서다.
- **③ `docs/patches/userinfo-leak-refuse-credentials.patch`** — URL 자격증명이 크롤·저장·렌더로
  새는 건. 적용 상태에서 초록 확인 후 뽑아 뒀다. **보안 경계**라 밤이 영구히 못 연다.
- **④ `~/.claude/settings.json` 미커밋** — 내 변경이 아니고(`model: opus → opus[1m]` + `allow`
  자리 정렬 · 권한 상향 아님을 diff 로 확인) 코어층 가드가 막았다. 승인하면 `--no-verify`.
- **⑤ `~/.claude/hooks/ojeong-guard.cjs`** — `RUNNER` 가 `^python3` 로 앞머리를 고정해 **환경변수로
  시작하는 이 저장소의 정식 테스트 명령을 검증으로 한 번도 안 센다.** 고칠 내용은
  `~/.claude/hooks/guard.test.js` 가 명세한다. 분류기가 그 파일 쓰기를 막아 내가 못 고친다 —
  나를 제약하는 가드를 내가 푸는 것은 권한 상향이라 우회하지 않는다.
- **⑥ `docs/digest.md` 212줄**(상한 200) — **561 이 산술로 확인: 승인으로도 안 풀린다.** 유일한
  레버가 닿는 줄이 **넷**뿐이라 다 지워도 207 이고, 남는 175줄은 규칙이 남기라 한 절과
  **탐색이 입력으로 읽는** 후보 절·사람 대기열이다. `tests/test_docs.py:420-424` 가 **일부러
  안 재는** 축이다. **아침 처방은 「지우게 해 달라」가 아니라 「상한 200 이 이 파일 모양에 안 맞다」**.
- **⑦ 정지 조건이 `session_id` 를 안 본다** (557 최초 · 570 이 **열 번째**) — `.context-state.json`
  은 모든 세션이 공유하는 파일 하나고 신선도 검사는 누가 썼는지를 안 본다. 563 이 판정을 한
  줄로 줄였다: `~/.claude/projects/<내 cwd 슬러그>/<state 의 session_id>.jsonl` 이 **없으면 남의
  것**이다. 처방(남의 것이면 statusLine 꺼진 것과 동일 취급)의 자리가 SKILL.md 의 «나를 멈추는
  룰»이라 밤이 안 연다(⑤ 와 같은 이유). **⑧ 의 `ctx` 칸은 이미 오염됐다.**
- **⑧ `metrics.jsonl` 이 밤마다 다른 것을 센다** (560 최초 · 561·562 확인). 셋이 동시에 깨졌다:
  **(ㄱ)** SKILL.md:226 의 「야간 시작 시 리셋」이 세션인지 그 밤인지를 안 정해 합이 누적 반복을
  넘는다 · **(ㄴ)** 빈손 밤엔 변하는 칸이 `ctx` 뿐인데 그게 ⑦ 로 굳어 해상도가 0 이다 ·
  **(ㄷ)** 53줄이 스키마 두 가지라 「정지 사유」가 아는 구간에서도 뒤바뀌어 있다.
  처방: 리셋 단위를 세션으로 못박고 줄에 세션 식별자를 넣는다. 자리가 공유 스크립트라 밤이 안 연다.
- **⑨ launchd 에이전트 둘이 이 저장소를 밤중에 함께 만진다** (563 최초 실측) —
  `com.ohjungs.osearch-{autoloop,autocommit}.plist` · **각 3시간 주기**. 563 이 스텝 도중이던
  11:34:41 에 **autocommit 이 내 미커밋 트리를 통째로** `loop/sync-563` 에 커밋하고 `main` 에
  병합했다(`d74ed2f`·`7a6c94c`) — **가설이 아니라 피해다.** **처방 택1**: ㉮ 수동 실행 중
  `launchctl bootout` ㉯ autocommit 에 「`loop/*` 이거나 트리가 더러우면 건너뛴다」 가드
  ㉰ 주기를 피해 실행. 셋 다 **사용자 기계의 예약 작업**이라 밤이 못 고른다.
- **⑩ `rules/docs.md` 2절 파일 표에 `baselines.md` 가 없다** — 계획 97 이 만든 234줄짜리 새
  문서 유형이라 **상한도 회전 규칙도 없다.** 자리가 저장소 밖(SKILL.md)이라 밤이 못 연다.

- ~~**⑪ `loop/e2e-roster` 가 원격과 갈라져 있다 — 병합이 막혔다**~~ — **해소(2026-09-13 반복 575).**
  적어 뒀던 처방 둘(㉮ 강제 푸시 승인 · ㉯ 로컬 되감기 승인)은 **둘 다 필요 없었다.**
  자동 스냅샷(`55a57db`)과 리뷰 커밋(`e31d115`)은 **트리가 같아서**(`git diff` 빈손) 평범한
  병합으로 합쳐진다 — 충돌 셋(`status`·`history_current`·`metrics`)은 내 쪽이 상위집합이라
  `--ours`, 병합 결과가 `fb1ac33` 과 0줄 차이임을 확인하고 커밋(`a9a14eb`)했다.
  `merge-to-main.sh` 가 전수 **770 OK** 위에서 `main` 을 밀었다(`b8f0bb1`).
  **남는 것은 원인 쪽 게이트 ⑨ 다** — 스냅샷을 만든 autocommit 은 그대로 돌고 있다.

병합은 손으로 조립하지 않는다 — `scripts/merge-to-main.sh` (전수가 초록일 때만 민다).

## 규모 축 (2026-09-13)

`pages` **52,172** · `docs` **40,347** · 2.48GB · 전수 **779 OK**(18.7s).
**e2e 는 13종이 아니라 22종이다** — 시나리오 **18** + 측정 **4**. 계획 98 이 명부와
「빠진 이름」을 무는 자를 세웠고, 계획 99 가 그 줄의 **수와 실재**를 못박는다.
필수 읽기 **375줄**/600 (`project.md` 60 + `status.md` 116 + `history_current.md` 199) — 여유 225줄.
