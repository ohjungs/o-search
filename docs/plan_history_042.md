# 계획 56 — `loader-isolation`

**`-k` 를 붙이면 항상 죽는 테스트가 하나 있다.** 계획 50 이 러너의 출력 문제를
`-b` 로 닫은 뒤, 전수를 안 돌리고 좁혀 보는 **유일하게 남은 정당한 수단**이 `-k` 인데
그 자리에 함정이 하나 서 있다. 오늘 다시 재서 확인했다.

```
PYTHONPATH=src python3 -m unittest discover -b -s tests -k Readme
→ AssertionError: Tuples differ: (605, 21) != (5, 21)
  "README 의 (단위, e2e) 숫자가 실제와 다르다 — 실제는 (5, 21)"
rc=1
```

**단순 오탐이 아니라 함정이다.** 실패 메시지가 「실제는 (5, 21)」이라고 말해서, 이것을
믿은 사람은 `README.md` 의 `## 검증` 에 `단위 5건` 을 적는다. 그러면 전수(`-k` 없음)가
RED 로 뒤집히고, 고친 사람은 자기가 방금 무엇을 깨뜨렸는지 모른다.

- **슬러그**: `loader-isolation`
- **브랜치**: `loop/loader-isolation`
- **기점**: `main`(`fe4dd0d61018a04e52fc077273c6ef70c57f7011`) — 코디네이터가 PR #10 을
  병합해 계획 55 의 코드·문서가 전부 원격에 들어왔고, 이 반복이 회전시킬 문서는
  아카이브 두 벌뿐이라 `main` 에서 따는 것이 집안일을 안 늘린다.
  `git fetch origin` · `git ls-remote origin main` 으로 직접 읽었다. 열린 PR 0건.
- **phase**: 개발 (설계 없음 — 6절)
- **스텝**: 1개
- **시작**: 2026-09-05 (반복 327)

## 1. 문제 · 목표 · 기대 결과

### 문제

`tests/test_readme.py` 의 `ReadmeTest.test_verification_counts_match_reality` 는
README 가 자랑하는 단위 테스트 건수를 **직접 세어** 대조한다. 세는 줄이 이것이다.

```python
actual_unit = unittest.defaultTestLoader.discover(str(TESTS_DIR)).countTestCases()
```

`unittest.defaultTestLoader` 는 **모듈 수준 싱글턴**이고, `python3 -m unittest ... -k P`
는 그 싱글턴의 인스턴스 속성 `testNamePatterns` 를 `["*P*"]` 로 **바꿔 놓는다**
(CPython `Lib/unittest/main.py`). 그래서 검사 안에서 다시 도는 `discover()` 가 바깥
러너의 필터를 물려받아, 「저장소의 단위 테스트 총수」가 아니라 **「지금 필터에 걸린
테스트 수」**를 센다. 검사가 재려던 값이 관측 도구에 오염된다.

탐침으로 그 상태를 손으로 만들어 두 세는 법을 나란히 쟀다(저장소 파일 무변):

| 상태 | `defaultTestLoader` | `TestLoader()` 새 인스턴스 |
|---|---|---|
| 필터 없음 | 605 | 605 |
| `testNamePatterns = ["*Readme*"]` | **5** | **605** |

### 목표

`-k` 로 좁혀 돌아도 이 검사가 **저장소 전체의 단위 테스트 수**를 세게 한다.
전수 실행의 값(605)은 한 건도 안 움직인다.

### 기대 결과

`-k Readme` 로 좁혀도 RED 가 아니라 GREEN 이고, 전수는 그대로 `605 OK · rc 0`.

## 2. 근거

`docs/digest.md` 의 `## 다음 계획 후보 (테스트 phase 갭)` 항목 **`[5]`③**
(「`-k` 를 붙이면 `test_verification_counts_match_reality` 가 항상 RED」).
탐색 6순위. **오늘 재측정했다** — 위 두 블록이 그 값이다.

