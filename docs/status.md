---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 200
updated: 2026-09-01
ctx: 52
night_iterations: 66
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 40 `exit-code-contract` 개발 1/1 완료 — 환경 오류가 rc 1 로 내려왔다.**
계획서 `docs/plan_exit-code-contract.md` · 설계서 `docs/design_exit-code-contract.md` ·
브랜치 `loop/exit-code-contract`(기점 `064e8a5`).
**계획 39 까지 전부 DONE·아카이브 완료.** 계획 34~37 은 PR #2 로 `main` 병합됨
(`main` 최신 `e0890c8`) — 38·39·40 의 `main` 병합은 사람이 정한다.

## 방금 한 것 (2026-09-01 · 개발 1)

### ① TDD — 단언 8곳을 먼저 뒤집어 RED 를 봤다

단언을 먼저 뒤집고 **462건 중 6건 FAIL**(`2 != 1`)을 눈으로 본 뒤 제품을 고쳤다.
실패한 여섯은 전부 설계서가 지목한 자리다 — `test_cli_query_on_drifted_index...` ·
`test_missing_db...` · `test_db_without_pages...` · `test_lock_past_timeout...` ·
`test_not_a_database...` · `test_query_on_a_not_a_database_file...`.

| 파일 | 무엇 |
|---|---|
| `src/websearch/indexer.py` | `:245`·`:251`·`:256`·`:265` `return 2` → **`return 1`** + `FileNotFoundError` 위에 이유 3줄. 인자 오류 `:218`·`:223` 은 2 유지 |
| `tests/test_indexer.py` | 6단언 2→1 · 이름 셋 `..._and_rc_2` → `..._and_rc_1` |
| `e2e/tokenizer_e2e.py` | `:153` 옛 색인 CLI 2→1 · `:168` 요약 문구 `500/rc=2`→`rc=1` |
| `e2e/indexer_interrupt_e2e.py` | `:281` 중단 뒤 질의 2→1 · docstring `:14`·출력 `:334` |
| `README.md` | `:28` 아래 계약 표(0·1·2·130) 9줄 |

`crawl.py`·`serve.py` 는 **0줄** — 설계가 그은 한도 그대로다.

### ② 설계의 "옮기는 자리 전수" 가 **한 곳을 빠뜨렸다**

설계서 §"옮기는 자리 전수" 는 7곳(단위 6 + `tokenizer_e2e:153`)이라고 적었지만
**`e2e/indexer_interrupt_e2e.py:281` 이 여덟째였다** — 재구축 중단 DB 의 질의가
`StaleIndexError` 를 거쳐 `assert q_rc == 2` 로 값을 붙들고 있었다. 설계가 못 본 이유는
**설계도 계획과 같은 도구를 썼기 때문이다**: 반복 199 가 "호출을 grep 하면 헬퍼 뒤의
단언이 안 보인다" 를 배우고 값(`rc, 1`)으로 세는 것으로 고쳤는데, 이 파일의 단언은
`assertEqual` 이 아니라 **`assert` 문**이고 변수도 `q_rc` 라 그 문법형에도 안 걸렸다.
**일반화: 값으로 세는 것으로는 부족하다 — 단언의 *문법형*(`assertEqual` / 맨 `assert`)이
파일 종류마다 다르면 한 벌만 세는 grep 은 종류 하나를 통째로 놓친다.**
바로잡은 값은 설계의 결론이 아니라 **범위**뿐이라 계약은 그대로 갔다(중단 DB 도 환경 오류다).

### ③ 변이 M1 이 새 단언 **하나만** 죽였다

`.git` 없는 스크래치패드 전체 사본(`rsync --exclude .git`)에서 `:242` 만 `return 2` 로
되돌리니 **462건 중 `test_missing_db_is_error_not_traceback` 1건만** FAIL 했다 —
설계가 예고한 그대로다. **처음엔 `src`+`tests` 만 복사했다가 438건·오류 7건이 나왔다**
(README·docs 를 읽는 테스트가 파일이 없어 깨졌다). 사본을 통째로 뜨고 **변이 전에
462 OK 를 먼저 확인**해서 기준선을 세운 뒤 심었다 — 안 그랬으면 "변이가 죽였다" 와
"복사가 부실했다" 를 못 갈랐다.

## 다음 (테스트 phase)

개발 스텝이 하나뿐이라 코드 작업은 **끝났다**. 테스트 phase 는 새 코드가 아니라
**계약이 실제로 전수인지**를 본다 — ②가 여덟째 자리를 뒤늦게 찾은 만큼
`assert` 문 형태의 rc 단언이 e2e 15파일에 더 없는지 확인한다(`returncode`·`_rc` 양쪽으로).
미커밋 상태다 — 커밋 메시지는 `개발 - exit-code-contract - 1/1 - ...`.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — **확인함**).
- 단위 **462건**이 하나라도 줄면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`)이 줄면 RED · 191줄(상한 200).
  `[7]` 은 계획 40 이 DONE 될 때만 닫는다(그때 49).
- 제품 diff 는 **`src/websearch/indexer.py` 한 파일**이다. `crawl.py`·`serve.py` 가
  바뀌면 RED.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
