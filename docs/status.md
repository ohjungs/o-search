---
signal: GREEN
phase: 개발
step: 2/2
attempt: 0
iteration: 488
updated: 2026-09-09
ctx: 73
night_iterations: 4
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — 개발 2/2 완료. 다음은 **테스트 phase (변이 검사)**다

**야간 처분은 그대로 패치만 남기기다.** 브랜치에 쌓인 뒤 마지막에 `docs/patches/`
로 뽑고 작업 트리를 되돌린다. **적용된 채로 남기지 않는다.**

- **한 것**: `urls.has_credentials(url)` 를 내고 `normalize` 가 그것을 부른다
  (판정을 두 곳에 두지 않는다). `crawl` 시드 루프가 자격증명 가지를
  `normalize is None` **앞에** 달았다 — 뒤에 달면 영영 안 닿는다.
- **사유를 알리려다 같은 것을 흘릴 뻔했다.** 위·아래 가지는 시드를 통째로 찍는데
  이 가지가 그러면 **비밀번호가 stderr 로 나간다.** `urls.domain_key(seed)` 로
  호스트만 적는다 — userinfo 를 떼는 함수가 이미 있었다.
- **단언 넷**: 사유에 「자격증명」이 있고 「읽을 수 없는」이 **없다**(거짓 사유 금지) ·
  `fetch_times` 가 비었다(요청이 안 나갔다) · 경로의 `@`(`http://a.com/@handle`)는
  **시드로 통과**한다.
- 전수 **712 OK** · README 단위 수 710 → 712.
- **남은 것 둘**: ① 테스트 phase — 변이로 이 자들이 진짜 무는지 확인
  ② e2e phase — `e2e/domain_key_e2e.py` 시나리오 1 갈아 끼우기(아직 안 고쳤다).
