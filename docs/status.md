---
signal: GREEN
phase: e2e
step: 2/2
attempt: 0
iteration: 491
updated: 2026-09-09
ctx: 62
night_iterations: 7
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — e2e 완료. 다음은 **패치 추출 · 작업 트리 되돌리기 · 야간 보고서**다

**여기가 야간 처분이 실행되는 자리다.** 계획 83 은 보안 건이라 `SKILL.md` 자동 적용
기준의 「보안 관련 — 줄 수 무관 항상 보류」에 걸린다. **적용된 채로 남기지 않는다.**

- `e2e/domain_key_e2e.py` 시나리오 1 을 갈아 끼웠다 — 「세 표기가 한 도메인」 →
  **「자격증명 URL 은 수신 0건 · 남은 표기는 여전히 한 칸」**. 하네스는 그대로다.
- **실물 한 번이 거짓 초록을 잡았다.** 첫 단언은 Host 헤더의 `@` 를 봤는데
  **`urllib` 은 Host 에 userinfo 를 안 싣는다** — 변이(거절 삭제) 사본에서 도착이
  3→4회로 늘었는데도 **초록이었다.** 증거를 **경로**(`/p1` = 자격증명 href 로만
  존재하는 자리)로 바꾸니 변이에서 종료 1 로 죽는다. `Authorization` 검사도 더했다.
- 실측: `OK 5.2s` · `--control` → 측정 불능(2) · 전수 **717 OK**.
- `project.md` 의 그 e2e 설명 줄과 `docs/e2e/userinfo-leak/result.md` 기록.
- **남은 절차**: ① `git diff main...HEAD -- src tests e2e README.md` 를
  `docs/patches/userinfo-leak-refuse-credentials.patch` 로 뽑는다(테스트 포함)
  ② `git apply --check` ③ 작업 트리 되돌리기 ④ 되돌린 상태에서 전수 709 OK 확인
  ⑤ `docs/reports/night_2026-09-09.md` ⑥ `metrics.jsonl` 한 줄.
