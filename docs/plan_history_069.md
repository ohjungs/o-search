# 계획 90 `live-plan-gap` — 버려진 계획을 아무도 안 물었다

## 1. 왜 지금인가 — 계획 하나가 스텝 3/3 을 남기고 버려졌고, 네 계획이 그 위를 지났다

**근거는 지어낸 것이 아니라 오늘 이 저장소가 들고 있는 상태다.**

```
index.md            | plan_iter-third-witness | 진행 | loop/iter-third-witness | 2/3 | — |
docs/plan_iter-third-witness.md   살아 있다 (90줄)
status.md frontmatter             plan: backoff-recovery · step 2/2
status.md 본문                    「## 계획 85 `iter-third-witness`」… 「## 다음 스텝 — 개발 3/3」
전수                              737 OK rc 0        ← 아무도 안 문다
```

`iter-third-witness` 는 개발 2/3 까지 가고(`aca4be4`) **3/3 을 실행하지 않았다.**
그 뒤 `f2e8e37` 이 **같은 번호 85 를 다시 써서** 다른 계획(`search-scaling`)을 마감했고,
86·87·88·89 가 차례로 지나갔다. 68개 계획 행 중 `진행` 은 **이 하나뿐**이다
(66 완료 · 1 보류(패치) · 1 진행).

**증상은 `status.md` 본문에서도 보인다.** 본문 마지막 변경은 `f2e8e37`(계획 85)이고
86~89 는 **frontmatter 세 줄만** 고쳤다 — 실측:

```
1b79a74 (89) 본문변경 0    78f323c (88) 본문변경 0
6ea7f10 (87) 본문변경 0    ba83bc2 (86) 본문변경 0
f2e8e37 (85) 본문변경 19   ← 마지막
```

그래서 오늘 이 세션이 `status.md` 를 읽었을 때 **본문이 시킨 일은 「개발 3/3 — 변이
3종을 심어라」**, 즉 넉 달 전 계획의 다 끝난 척하는 스텝이었다. `history_current.md`
와 `git log` 를 교차로 읽지 않았으면 그것을 했다.

**왜 스위트가 조용한가.** 문서 가드가 이미 여덟 벌 있는데(`iter_gap`·`step_gap`·
`strike_gap`·`verdict_gap`·`archive_gap`·`const_gap`·`cap_gap`·`DocCitationTest`)
전부 **`status.plan` 이 가리키는 그 계획만** 본다. `step_gap` 은 `plan: backoff-recovery`
행의 스텝 칸을 대조해 2/2 = 2/2 로 초록이고, **뒤에 남겨진 행은 시야 밖**이다.
`archive_gap` 은 `완료` 만 아카이브를 요구하고 `보류`·`진행` 은 명시적으로 봐준다
(`test_held_plan_stays_put`). **버려진 계획을 무는 자가 0개다.**

## 2. 처방 — 「`진행` 인 행은 지금 도는 계획뿐이다」를 자로 만든다

`live_gap(status_text, index_text)`:

- `index.md` 에서 상태 칸이 `진행` 인 계획 행의 슬러그를 전부 모은다
- `status.md` 의 `plan:` 슬러그와 다른 것이 하나라도 있으면 **그 이름을 붙여 신고**한다
- `진행` 이 0개면 조용하다 — 계획 마감 직후·`plan: null` 이 정당하게 그렇다

**산문을 안 읽는다.** 「본문이 `plan:` 슬러그를 부르는가」로 잡는 안도 있었고 그것도
오늘 실물을 물었겠지만, 산문 매칭은 거짓 RED 의 원천이고(`verdict_gap` 이 어휘 `통과`
를 요구하지 않기로 한 것과 같은 이유 — 2026-09-07 실측에서 여섯 행이 거짓 RED 였다)
**버려진 계획이라는 사실 자체는 표의 칸에 이미 적혀 있다.** 칸을 읽는 쪽이 짧고 세다.

**실물은 이 반복이 손으로 맞춘다** (계획 85 가 반복 번호에 한 것과 같은 순서다).
자가 서는 순간 실물이 빨간 것과 **자에 이빨이 있는 것은 다른 명제**라, 후자는 스텝 1 이
**정정 전 트리를 자에 먹여서** 증명하고 스텝 2 의 변이가 마무리한다.

## 3. 스텝

| # | 산출물 | 의존 |
|---|---|---|
| 1 | `live_gap` + `LivePlanSyncTest`(실물) + `LiveGapTest`(합성 갈래). 이빨은 `git show <이 커밋>:docs/{status,index}.md` 를 먹여 잰다 | 이 반복의 실물 정정 |
| 2 | 변이 3종으로 재고 `digest ## 반복 실패` 에 등재 | 1 |

스텝 2 는 1 의 산출물(`live_gap` 본체)을 실제로 고쳐 재므로 진짜 의존이다.

## 4. 완료 기준 — 실행해서 확인한다

- **스텝 1**: `live_gap(git show HEAD:docs/status.md, git show HEAD:docs/index.md)` 이
  **`iter-third-witness` 를 이름으로** 신고한다. 지금 트리에서는 `None`.
  전수 `PYTHONPATH=src python3 -m unittest discover -b tests` OK rc 0.
- **스텝 2**: 변이 3종이 각각 최소 1건을 죽인다 —
  ① `진행` 필터 삭제(모든 행을 본다) ② `status.plan` 비교 삭제(진행이 있으면 무조건 신고
  하지 않고 무조건 통과) ③ 판정 통째 삭제(`return None`).
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다(`project.md`).
  변이가 **실제로 심어졌는지 먼저 단언**한다(digest `[8]` — BSD sed 가 조용히 무시한다).

## 5. 하지 않을 것

- **`iter-third-witness` 의 스텝 3/3 을 대신 하지 않는다.** 변이 3종을 심어 `iter_gap`
  을 재고 digest 에 등재하는 일은 그 계획의 몫이고 별건이다 — 이 반복은 index 행을
  `보류(미완)` 로 바꿔 **사실대로** 적고, 재개 근거를 `digest ## 보류` 에 올린다.
  계획서 `docs/plan_iter-third-witness.md` 는 살려 둔다(재개하려면 그게 있어야 한다).
- **`status.md` 본문에 자를 세우지 않는다.** 2절의 이유. 본문 정정은 이 반복이 한다.
- **번호 85 가 둘인 것은 안 고친다.** 아카이브·digest·index 가 이미 그 번호로 서로를
  가리켜 지금 바꾸면 인용이 통째로 깨진다(계획 85 가 옛 겹침 셋에 내린 것과 같은 판단).
  자가 무는 것은 번호가 아니라 슬러그다.

## 6. 설계 없음 — 트리거 대조

| 트리거 | 해당 |
|---|---|
| 새 모듈·파일 생성 | 아니오 — `tests/test_docs.py` 에 함수 1 + 클래스 2 |
| 공개 인터페이스 추가·변경 | 아니오 — 제품 계약 무변, `src/` 무변 |
| 데이터 구조·저장 형태 변경 | 아니오 |
| 3개 이상 파일에 걸침 | 아니오 — 코드는 `tests/test_docs.py` 하나. `README.md` 의 단위 건수는 `ReadmeCommandsTest` 가 강제하는 **동반 수정**이라 따로 세지 않는다(계획 76 `[R76-2]` 가 이것을 안 적어 걸렸다) |
| 되돌리기 어려운 선택 | 아니오 |
| 대안이 2개 이상 갈림 | **갈렸고 2절에서 골랐다** — 표의 칸 대 본문 산문. 갈림이
  한 줄로 끝나 설계서를 안 연다 |
