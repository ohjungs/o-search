---
signal: GREEN
phase: 개발
step: 1/2
attempt: 0
iteration: 487
updated: 2026-09-09
ctx: 68
night_iterations: 3
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — 개발 1/2 완료. 다음은 **개발 2/2 (시드 스킵 사유)**다

**야간 처분은 그대로 패치만 남기기다.** 아직 커밋은 브랜치에 쌓이는 중이고,
마지막에 `docs/patches/` 로 뽑은 뒤 되돌린다.

- **한 것**: `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을 준다.
  되붙이던 `userinfo + at` 을 지웠다. 전수 **710 OK**.
- **뒤집은 계약을 테스트가 안다**: `test_userinfo_survives` → 
  `test_a_url_carrying_credentials_is_refused`(세 모양: `u:pw@` · `user@` ·
  `google.com@evil.test`) + 대조군 `test_an_at_sign_outside_the_netloc_is_not_credentials`
  (경로·질의의 `@` 는 통과). 멱등성 목록에서도 userinfo 항목을 뺐다.
- **곁가지 둘을 함께 닫았다** — 스텝이 아니라 **가드가 울려서** 한 것이다:
  ① `HistoryCapTest` 가 321 > 300 으로 울어 반복 461~474 를 `history_077.md` 로
  회전하고 `digest` 명부·회전 줄을 더했다(계획 76 가드의 **두 번째 발화**)
  ② `test_verification_counts_match_reality` 가 README 단위 수 709 → **710** 을 요구했다.
- **다음 반복이 알아야 할 것**: `e2e/domain_key_e2e.py` 는 **아직 안 고쳤다.**
  설계가 예고한 대로 지금 돌리면 종료 2(측정 불능)로 크게 실패한다 — 그 파일의
  시나리오 1 을 새 계약으로 갈아 끼우는 것은 **e2e phase 몫**이다.
