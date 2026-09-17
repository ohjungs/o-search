# e2e — 계획 103 `dep-zero` (2026-09-17 · 반복 607)

계획서대로 **별도 e2e 파일을 만들지 않았다** — 산출물이 단위 검사 하나라
**변이(가짜 임포트)가 이 계획의 e2e** 다. 사람이 하는 그대로 했다: 진짜 소스에 평범한
임포트 한 줄을 심고, `project.md` 의 전수 명령을 맨몸으로 치고, 되돌렸다.

- 전수(변이 전·후): **797 OK** (20.2s / 21.2s) · 변이 넷 뒤 작업 트리 `git status --porcelain` **빈 줄**
- 명령: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b tests`

| 변이 | 심은 곳 | 결과 |
|---|---|---|
| M-A 안 깔린 서드파티 | `src/websearch/serve.py:30` `import requests` | FAILED (실패 11 · **에러 10**) · 신고 `serve.py:30 import requests` |
| M-B **깔린** 서드파티 | `src/websearch/indexer.py:15` `import six` | **FAILED (실패 1)** · `indexer.py:15 import six` |
| M-C 함수 본문 안 | `e2e/perf_search.py:52` `    import six` | FAILED (실패 1) · `perf_search.py:52 import six` |
| M-D `from` 임포트 | `tests/test_smoke.py:5` `from six import moves` | FAILED (실패 1) · `test_smoke.py:5 import six` |

**M-B 가 이 계획이 존재하는 이유고, 나머지 셋은 그물의 폭이다.** `six` 는 이 기계에서
`<stdlib>/…/3.9/lib/python3.9/site-packages/six.py` 에 산다 — **stdlib 디렉터리 밑**이라
반복 606 리뷰 전의 판정(접두사 한 줄)은 이것을 **통과**시켰다. 오늘은 797 중 **정확히 하나**가
빨갛고 메시지가 줄번호까지 짚는다.

**M-A 는 덤으로 다른 것을 보여 줬다** — 안 깔린 패키지는 전수가 어차피 빨갛다. 다만 모양이
**실패 11 · 에러 10 · 수집된 테스트가 797 → 662** 로 줄어드는 난장판이고, 그 빨감은 계획서가
적어 둔 대로 「내 기계 문제」로 읽힌다. **이 자의 값은 M-A 가 아니라 M-B 에 있다**: 깔린 기계에서
조용히 초록이던 자리가 이제 한 줄짜리 판정으로 나온다.

**안 잰 것**: `__import__("requests")` · `importlib.import_module` 로 감춘 임포트는 그물
밖이다(`test_deps.py` 의 `ponytail:` 주석 — 잡는 것은 「어느 날 평범한 임포트 한 줄」 하나다).
품질 기준 표의 나머지 여섯 축은 이 계획이 건드린 파일이 없어 **안 돌렸다**(e2e 룰 1-3절
「기존 위반은 이 계획을 막지 않는다」) — **통과가 아니라 미검증**이다.
