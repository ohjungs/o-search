---
signal: GREEN
phase: e2e
step: 2/2
attempt: 0
iteration: 490
updated: 2026-09-09
ctx: 56
night_iterations: 6
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — 리뷰 완료(자동 수정 3). 다음은 **e2e phase**다

**야간 처분은 그대로 패치만 남기기다.** e2e 를 마치면 `docs/patches/` 로 뽑고
작업 트리를 되돌린 뒤 야간 보고서를 쓴다. **적용된 채로 남기지 않는다.**

- **백지 패스(패스 A)를 별도 세션에 넘겼다.** 준 것은 diff 와 수정된 파일뿐이다.
- **[R83-1] 내가 낸 RED 를 백지 패스가 주웠다.** 반복 489 가 `status.md` 의
  `step:` 을 `—` 로 적어 `test_docs.StepSyncTest` 가 빨개졌다(전수를 status 수정
  **전에** 돌려서 커밋 때 못 봤다). `step: 2/2` 로 되돌렸다 — **전수 717 OK.**
- **[R83-2]** `has_credentials` 독스트링의 「못 읽는 URL 에는 `False`」가
  **자기 테스트와 모순**이었다(폴백 경로의 `u:pw@[oops` 는 `True`). 실제 계약은
  「안 던진다」다 — 독스트링과 `design_userinfo-leak.md` 계약 절을 함께 고쳤다.
- **[R83-3]** 설계 「범위 밖」이 예고한 digest 후보 등재 — `domain_key` 의 userinfo
  접기는 죽은 코드가 아니라 **호출자 둘 중 하나(시드 메시지)에서만 산다**.
- **넘긴 것**: e2e `domain_key_e2e.py` 종료 2(설계가 예고한 그것) → **e2e phase 몫** ·
  기존 DB 행 정리(계획 「하지 않을 것」) · 시드 루프와 `normalize` 가 서로 다른
  문자열에 같은 질문을 묻는 커플링(구성 가능한 불일치를 못 찾아 80점 미만).
- **다음**: `e2e/domain_key_e2e.py` 시나리오 1 을 「자격증명 표기는 수신 0건 · 남은
  표기는 여전히 한 도메인」으로 갈아 끼우고, 파일 독스트링에 **017 의 e2e 급 회귀
  탐지기가 여기서 끝나고 단위 `test_urls.py` 로 남는다**고 적는다. `project.md` 의
  그 e2e 설명 줄도 함께 고친다.
