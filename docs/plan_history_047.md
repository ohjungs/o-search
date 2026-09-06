# 계획 61 — `iter-gap-cover`

`tests/test_docs.py` 의 `IterationSyncTest` 는 `docs/metrics.md` 의 `| 반복 |` 과
`docs/status.md` 의 `iteration:` 을 대조하는데, 그 **판정 자체를 재는 것이 0개**다.
실물 두 문서가 늘 맞춰져 있어서 판정을 통째로 지워도 전수 614건이 초록이다.

- **근거**: `docs/digest.md` `## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 의 `[6]`
  「`IterationSyncTest` 의 «판정» 도 실물 문서 위에서만 돈다」(2026-09-06 계획 60
  테스트 phase 가 등재). 그 항목이 적어 둔 **여는 조건은 「반복 축 검사를 손대는 날」**
  이고, 이 계획이 곧 그날이다 — 계획 60 이 그것을 미룬 이유는 「직교 편집」 하나였고
  (계획 60 계획서 5절이 반복 축을 범위 밖으로 그었다) 계획 60 이 반복 355 에서
  DONE 으로 닫혔으므로 그 이유는 오늘 없어졌다.
- **기점**: `loop/passage-cost-band` 의 계획 60 마감 커밋(`a8a052a`). 고칠 파일
  `tests/test_docs.py` 는 `origin/main`(`d1fe3e9`)에 **`step_gap` 이 0건**이라
  (`git show origin/main:tests/test_docs.py`) 이 계획이 흉내 낼 관용구가 거기 없다 —
  `main` 에서 새로 따면 안 된다. 브랜치는 계획 57·58·59·60 과 같이 쌓아 둔 채로 간다.
- **원격**: `origin/main` 은 계획 56(`d1fe3e9`)까지고 열린 PR 은 0건이다
  (2026-09-06 반복 356 이 `git ls-remote origin main` 으로 다시 읽었다). 병합은 사람 몫이다.

## 1. 문제 · 목표 · 기대 결과

**문제.** `IterationSyncTest.test_metrics_and_status_agree`(`tests/test_docs.py:201`)는
정규식 둘로 두 문서에서 수를 뽑아 대조한다. 정규식 **둘**은 `IterationPatternTest` 가
합성 표로 붙들지만, 그 위에 얹힌 **판정**(가드 둘 + 비교 하나)은 실물 문서 위에서만
돌고 실물은 늘 맞춰져 있다. 그래서 판정을 무력화하는 변이가 전부 조용히 산다.
계획 60 이 스텝 축에서 닫은 것과 **글자 그대로 같은 구멍이고 축만 다르다.**

**목표.** 판정을 `iter_gap(status_text, metrics_text)` **순수 함수**로 빼고, 그 갈래를
합성 문자열로 밟는 `IterGapTest` 를 세운다. 저장소의 기존 관용구 그대로다 —
`done_section`·`indexed` + `ArchiveMatchTest`(계획 44) · `step_gap` + `StepGapTest`(계획 60).
`IterationSyncTest` 는 실물 두 문서를 읽어 `iter_gap` 을 부르는 세 줄로 남는다.

**기대 결과.** 제품 `src/` **0줄** · 고치는 파일 **`tests/test_docs.py` 하나**
(+ 단위 건수가 늘면 `README.md` 러너 줄 한 줄) · 2절 변이 넷이 **4/4 사망**.

## 2. 착수 탐침 — 오늘 다시 쟀다 (2026-09-06 · 반복 356)

`digest [7]`「기록된 답을 실행 전에 다시 재라」의 **열두 번째 적용**. 저장소 파일은
한 바이트도 안 고치고 `IterationSyncTest` 의 메서드를 **메모리에서** 갈아 끼워
전수를 돌렸다(양성 대조로 패치 대상 모듈이 `tests/test_docs.py` 임을 먼저 확인했다).

| 변이 | 오늘 실측 | 판정 |
|---|---|---|
| **대조군(무변이)** | `Ran 614 · OK` | 기준선 |
| **M1 대조를 자기비교로**(`a.group(1), b.group(1)` → `b.group(1), b.group(1)`) | `Ran 614 · 죽은 단언 0` | **생존 — 기록된 그대로** |
| **M2 `assertIsNotNone(a)` 가드 삭제** | `Ran 614 · 죽은 단언 0` | **생존 — 기록에 없던 갈래** |
| **M3 `assertIsNotNone(b)` 가드 삭제** | `Ran 614 · 죽은 단언 0` | **생존 — 기록에 없던 갈래** |
| **M4 판정 통째 삭제**(메서드를 `pass` 로) | `Ran 614 · 죽은 단언 0` | **생존 — 이 계획의 표적** |
| M5 `ITER_ROW` 를 `^\| 반복[^\|]*\| ([0-9]+) \|` 로 넓힘 | `Ran 614 · failures=1`(`IterationPatternTest.test_only_the_exact_row_matches`) | 사망 — 정규식 축은 이미 닫혀 있다 |
| 양성 대조(메서드를 `self.fail()` 로) | `Ran 614 · failures=1`(`IterationSyncTest`) | 변이가 실제로 심어졌다(`digest [8]`) |

**기록된 답이 오늘 절반 틀렸다.** `digest [6]` 은 8점이 아닌 이유로 **①「갈래가
하나뿐이다 — 살아남는 변이도 «대조 무력화» 하나뿐이다」**를 적었는데, 실측은 **넷이
살아남는다**. 썩을 표면은 「대조」 하나가 아니라 **셋**(`a` 없음 · `b` 없음 · 대조)이고,
그 셋이 곧 이 계획이 밟을 갈래다. 이유 **②「어긋나면 사람 눈에 바로 보인다」**는
그대로 참이라(계획 60 이 스텝 축만 연 비대칭이 여기 있다) 점수는 6→**7**로만 올린다.

## 3. 스텝 — 1개

**스텝 1 — 판정을 `iter_gap` 으로 빼고 `IterGapTest` 로 갈래를 밟는다.** 의존: 없음.
예상 파일: `tests/test_docs.py` · (건수가 늘면) `README.md`.

`tests/test_docs.py:88` 의 `step_gap` **바로 위 또는 아래**에 `iter_gap(status_text,
metrics_text)` 를 세운다 — 인자 순서는 `step_gap` 과 같게 `status` 를 먼저 받는다.
반환은 어긋난 자리 한 줄, 어긋남이 없으면 `None`(같은 계약). 갈래 셋은 오늘 메서드가
이미 가진 것 그대로다: `ITER_ROW` 매치 없음 · `ITER_LINE` 매치 없음 · 두 수가 다름.
`IterationSyncTest.test_metrics_and_status_agree` 는 두 파일을 읽어 `iter_gap` 을 부르고
`assertIsNone(gap, gap)` 하는 세 줄로 줄인다(`StepSyncTest:231` 과 같은 모양).
`IterGapTest` 는 합성 문자열로 갈래 넷(초록 하나 + 위 셋)을 밟는다.

**스텝이 하나인 이유**(`rules/plan.md` 3절): 산출물이 함수 하나와 그것을 밟는 테스트
클래스 하나라 되돌리기가 커밋 하나 revert 다. 쪼개면 중간 상태가 「함수는 있는데
아무도 안 부른다」라 검증 가능한 노드가 아니다.

## 4. 완료 기준 — 전부 검증 가능

1. **2절 M1~M4 가 4/4 사망**한다. 같은 메모리 변이 하네스로 다시 재고, 각 변이가
   죽이는 단언이 **의도한 그것**인지 이름으로 확인한다(변이 하나가 전부를 죽이면
   갈래를 못 가른 것이다).
2. **양성 대조** — `iter_gap` 이 어떤 입력에도 `None` 을 돌려주게 비틀면 `IterGapTest`
   에서 **셋 이상**이 죽는다(`StepGapTest` 의 대조군과 같은 자리).
3. `ITER_ROW`·`ITER_LINE` 을 넓히는 M5 는 **여전히 `IterationPatternTest` 가** 죽인다 —
   이 계획이 그 축의 감지력을 낮추지 않았다는 증거다.
4. 전수 `PYTHONPATH=src python3 -m unittest discover -b tests` 가 **맨몸**으로
   `OK` · `rc 0`(파이프·리다이렉션 없음). 건수가 614 에서 늘면 `README.md` 러너 줄의
   단위 건수를 같은 커밋에서 함께 고치고 `tests/test_readme.py` 가 초록이다.
5. 제품 `src/` **0줄** — `git diff --stat <기점> HEAD -- src/ e2e/ docs/specs/ data/`
   가 빈손이고 `data/crawl.db` sha256 무변.
6. `docs/status.md` 의 `step` 과 `docs/index.md` 61번 행의 스텝 칸이 매 커밋 함께
   움직인다 — 계획 60 이 세운 `StepSyncTest` 가 이 계획 위에서 실제로 도는 것이
   그 검사의 두 번째 시험대다.

## 5. 하지 않을 것

- **`ITER_ROW`·`ITER_LINE` 정규식을 안 건드린다.** 2절 M5 가 그 축은 이미 닫혀
  있음을 보였다(`IterationPatternTest`). 넓히지도 좁히지도 않는다
- **`step_gap` 과 `iter_gap` 을 하나로 합치지 않는다.** 두 축은 갈래가 다르다 —
  스텝 축에는 `plan: null` 갈래와 「슬러그로 행 집기」가 있고 반복 축에는 둘 다 없다.
  합치면 인자로 갈래를 켜고 끄는 물건이 되고, 그것은 없는 일을 만드는 것이다
  (ponytail 사다리 1번). 두 함수가 나란히 있는 것이 오늘의 관용구다
- **`docs/metrics.md`·`docs/status.md` 의 내용을 안 고친다** — 검사가 문서에 맞추는
  것이 아니라 문서가 이미 맞다(2절 대조군 초록). 어긋남을 만들어 넣지 않는다
- **`StepSyncTest`·`StepGapTest`·`ArchiveMatchTest` 를 안 건드린다** — 직교 편집
- 새 e2e 파일을 안 만든다(`rules/e2e.md` 3절 — 프로세스 밖에서 달라지는 것이 0)
- 스키마·마이그레이션·재색인·새 의존성·`docs/specs/` **0**

## 6. 설계 생략 사유

`rules/design.md` 1절 트리거에 **하나도 안 걸린다** — 새 모듈 없음(기존 파일 안의
모듈 수준 함수 하나) · 제품 공개 인터페이스 무변 · 데이터 구조 무변 · 파일 1개 ·
되돌리기가 커밋 하나 revert · 보안 무관.

**대안이 갈리지 않는 이유가 계획 60 에 있다.** 「판정을 순수 함수로 빼고 합성
문자열로 갈래를 밟는다」는 이 저장소가 같은 축에서 **어제 갈라 놓은 결정**이다
(`docs/design_history_046.md` 안 D · `ArchiveMatchTest` 는 그전 선례). 떠오른 다른
대안 둘은 이미 죽어 있다: ① `step_gap` 과 합치는 일반화 → 5절 두 번째 줄이 거부 ·
② 실물 대신 임시 디렉터리에 가짜 `docs/` 를 깔고 `DOCS` 를 패치 → 산출물이 같고
파일 입출력만 늘어 `StepGapTest`(합성 문자열)의 선례보다 비싸다.

## 7. 위험

- **거울 테스트의 유혹** — `IterGapTest` 가 `iter_gap` 의 구현을 베껴 쓰면 변이가 둘을
  함께 고칠 때 안 죽는다(`rules/test.md`). 기대값은 **문자열 안의 수**로 적고
  구현 상수를 참조하지 않는다
- **갈래를 못 가르는 실패** — 2절 M2·M3 은 서로 다른 가드라 각각 **다른** 단언이
  죽어야 한다. 하나가 넷을 다 죽이면 `IterGapTest` 가 갈래별로 안 나뉜 것이고,
  그것을 완료 기준 1 이 이름으로 잡는다
- **건수 드리프트** — 새 테스트 메서드가 늘면 `README.md` 의 단위 건수가 같은 커밋에서
  안 움직이는 사고가 이 저장소에 이미 있다(`digest ## 반복 실패`). 완료 기준 4 가
  `tests/test_readme.py` 로 그것을 잡는다
