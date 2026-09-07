# 계획: `project.md` 가 인용한 코드 상수가 낡는 것을 기계로 막는다

- **슬러그**: `project-const-drift`
- **브랜치**: `loop/project-const-drift`
- **근거**: 탐색 실측 2026-09-07 — `docs/project.md:188-189` 가 `indexer.MAX_PASSAGE_HTML`
  **= 35,000자**라고 적어 두었는데 실제 값은 `src/websearch/indexer.py:92` 의
  **2,000,000** 이다. 계획 74 가 자를 바이트에서 태그로 갈면서(`MAX_PASSAGE_TAGS = 3_000`)
  코드와 `tests/test_indexer.py` 는 고쳤지만 `project.md` 는 안 고쳤다
  (`git log -- docs/project.md` 의 마지막 커밋은 계획 58 의 `724d8c8`).
  digest `[6]` 「문서를 입력으로 읽는 검사가 한 벌은 있어야 한다」가
  **「같은 부류로 아직 안 잰 것」으로 이 자리를 지목해 두었다.**
- **시작**: 2026-09-07 20:20

## 목표

`docs/project.md` 는 루프가 **매 반복 읽는 네 파일 중 하나**이고, 「품질 기준」 절은
그 판단의 눈금이다. 지금 그 눈금 한 줄이 거짓이다 — 캡의 **값**(35,000 대 2,000,000)도
**단위**(자 대 태그)도 틀렸고, 거기서 유도한 숫자(최악 350ms · 동결 35,000×10 ·
상한 1.4286 ms/1000자)가 전부 딸려 틀렸다. 계획 57·58 은 이 자리를 **손으로** 맞췄고
(`e6f375c` 「기록 자리 둘을 오늘 값으로 맞춘다」) 계획 74 는 잊었다 — 세 번째다.

끝나면 ① 그 절이 태그 축의 오늘 값을 적고 ② `tests/test_docs.py` 가 `project.md` 의
**상수 인용을 실제 값과 대조**해, 다음에 상수가 움직이면 문서가 조용히 낡는 대신
빨개진다. 규율이 아니라 기계로 옮기는 것이다(`digest` 의 `index-step-sync` 선례).

## 하지 않을 것

- **파생 숫자는 안 잰다** — 최악 ms · 계수 · p95 는 코드에서 읽을 수 없고 재려면 측정을
  테스트 안에 넣는 것이라, `project.md` 자신이 경고하는 흔들리는 검사가 된다.
  상수 값이 **닻**이고, 닻이 움직이면 사람이 그 문단을 다시 읽는다.
- **`indexer.MAX_PASSAGE_TAGS`·`MAX_PASSAGE_HTML` 의 값 자체** — 계획 74 가 정한 값이고
  이 계획은 기록만 맞춘다. `src/` 는 0줄이다.
- **`README.md`·`digest.md` 의 숫자** — 검사는 `project.md` 한 파일만 문다. 넓히는 것은
  이 검사가 실물에서 값을 낸 뒤의 별개 판단이다.
- **괄호 표기 인용**(`fetcher.MAX_BYTES`(2MB)) — 오늘 참이고, `= N` 형태만 문다.

## 설계

- **생략** — 새 모듈 0 · 공개 계약 무변 · `src/` 0줄 · 파일 2개(`docs/project.md` ·
  `tests/test_docs.py`) · 되돌리기 자유. `test_docs.py` 에 이미 `iter_gap`·`step_gap`·
  `strike_gap`·`verdict_gap` 넷이 같은 모양으로 살아 있어 **고를 갈림길이 없다**
  (ponytail 사다리 2번 — 저장소에 있는 패턴을 그대로 쓴다). `design.md` 1절 트리거 미해당.

## 스텝

### 1. 낡음 판정을 순수 함수로 세우고 갈래를 못박는다
- **완료 기준**: `tests/test_docs.py` 에 `const_gap(project_text)` 와 `ConstGapTest`.
  `` `mod.CONST` `` 뒤에 `= 숫자` 가 붙은 인용만 물고, 값이 다르면 그 줄을 돌려준다.
  갈래 단언: ① 일치하면 조용하다 ② 값이 다르면 보고한다 ③ `= N` 이 없는 인용
  (`design_check.PAIRS` · `fetcher.MAX_BYTES`(2MB))은 안 문다 ④ 없는 상수 이름은
  **조용히 넘기지 않고** 보고한다 ⑤ 쉼표(`2,000,000`)와 굵게(`**= 3,000**`)를 읽는다.
  `PYTHONPATH=src python3 -m unittest discover -b tests` 통과.
- **건드릴 파일**: `tests/test_docs.py`
- **의존**: 없음
- **상태**: 완료

### 2. 살아 있는 `project.md` 에 물린다 — 오늘은 빨개야 한다
- **완료 기준**: `ProjectConstTest.test_project_cites_live_constants` 추가.
  **먼저 실패하는 것을 눈으로 본다** — 실패 메시지가 `indexer.MAX_PASSAGE_HTML`
  35,000 ≠ 2,000,000 을 가리켜야 한다. 그것이 오늘의 근거를 재현한 증거다.
  이 스텝은 RED 로 끝난다(스텝 3 이 초록으로 만든다).
- **건드릴 파일**: `tests/test_docs.py`
- **의존**: 1
- **상태**: 대기

### 3. 「품질 기준」 절을 태그 축의 오늘 값으로 다시 쓴다
- **완료 기준**: `docs/project.md:188` 이하 문단이 `MAX_PASSAGE_TAGS = 3,000` ·
  최악 모델 **120ms**(예산 24%) · 동결 `8,000 × 10` · 계수 상한 `500/(캡k태그 × 건수)`
  = **16.67 ms/1000태그** 를 적는다 — 숫자는 전부 `tests/test_indexer.py:835-872` 와
  계획 74 실측(`docs/e2e/passage-prefer-body/result.md`)에서 가져오고 **추측하지 않는다.**
  `근거 문단 기준선`(:177) 의 p95 는 **오늘 다시 재서**(`e2e/passage_eval.py`) 적는다.
  전수 통과 + 스텝 2 의 검사가 초록.
- **건드릴 파일**: `docs/project.md`
- **의존**: 2
- **상태**: 대기

## e2e 시나리오

1. `MAX_PASSAGE_TAGS` 를 3,000 → 4,000 으로 바꾸는 변이를 심는다 → 전수를 돌리면
   **문서 검사가 빨개지고** 메시지가 `project.md` 의 어느 줄이 낡았는지 가리킨다.
   되돌리면 초록. (계획 74 가 실제로 밟은 그 길을 재현한다)
2. 상수 이름을 `MAX_PASSAGE_TAGS` → `PASSAGE_TAG_CAP` 로 바꾸는 변이 → 검사가
   「없는 상수를 인용한다」로 빨개진다(조용히 넘기지 않는다).
3. 루프가 평소처럼 `docs/project.md` 를 읽었을 때 「품질 기준」 절의 캡 문단이
   `indexer.py` 와 한 글자도 안 어긋난다.

## 기록

- 2026-09-07 스텝 1 완료 — `const_gap()`·`_const_value()` + `ConstGapTest` 7건.
  임포트가 아니라 소스의 정수 리터럴을 읽는다(인용 대상이 `e2e/` 에도 살 수 있다).
  변이 4종 전부 죽음. 단위 655 → 662건, README 의 건수 가드가 그 자리에서 울어 함께 고쳤다.
