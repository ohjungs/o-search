# e2e — 계획 113 `deps-unknown-branches` (2026-10-09 반복 696)

**새 e2e 파일 0개.** 이 계획의 산출물이 테스트라 e2e 는 「실물에서 재발 경로를 재연하는 것」이고,
그 재연은 **전수 러너와 실물 네임스페이스 패키지 하나**로 끝난다(사다리 1번 — 새 시나리오 파일을
만들지 않았다). 판정은 전부 `scripts/verdict.sh` 의 마지막 줄로 읽었다.

## 시나리오 1 — **실제 재발 경로 재연** · 통과

이 파일의 전제가 「`import requests` 한 줄이 들어오는 날」이므로 **합성 픽스처가 아니라 실물**로 쳤다.
이 기계의 site 디렉터리에 `__init__.py` 없는 `bin` 디렉터리가 있고 `find_spec("bin")` 이
**스펙은 주고 `origin` 은 `None`** 이다 — ㉡ 갈래를 타는 **실물 서드파티 네임스페이스 패키지**다.
`bin` 은 `src`·`tests`·`e2e` 바로 밑에 없어서 `LOCAL` 로 먼저 통과하지도 않는다(실측 `grep -x` 0건).

`src/websearch/flags.py:1` 에 `import bin` 한 줄을 심고 전수를 돌렸다:

```
FAIL: test_no_third_party_import (test_deps.DependencyZeroTest)
AssertionError: Lists differ: [] != ['flags.py:1 import bin']
  … : 컨셉 경량 3·5 는 의존성 0 이다. 추가하려면 계획서에 사유 한 줄이 먼저다: flags.py:1 import bin
── Ran 868 tests in 22.573s FAILED (failures=1) rc=1
```

**자리와 이름을 대고, 어긴 사양 조항까지 인용한다.** 무는 자는 **하나**다.

## 시나리오 2 — **음성 대조가 존재 증명이다** · 통과 (이 계획의 핵)

시나리오 1 의 RED 가 **원래 있던 자 덕인지 이 계획이 세운 자 덕인지**를 가른다.
`import bin` 을 **그대로 심어 둔 채** ㉡ 갈래만 뒤집었다(변이 M3 — `if not spec.origin: return True`):

```
FAIL: test_rejects_namespace_package (test_deps.JudgeTest)
── Ran 868 tests in 22.607s FAILED (failures=1) rc=1
```

**`DependencyZeroTest` 가 초록으로 돌아섰다** — 실물 서드파티 임포트가 심긴 트리에서 「의존성 0」
판정이 통과한다. 그 한 줄을 뒤집는 것을 막는 자는 **이 계획이 세운 테스트 하나뿐**이고,
반복 693 이 센 「갭 0」이 **합성 변이가 아니라 실물 임포트 위에서** 재확인됐다.

## 시나리오 3 — 전수 + e2e 명부 · 통과

심은 줄과 변이를 **사본 교체로** 되돌린 뒤(`git restore` 는 안 썼다 — 반복 686 의 자리):
`git status --short` **빈손** · 전수 **868 OK rc=0** · e2e **18종 전부 `rc=0`**(래퍼의 마지막 줄로 판정).

## 못 잰 것

- **린트·타입체크는 없다**(`project.md`) — 미검증.
- `perf_*` 는 안 돌렸다. 이 계획은 `src/` 를 0줄 고쳤으므로 처리량·메모리 축은 같은 트리다.
- `ImportError` 팔은 여전히 무증인이다 — `digest.md` 후보 `[4]` 에 도달성 실측과 함께 등재.
