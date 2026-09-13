# e2e 결과 — 계획 99 `e2e-roster-count` (2026-09-13 반복 579)

대상: `tests/test_docs.py` 의 `e2e_label_gap` — `docs/project.md` 명부 항목이
**기계가 읽는 줄**이기를 그치는 자리(유령 이름 · 라벨 드리프트)를 문다.

사용자는 사람이 아니라 **명부를 읽어 명령을 조립하는 러너**다. 그래서 「사용자가 하는
그대로」는 *명부에 유령을 심고 러너를 돌리는 것*이다.

## 시나리오 1 — 유령을 실제로 심는다 · **통과**

`docs/project.md` 의 명부에 `roster_ghost_e2e` 를 한 개 넣고 라벨을 18 → 19 로 올렸다
(계획 98 e2e 첫 판이 `E2eRosterTest` 로 실제로 밟았던 모양 그대로).

```
$ PYTHONPATH=src python3 e2e/roster_ghost_e2e.py          # 러너가 명부에서 조립한 명령
can't open file '.../e2e/roster_ghost_e2e.py': [Errno 2] No such file or directory
rc=2

$ PYTHONPATH=src python3 -m unittest discover -b tests    # 전수
FAIL: test_project_roster_names_are_all_runnable (test_docs.E2eLabelTest)
AssertionError: 'project.md 의 명부가 없는 파일을 1개 부른다 — `roster_ghost_e2e`.
  이 줄은 사람만 읽는 줄이 아니라 **기계가 읽는 줄**이라 유령 하나가 러너를 rc=2 로 죽인다'
Ran 779 tests  FAILED (failures=1)
```

**순서 증명**: 러너의 rc=2 는 「그런 파일이 없다」까지만 말하고 **어느 문서의 어느 줄이
낡았는지는 안 말한다.** 전수는 그보다 앞 관문이고 **원인을 이름으로 찍는다** — 계획 98
때는 이 자리가 비어 있어 e2e 가 죽고 나서야 알았다.

원복(`docs/project.md` diff 0) 후 전수 **Ran 779 · OK**.

## 시나리오 2 — 음성 대조 (이빨 측정) · **통과**

유령을 심은 **그대로** 두고 판정만 무력화했다(`if ghosts:` → `if False:`).

| 무엇을 돌렸나 | 결과 | 읽는 법 |
|---|---|---|
| 실물 1건(`E2eLabelTest`) | **OK · rc=0** | 판정을 끄면 **살아 있는 문서의 유령이 안 보인다** — 붉은색의 출처가 이 판정임이 확정된다 |
| 전수 779 | FAILED (3건) | 죽은 것은 **갈래**(`E2eLabelGapTest`)뿐이다 — 합성 픽스처가 「판정을 조용히 끄는 길」을 막는다 |

이 저장소가 갈래와 실물을 **둘 다** 두는 이유가 여기서 그대로 보인다. 실물만 있으면
판정을 끄는 변이가 초록으로 통과하고, 갈래만 있으면 살아 있는 문서가 낡아도 조용하다.

## 만든 파일

- `docs/e2e/e2e-roster-count/result.md` (이 문서) — 그 밖에 만든 파일 없음.
  유령은 **심고 되돌렸다**(`docs/project.md` 최종 diff 0).
