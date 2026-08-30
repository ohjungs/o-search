---
signal: GREEN
phase: DONE
step: 1
attempt: 0
iteration: 173
updated: 2026-08-30
ctx: 75
night_iterations: 50
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt` DONE — 전 phase(계획·설계·개발 4·테스트·리뷰·e2e) 닫혔다.**
`plan_history_021.md` · 설계 `design_history_021.md` · e2e 결과 `docs/e2e/graceful-interrupt/result.md`.
브랜치: `loop/graceful-interrupt`. 작업 트리 깨끗 · 원격과 갈라짐 없음.
**열린 계획 0.** `main` 은 `f888518` 그대로 — **병합은 사람 판단 항목이다.**

기준선: 단위 **447건 OK** · e2e **18종 전수 rc=0**(합계 154초) · recall@10 100%/95% ·
오탐 평균 14.0 · p95 9.30ms · JS 0 B · 최저 명암비 4.87:1 · 처리량 10.25/10.28 docs/s.

## e2e phase 결과 (마지막 phase, 코드 0줄)

만든 파일은 `docs/e2e/graceful-interrupt/result.md` 하나다. **재는 수단은 스텝 4 가 이미
커밋했고**(`e2e/interrupt_e2e.py`, `6349a37`) 이 phase 는 결과를 기록으로 옮겼다
(`rules/e2e.md` 5절 — 이미 있는 것으로 되면 새로 만들지 않는다).

- **목표 12초에 실측 10.0초.** 착수 전 69.57초였다. `[1]` 안 답하는 서버 + `Crawl-delay: 30`
  → **SIGINT 뒤 10.0초 · rc 130 · 페이지 요청 1건 · DB 0행**.
- `[2]` 느린 서버(응답 5초) → 5.0초에 종료하고 **떠 있던 응답 1행을 줍는다** ·
  `[3]` 중단 중 `Crawl-delay` **위반 0** · `[4]` 두 번째 Ctrl-C **0.00초에 rc `-2`** ·
  `[0]` 대조군 3페이지 rc 0 · `--control` **rc 2**(잴 대상이 없으면 초록이 아니다).
- **여유는 공칭값 그대로** — 시나리오 1 은 상한 12.0에 10.0(여유 2.0), 2 는 8.0에 5.0(3.0).
  얇다는 것은 이미 아는 항목(`digest.md` `[4]`)이고 **상한을 올리면 계획의 12초 목표 자체가
  흐려져** 값을 안 건드렸다. 깨지는 날의 답은 `SLOW_SECONDS` 인하다.
- 품질 4축·크롤 처리량·1초 하한 **전부 기준선 그대로**(표는 `result.md`).
- 회전을 **먼저** 했다 — `history_current.md` 가 정확히 상한 300줄이라 앞 여덟 반복을
  `history_012.md` 로 밀고(300 → 100줄) `digest.md` 에 압축했다. 앞 두 번은 넘긴 채 갔다.

## 다음 반복이 할 일

**새 계획 탐색(discover)** — 열린 계획이 0 이다. `digest.md` 의 `## 다음 계획 후보`
(특히 `[5]` `--deadline` 만료가 `stop` 을 안 쓴다)와 `index.md` 를 읽고 고른다.
계획 34 가 무엇을 남겼는지는 `index.md` 34번과 `plan_history_021.md` 8절에 있다.
`main` 병합은 루프가 하지 않는다.

## 한도 (넘으면 RED)

- 도메인당 요청 간격 1초 이상 · robots.txt `Crawl-delay` 준수. **중단 중에도 그렇다.**
- `data/crawl.db` 실물·스키마를 안 건드린다. e2e·탐침은 임시 디렉터리에서만.
- 외부 네트워크 금지 — 로컬 테스트 서버만.
- `docs/specs/` 는 사용자 소유(읽기만) · `--no-verify` 금지 · `main` 직접 커밋 금지.
