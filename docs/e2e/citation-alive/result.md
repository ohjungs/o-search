# e2e 결과 — citation-alive (계획 109, e2e phase)

- 2026-09-28 · 반복 655 · **새로 만든 e2e 파일 0개** (계획 6절의 잠정 판정을 실측으로 확정 —
  계획 42·108 과 같은 자리다)
- 선통과: 전수 `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests`
  → **842 OK rc=0** (맨몸·포그라운드). 린터·타입체커 **없다**(`docs/project.md ## 명령`).
  **CI 없다** — `.github` 가 없고 `project.md` 에 확인 명령이 없다(`rules/e2e.md` 1절 2항 해당 없음)
- 제품 **동작 0줄** — `git diff 3aaa00a..HEAD -- src` 는 5줄이고 **전부 `#` 로 시작하는 주석**이다
  (비주석 변경 줄을 센 실측: **0**). 그래서 컨셉의 성능·경량 축은 **이 계획이 건드린 파일에
  걸 것이 없다** — 돌리지 않았고, **「통과」라고 적지 않는다**(`rules/e2e.md` 1절 3항)
- UI 없음 → 4절 8단계 체크리스트 해당 없음. `data/crawl.db` 는 **손대지 않았다**(mtime 09-15
  그대로 · 이 계획의 어떤 명령도 DB 를 열지 않는다)
- 사본: `git archive HEAD` 를 `/tmp/zp109_e2e` 에 풀어 **저장소 워킹트리는 무변경**으로 뒀다

## 시나리오 — 계획 6절 그대로 셋

소비자가 **루프 자신**이라 사용자 흐름이 「전수를 돌린다」다. 그래서 e2e 도구는 전수 러너고,
「사용자가 하는 그대로」는 **마감이 하는 파일 이동을 사본에서 그대로 하는 것**이다.

### ① 대조군 — 손대지 않은 사본이 초록

```
cd /tmp/zp109_e2e && … scripts/verdict.sh python3 -m unittest discover -b tests
  → ── Ran 842 tests in 24.214s OK rc=0
```

### ② 사건 재연 — 아카이브하고 인용을 안 고치면 **RED**

`rules/docs.md` 4절의 마감을 그대로 밟았다(사본에서):

```
mv docs/plan_citation-alive.md   docs/plan_history_084.md
mv docs/design_citation-alive.md docs/design_history_082.md
  → ── Ran 842 tests in 24.460s FAILED (failures=1) rc=1
```

**실패는 정확히 하나**고 그것이 이 계획의 자다:

```
FAIL: test_code_cites_documents_that_exist (test_docs.CitationAliveTest)
  tests/test_docs.py:2094 — `design_citation-alive.md`
  tests/test_docs.py:2105 — `plan_citation-alive.md`
  tests/test_docs.py:2146 — `design_citation-alive.md`
```

**다른 문서 가드는 하나도 안 울었다** — 계획 파일이 사라지고 `index.md` 행이 그대로인데도
전수가 조용하다. digest `[7]` 이 적은 「831 OK 가 넷을 안 물었다」와 같은 그림이고, 이 자
하나가 그 그림을 바꾼다.

**이 셋은 검사 자신의 코드 안에 있다** — 주석 둘과 **실패 메시지 문자열 하나**다. 즉 마감
커밋은 **파일 이동과 코드 편집을 같은 커밋에** 담아야 초록이다(리뷰 [R109-3]). 그것이
설계가 노린 성질이다 — 아카이브가 인용을 끊으면 **끊은 사람이 그 자리에서 안다.**

### ③ 음성 대조 — 자를 빼면 같은 편집이 조용하다

②의 사본에서 `CitationAliveTest`(10줄)만 지우고 README 의 단위 수를 841 로 맞췄다
(그 가드가 탐침의 부작용을 무는 것이지 아카이브 편집을 무는 것이 아니다):

```
  → ── Ran 841 tests in 25.578s OK rc=0
```

**끊긴 인용 셋을 안고 초록이다.** ②와 ③의 차이가 곧 이 계획의 산출물이다.

## 천장 — 이 e2e 가 못 재는 것

- **백틱 밖 인용 57자리**(리뷰 [R109-2] 실측 65 결손 중 픽스처 8 제외)는 ②에서도 조용하다.
  이 자가 무는 것은 코드 인용의 **41%** 이고, 나머지는 다음 계획이다.
- `docs/*.md` 안의 결손 44종 · 아카이브 안의 끊긴 인용(`design_history_028.md:3` 의
  `plan_focus-contrast.md` 가 그 예다)은 **범위 밖**이다 — 아카이브는 고치지 않는다.
- 사본은 `git archive HEAD` 라 **추적 안 되는 파일**(`data/`·`docs/reports/`)이 없다. 그 셋은
  이 계획이 안 읽는다.
