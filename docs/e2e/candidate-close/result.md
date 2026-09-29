# e2e 결과 — 계획 111 `candidate-close`

- 일시: 2026-09-29 (반복 671) · 커밋 `b6ce6b7` 기준
- 수단: **사본에서 전수를 실제로 돌린다.** `git archive HEAD | tar -x -C $(mktemp -d)` 로
  떠낸 트리에서 `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests`.
  새 도구·새 파일 **0개** — 이 계획이 재는 것이 문서 대조라 사용자가 하는 그대로가 곧 전수다.
- 원본 저장소는 **안 건드렸다.** 셋 다 사본에서만 편집했다.

## ① 대조군 — 마감 상태 그대로

```
── Ran 857 tests in 22.946s OK rc=0
```

**통과.** 손대지 않은 사본이 조용하다.

## ② 사건 재연 — 계획 110 이 그은 취소선을 뗀다

`docs/digest.md` 의 후보 줄 하나에서 `- ~~` 를 `- ` 로 돌렸다(`index.md` 의
`plan_history_085` 행은 `완료` 그대로).

```
FAIL: test_opened_candidates_are_struck_through (test_docs.OpenSyncTest)
AssertionError: '집어간 후보에 취소선이 없다 — index.md `plan_history_085` 는 `완료` 인데
digest 후보 줄 「백틱 밖 인용 57자리는 여전히 아무도 안 문다」 가 `- ~~` 로 시작하지 않는다'
Ran 857 tests in 22.507s
FAILED (failures=1)
```

**통과.** `failures=1` 이고 메시지가 **슬러그와 제목으로 그 줄을 댄다** — 계획서 완료 기준 2
그대로다. 사람이 파일을 뒤져 자리를 찾을 필요가 없다.

> 되돌린 줄에 마감 관용구(`**닫혔다 — …**`)가 **꼬리로 남았다.** 취소선만 떼고 관용구는
> 남은 부분 되돌리기인데, 그래도 `open_gap` 이 문다 — `closed_pointers` 는 `- ~~` 를
> 요구하므로 이 줄을 안 집고, 무는 것은 새 자 한쪽뿐임이 오히려 선명해졌다.

## ③ 음성 대조 — 새 자를 빼면 같은 편집이 조용한가

②의 편집을 그대로 둔 채 `OpenSyncTest`(14줄)만 지우고 README 건수를 856 으로 맞췄다.

```
Ran 856 tests in 23.023s
OK
```

**통과.** 같은 편집이 **조용해진다** — ②의 빨강은 이 계획이 세운 자가 낸 것이지
기존 검사가 내던 것이 아니다.

## 만든 파일

- `docs/e2e/candidate-close/result.md` (이 파일). 그 외 **없다** — 도구 산출물도 없다.

## 천장 (이 e2e 가 못 재는 것)

- **회전이 후보 절을 말리는 날**은 안 밟았다. 그 갈래는 합성
  `OpenGapTest.test_rotation_draining_the_section_bites` 가 밟는다 — 실물로 재현하려면
  digest 를 상한 200 으로 줄여야 하고 그것은 사람 결정 대기 `[6]` 이다.
- `false_strike` 쪽은 실물에 거짓 취소선이 없어 **음성만 확인**했다(①). 양성은
  `FalseStrikeGapTest` 가 합성으로 밟는다.
