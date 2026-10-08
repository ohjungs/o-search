# 계획 113 — `deps-unknown-branches`: 「모르면 실패」를 밟는 갈래 둘에 자를 붙인다

## 문제

컨셉 경량 3·5(「신규 의존성은 사유 한 줄 없이 추가하지 않는다 · 의존성 0 을 유지한다」)를
재는 자는 `tests/test_deps.py` **하나**고, `docs/project.md` 품질 기준 표에서 **유일하게
전수 안에서 저절로 도는 줄**이다. 나머지 여섯 축은 사람이 기억해서 쳐야 한다.

그 자의 판정 `is_allowed`(`tests/test_deps.py:130`)는 설계가 **「모르면 통과가 아니라
모르면 실패」**다(같은 파일 모듈 docstring 판정 규칙 5·6번). 그런데 그 심장을 밟는
갈래가 둘인데 **테스트가 0개**다 — 2026-10-09 반복 691 이 파일을 전문으로 읽어 확인했다:

- **㉠ `except (ImportError, ValueError): return False`** — `find_spec` 자체가 터지는 길.
- **㉡ `if spec is None or not spec.origin: return False`** 의 **`not spec.origin`** —
  네임스페이스 패키지(디렉터리만 있고 `__init__.py` 가 없는 것). `spec is None` 쪽은
  `JudgeTest.test_rejects_third_party` 가 이미 밟는다(이 기계에 `requests` 가 없다).

## 목표 · 기대 결과

둘 다 `return True` 로 뒤집으면 **새 테스트만** 빨개진다. 오늘은 둘 다 뒤집어도 전수가
조용하다 — 즉 **안 깔린 서드파티·네임스페이스 패키지가 초록으로 통과하는 변경을 아무도
안 막는다.** 제품 `src/` 는 0줄이고 판정 동작도 안 바꾼다. **굳히는 자만 더한다.**

## 재현은 이미 쟀다 (저장소 밖 `/tmp` · Python 3.9.6)

- ㉠ `sys.modules` 에 `__spec__ = None` 인 모듈을 심으면 →
  `ValueError: ghostmod.__spec__ is None`
- ㉡ `__init__.py` 없는 디렉터리를 `sys.path` 에 두면 → `spec` 은 있고 `spec.origin is None`

둘 다 표준 라이브러리만으로 결정적이다. **네트워크·설치 없음** (`project.md` 한도).

## 스텝

### 스텝 1 — ㉠ `find_spec` 이 터지는 길 (의존: 없음)

- 건드릴 파일: `tests/test_deps.py` (`JudgeTest` 에 테스트 1개)
- `sys.modules` 를 더럽히므로 `addCleanup` 으로 반드시 되돌린다 — 안 되돌리면 뒤에 도는
  테스트가 그 유령 모듈을 본다(이름순 실행이라 조용히 전염된다).
- **완료 기준**: ① 전수 `867 OK rc=0` ② 변이 `except …: return True` 에서 **새 테스트가
  FAILED** ③ 변이를 되돌리기 **전에** 같은 변이로 전수를 돌려 **새 테스트 말고는 아무도
  안 무는 것**을 센다(갭 증명 — 이 숫자가 계획의 근거다)

### 스텝 2 — ㉡ 네임스페이스 패키지 (의존: 1 — 장부 줄이 스텝 1 의 건수까지 센다)

- 건드릴 파일: `tests/test_deps.py` · `README.md:104` 의 「단위 866건」 장부 줄
- 임시 디렉터리를 `sys.path` 에 넣고 `addCleanup` 으로 뺀다. 이름은 `LOCAL`(저장소가
  스스로 제공하는 이름들)과 겹치지 않는 것을 쓴다 — 겹치면 첫 줄에서 `True` 로 끝나
  이 갈래에 도달하지 못한다.
- **완료 기준**: ① 전수 `868 OK rc=0` ② `README.md` 단위 수를 안 고치면
  `tests/test_readme.py` 가 실측치를 대며 RED ③ 변이 `if spec is None: return False`
  (`origin` 조건 제거)에서 **새 테스트가 빨갛다**

설계 생략 — `design.md` 1절 트리거 0건: 새 파일 0개 · 공개 인터페이스 변경 0 · 파일 2개 ·
되돌리기는 커밋 하나 revert · **갈림길 없음**(두 갈래의 재현 수단이 각각 하나뿐이다).
스텝이 3개 미만인 이유: 테스트 둘이고 둘이 같은 파일의 같은 함수를 민다.

## 하지 않을 것

- **`is_allowed`·`is_stdlib_origin` 의 동작 변경** — 오늘 판정은 옳다(계획 103 리뷰가
  두 판을 실증해서 고쳤다). 이 계획은 자만 붙인다
- **문자열로 감춘 임포트 추적**(`__import__`·`importlib.import_module`) —
  `tests/test_deps.py` 모듈 docstring 의 `ponytail:` 주석이 범위 밖으로 박아 둔 것
- **허용 목록 도입** — 같은 docstring 이 「손으로 민 목록은 옳은 변경을 빨갛게 만든다」로 거부
- **`FILE_FLOOR`·`IMPORT_FLOOR` 조정** — 건수가 늘어도 하한은 하한이다
- **`status.md` 접기 외의 문서 정리** — 접은 것은 계획서를 쓸 자리를 만들기 위한 선행
  작업이고(`ReadBudgetTest` 600), 그 밖의 문서는 안 건드린다

## e2e 시나리오 (계획 단계에 확정 — 구현에 맞춰 낮추지 않는다)

1. **실제 재발 경로 재연** — `src/websearch/` 의 파일 하나에 **㉡ 모양의 임포트 한 줄**을
   심고(이 기계에 깔린 네임스페이스 패키지, 없으면 `sys.path` 에 심은 것) 전수를 돌리면
   `DependencyZeroTest` 가 **자리와 이름을 대며** RED 다. 되돌린다.
2. **음성 대조** — 두 갈래를 각각 `return True` 로 되돌린 상태에서 전수를 돌려
   **새 테스트 둘 말고 무는 자가 0개**임을 센다. 오늘 이 자리를 지키는 것이 이 둘뿐이라는
   존재 증명이고, 1번의 RED 가 새 테스트 덕인지 원래 있던 자 덕인지를 가른다.
3. 1순위 전수 **868 OK rc=0** + e2e **18종 rc=0**.
