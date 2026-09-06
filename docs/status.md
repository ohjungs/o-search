---
signal: DONE
phase: e2e
step: 0/0
attempt: 0
iteration: 381
updated: 2026-09-06
ctx: 56
night_iterations: 187
night_red: 2
night_retries: 4
plan: null
---

## 현재 상태

**계획 65 `readme-band-cover` 를 e2e 1/1 로 닫았다 — 통과 · 완료 기준 10/10 · 활성 계획 0.**
e2e 21종을 전부 맨몸으로 다시 돌려 **rc 0 · 21/21** 이고, 전수는 `Ran 623 tests in
15.787s` · `OK` · rc 0 이다. 결과는 `docs/e2e/readme-band-cover/result.md`.

## e2e 결과

**새 e2e 파일 0개를 「해당 없음」으로 넘기지 않고 근거 셋으로 쟀다**(`rules/e2e.md` 3절) —
프로세스 밖 변화 0(`git diff --stat 44b4eb8 HEAD -- src/ e2e/ docs/specs/ data/` **빈손**) ·
새 클래스가 `tests/` 안이라 네 수단(웹 UI·HTTP API·CLI·라이브러리) 어디에도 걸 곳이 없다
(`src/` 에 `tests` 를 import 하는 줄 **0건**) · 새로 만들면 전수 명령과 겹쳐 「1회만」이
깨진다. **이 계획은 반대 방향으로 한 칸 더 걸린다** — 검사가 `e2e/*.py` 다섯을 임포트하지만
그 방향은 «테스트 → e2e» 라 제품이 테스트를 부르는 자리는 여전히 0 이다.

**대신 사용자 관점 검증을 실물 사본에서 아홉 판 돌렸다.** 이 가드의 사용자는 **README 합격선을
손으로 고치거나 `e2e/*.py` 상수를 튜닝하는 사람**이라, 앞 phase 의 메모리 변이 서른셋이 아니라
**진짜 파일 편집**으로 다시 밟았다. 한쪽만 고친 셋(U1 문서 80%→85% · U2 상수 `BUDGET_MS`
300→250 · U3 환산 축 JS 50→100KB)과 표에서 행을 지운 U7 이 **4/4 사망**하고, 양쪽을 함께
옮긴 정당한 튜닝(U4 크롤 5→6)과 표기만 바꾼 편집(U6 `3.0`→`3`)은 **안 막는다**. 죽는 자리가
전부 `subTest` 라벨까지 맞고 실패 메시지가 양쪽 값과 배율을 다 찍는다.

**U7 이 U1~U3 과 다른 단언에서 죽는 것이 요점이다** — 표에서 행이 사라지면 대조할 값 자체가
없어지는데, 그 자리를 「찾을 게 없으니 통과」로 넘기지 않는다(`1 != 0`).

## e2e 가 잡은 것 — 계획서의 「안 잰다」 주장 하나

**U8 이 조용했다.** README 표 셋째 칸의 측정기 파일 이름을 `e2e/quality_eval.py` →
`e2e/quality_evals.py` 오타로 만들어도 `Ran 6 · OK · rc 0` 이다. 계획 65 5절은 그 축을
「**새 표가 모듈을 임포트하므로 이름이 틀리면 그 자리에서 터진다**」로 적고 잘랐는데
**뒤 절반이 거짓**이다 — `QUALITY_BAND` 가 임포트하는 것은 튜플 **자신의 리터럴**
(`"quality_eval"`)이지 README 셋째 칸이 아니고, `E2E_COUNT` 대조는 파일 **개수**만 센다.
`MODULE` 정규식은 `-m websearch.<모듈>` 형태만 잡아 표의 백틱 경로를 안 본다.
**이 파일이 존재하는 이유(『README 가 없는 모듈 `websearch.cli` 를 안내한 채 푸시됐다』)와
정확히 같은 모양의 구멍**이 표의 셋째 칸에 남아 있다.

**오늘 안 고친다** — 계획 5절이 범위 밖으로 자른 자리라 e2e phase 가 스스로 넓히면 카파시
3번(직교 편집)이다. `digest [7]④` 로 처방까지 등재했다. 완료 기준에는 영향이 없고(어느
기준에도 안 들어 있다) 오늘 실물 아홉 칸은 전부 실재한다.

**U5 는 알려진 천장이지 결함이 아니다** — 수치 `4.5` 가 맞는데 문구만 다듬어도 빨개진다.
`tests/test_readme.py:47-49` 가 명시적으로 고른 쪽이고(문구를 통째로 담으면 거울이 된다),
고치는 법이 실패 메시지에 정규식으로 찍힌다.

## 검증

전수 **맨몸** `Ran 623 tests in 15.787s` · `OK` · **rc 0**.
e2e 21종 개별 실행 **전부 rc 0**. `ls e2e/*.py` **21개** ↔ `README.md:105` 「e2e 시나리오 21종」 ·
`README.md:104` 「단위 623건」 ↔ 실제 623.
기준선 **8축 전부 회귀 0** — 정확도 100.0% · `/passages` p95 1.48ms · `/search` p95 8.81ms ·
ko 20/20 · en 19/20 · 매치 14.0/11/28 · 크롤 [열림] 10.23 [차단] 10.24 · JS 0 B · 최저 대비 4.87:1 ·
숨은 텍스트 0/5. 움직인 것이 없어 `docs/project.md` 를 한 줄도 안 갱신했다.
범위 무접촉 — `git diff --stat 44b4eb8 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변.

## 다음

**활성 계획 0 — 다음 반복은 계획 phase 다.** 후보 탐색은 이 반복에서 하지 않았다.
`digest ## 다음 계획 후보 (테스트 phase 갭)` 의 `[7]` 이 이번 phase 로 **①③④ 세 갈래**가 됐다
(②는 리뷰 380 이 닫았다). 넷째가 오늘 새로 붙은 것이고, ①(표 행 수를 `len(QUALITY_BAND)` 와
대조)과 함께 **표 구조 축 하나로 묶여 한 계획이 될 수 있다**.

## 한도

- 병합은 사람 몫이다 — 계획 57~65 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지). 전수·e2e 21종·
  사용자 편집 9판을 전부 맨몸으로 돌리고 판정 줄을 눈으로 봤다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 편집은 저장소 밖에서만 — `mktemp -d` 사본. 매 판 뒤 `git status --porcelain` 빈손이고
  실물 `README.md`·`e2e/*.py` 는 이 phase 에서 **0줄** 움직였다.
- `night_iterations` 187 그대로다(대화형 반복이라 안 올린다).
- `docs/digest.md` 는 **200줄 정각**이다 — 완료 한 줄을 더하면서 가장 오래된 완료 항목
  하나(계획 60 `index-step-sync` · 원본 `plan_history_046.md`)를 지워 정각을 지켰다.
- `docs/history_current.md` 는 이번 append 뒤 **255줄**(항목 6/20)이라 회전은 아직 아니다.
  다음 회전 번호는 `history_067.md` 다.
- 계획서를 `docs/plan_history_051.md` 로 아카이브했다(`ArchiveIndexTest` 는 `history_*.md`
  만 명부로 재므로 `digest` 명부 갱신은 필요 없다).
