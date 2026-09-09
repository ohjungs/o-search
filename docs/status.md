---
signal: DONE
phase: 계획
step: 2/2
attempt: 0
iteration: 492
updated: 2026-09-09
ctx: 66
night_iterations: 8
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — 계획 83 은 **패치로 남았다.** 적용은 사람이 한다

- **`docs/patches/userinfo-leak-refuse-credentials.patch`** (382줄 · 구현 + 테스트 +
  e2e). `git apply --check` 통과. 아침에 `git apply <경로>` 로 적용한다.
- **작업 트리는 되돌렸다** — `src`·`tests`·`e2e`·`README.md` 는 `main` 과 같고
  전수 **709 OK** · 옛 `domain_key_e2e.py` 도 `OK 7.2s` 로 그대로 돈다.
  브랜치에 남는 것은 **문서와 패치**뿐이다.
- **왜 적용하지 않았나**: `SKILL.md` 자동 적용 기준 「보안 관련 — 줄 수 무관 항상
  보류」 · `severity.md` 3절. 신뢰 경계를 **무엇이 넘는지** 좁히는 변경이라
  판단을 사람에게서 뺏지 않는다.
- **적용하면 바뀌는 계약 하나**: `urls.normalize` 가 netloc 에 `@` 를 든 URL 에
  `None` 을 준다(018 의 「보존」을 뒤집는다). 되돌리려면 `normalize` 안의 조건
  한 줄을 지운다.
- 야간 보고서: `docs/reports/night_2026-09-09.md`.