기록된 처방은 *"패턴을 잠시 비웠다 되돌리는 두 줄"*(전역 저장·복원)이었는데,
탐침이 **더 작은 답**을 냈다: 새 인스턴스 하나면 전역을 만질 일 자체가 없다.
저장소의 여덟 번째 「기록된 답을 실행 전에 다시 재라」 사례다.

## 3. 스텝 (1개 — 고칠 것이 한 줄이라 쪼갤 자리가 없다)

### 스텝 1 — 세는 자를 러너의 필터에서 떼어낸다 · 의존: 없음

`tests/test_readme.py` 의 위 한 줄에서 `unittest.defaultTestLoader` 를
`unittest.TestLoader()` 로 바꾼다. 왜 새 인스턴스여야 하는지는 주석 한 줄로 남긴다
(다음 사람이 「짧으니 되돌리자」로 지우지 않게).

**호출처는 저장소 전체에 이 한 곳뿐이다** — `defaultTestLoader` · `TestLoader` ·
`.discover(` 를 `tests/` · `e2e/` · `src/` 에서 세어 확인했다. 공유 지점 수정이라
같은 함정의 형제 호출자가 남지 않는다.

**건드릴 파일(예상)**: `tests/test_readme.py` 한 개, 제품 `src/` **0줄**.

## 4. 완료 기준 (전부 실행해서 본다)

1. `PYTHONPATH=src python3 -m unittest discover -b -s tests -k Readme` → `OK` · rc 0.
2. `PYTHONPATH=src python3 -m unittest discover -b -s tests` → `Ran 605 tests` · `OK` · rc 0.
   (건수가 605 에서 움직이면 새 테스트를 안 넣었는데 움직인 것이므로 멈춘다.)
3. **고친 줄이 실제로 그것을 막는지 본다** — 검사 안에서 전역 패턴을 손으로 세팅해도
   센 값이 605 로 남는지 확인한다. 되돌리면(다시 `defaultTestLoader`) 그 확인이 죽는다.
4. `README.md` 의 `단위 605건` 은 **한 글자도 안 고친다**. 고쳐야 한다면 진단이 틀린 것이다.
5. `git status --short` 에 `tests/test_readme.py` 외 코드 파일 0개.

## 5. 하지 않을 것

- **`README.md` 의 숫자 수정** — 이 계획은 숫자가 틀렸다는 주장이 아니라, 세는 자가
  오염된다는 주장이다. 605 는 맞는 값이다.
- **`RUNNER_LINE` · `BUFFERED` 등 같은 파일의 다른 정규식·검사** — 오늘 오탐 신호 0.
- **`unittest` 러너 명령·`project.md` 의 검증 명령 변경** — 범위 밖.
- **새 e2e 파일** — 프로세스 경계에서 재는 것이 없다. 이 함정은 러너 인자 하나로
  단위 스위트 안에서 완전히 재현된다.
- **`docs/specs/` · `data/crawl.db` · 스키마·마이그레이션** — 무접촉.
- **다른 테스트의 전역 상태 점검(감사)** — 호출처가 한 곳뿐임을 이미 셌다. 넓히면
  이 계획이 아니라 별건이다. 필요가 보이면 `digest.md` 후보로 남긴다.

## 6. 설계 판정 — **필요 없다**

대안이 갈리지 않는다. 「전역을 저장·복원한다」와 「새 인스턴스를 쓴다」 중 후자가
엄격히 작고(한 낱말 vs 두 줄), 전역을 **아예 안 만지므로** 실패 경로에서 복원을
빠뜨릴 자리도 없다. 파일 1개 · 한 줄 · 보안 무관 · 제품 0줄이라 설계 트리거 0.

## 7. 위험

- **최대 위험은 「고쳤는데 아무것도 안 막는다」** — 그래서 완료 기준 3 이 변이로 잰다.
- 전수 건수 605 가 변하는 것. 새 인스턴스는 필터만 안 물려받고 탐색 규칙은 같아서
  탐침에서 605 = 605 였다. 그래도 완료 기준 2 로 눈으로 본다.
