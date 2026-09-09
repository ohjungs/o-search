---
signal: GREEN
phase: 설계
step: 0/2
attempt: 0
iteration: 486
updated: 2026-09-09
ctx: 62
night_iterations: 2
night_red: 0
night_retries: 0
plan: userinfo-leak
---

## 다음 반복이 읽을 것 — 설계를 마쳤다. 다음은 **개발 스텝 1**이다

**야간 처분은 그대로 패치만 남기기다** (`SKILL.md` 「보안 관련 — 줄 수 무관 항상 보류」).
끝까지 구현·테스트하고 초록을 확인한 뒤 `docs/patches/` 로 뽑고 작업 트리를 되돌린다.

- **고른 안은 후보가 적어 둔 둘이 아니다.** A(렌더에서 가린다)·B(저장 열쇠에서 뗀다)는
  **둘 다 자격증명이 남의 서버로 나가는 것을 그대로 둔다.** 컨셉 갈림길 1순위가
  크롤 윤리라 **C — 입구에서 거절**을 골랐다. `docs/design_userinfo-leak.md`
- **3-2 탐침이 실제로 뭘 잡았다.** 「거절해도 잃는 것이 없다」는 제품 쪽에서는 참이고
  (실물 400행 중 거절될 것 **0건**) **테스트 쪽에서는 거짓**이었다 — URL 리터럴 352개
  중 netloc `@` 가 10개고 그중 **셋**이 걸린다: `tests/test_urls.py:289`
  (`test_userinfo_survives` — 계약 자체) · `:321`(멱등성 목록) ·
  `e2e/domain_key_e2e.py:150`(시드가 거는 링크).
- **대가를 하나 치른다** — `domain_key_e2e.py` 는 userinfo 가 「`normalize` 가 접지
  않고 `domain_key` 는 접는」 **살아 있는 유일한 축**이라고 스스로 적어 뒀다. C 를
  넣으면 그 축이 사라지고 그 파일의 **종료 2 가드가 크게 실패**한다(조용한 통과가 아니다).
  처방은 같은 하네스 위에서 **재는 것을 갈아 끼우기** — 「세 표기가 한 도메인」 →
  「자격증명 표기는 수신 0건 · 남은 표기는 여전히 한 도메인」. 017 의 **e2e 급** 회귀
  탐지기는 여기서 끝나고 단위 `tests/test_urls.py:162` 만 남는다. 파일에 적는다.
- **계약은 설계 「계약」 절이 정본이다** — `normalize` 는 netloc 의 `@` 만 보고,
  **경로·질의의 `@` 는 통과**시킨다. `to_ascii`·`domain_key`·`_split`·`robots._base`
  는 무변경 · `serve`·`store`·`indexer` 0줄.
