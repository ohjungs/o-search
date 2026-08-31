# 계획 37 — `indexer-interrupt`: 색인 도중 Ctrl-C 가 색인을 지운다

phase: 리뷰 (개발·테스트 끝 · 설계 생략 — 아래 8절)
브랜치: `loop/indexer-interrupt` (기점 `a8ad633`, `loop/signal-budget-cover` 에서 팠다)
슬러그: `indexer-interrupt`

## 1. 문제 · 목표 · 기대 결과

**문제 (둘이고, 뿌리가 다르다).**

① **재구축 중 중단은 옛 색인을 지운 채 끝난다.** `indexer.index_pages()` 는 스키마가
드리프트했을 때 `DROP TABLE docs` → `CREATE` → 전건 `INSERT` → `db.commit()` 로 재구축한다.
그런데 **Python 3.9.6 의 `sqlite3` 은 DDL 을 암묵 트랜잭션에 넣지 않는다** — `DROP`/`CREATE`
는 그 자리에서 autocommit 되고 `INSERT` 만 트랜잭션 안에 있다. 그래서 재구축 도중 Ctrl-C
를 받으면 **옛 색인은 커밋된 채로 사라지고 새 색인은 롤백되어 0행**이 된다. 그때부터
`search()` 는 모든 질의에 `결과 없음` 을 낸다 — **크롤 데이터가 없는 것과 구별되지 않는
성공**이다. 이 저장소가 이미 세 번 닫은 실패 모양이다(21 `indexer-cli-guard` · 26
`crawl-max-guard` · 29 `seed-scheme-guard`).

② **`indexer.main` 만 중단 계약이 없다.** `crawl` 은 SIGINT 를 rc **130** 과 안내 문구로
받고(계획 34·35·36), `serve` 는 `except KeyboardInterrupt: pass` 로 rc **0** 을 낸다.
`indexer` 만 트레이스백을 그대로 흘리고 rc **-2** 로 죽는다. 계획 21 이 **이 함수에서**
이미 세운 관용구("트레이스백은 복구법을 안 알려 준다")를 중단 경로만 안 따른다.

**목표.** 색인 도중 Ctrl-C 가 (ㄱ) **색인을 지우지 않고** (ㄴ) 무엇이 일어났는지 말한다.

**기대 결과.**
- 재구축 도중 SIGINT → `docs` 가 **옛 정의·옛 행수 그대로** 살아 있다.
- 정상 색인 도중 SIGINT → 오늘처럼 색인 무변경(이미 참, 회귀 방지로 못박는다).
- 두 경우 다 rc **130** 과 한 줄 안내(트레이스백 없음).

## 2. 근거

- 출처: `discover.md` **6순위 — `digest.md ## 반복 실패`** 의 "CLI 가 예상 못 한 입력에
  트레이스백을 낸다"(**2회**: 21 `indexer.main` 없는 DB · 24 `serve.main --port`).
  이번이 **같은 파일의 세 번째 자리**다.
- 축: `status.md` 가 지목한 20·23·33·34·35·36 의 **종료 계약** 축. 34~36 이 `crawl` 에서
  닫은 계약을 `indexer` 는 안 갖고 있다.
- ①은 후보 목록에 **없던 것**이다 — 착수 탐침이 ②를 재다가 드러났다(3절 B).

## 3. 착수 탐침 실측 (2026-08-31 · 전부 스크래치패드 임시 디렉터리)

**탐침 A — 정상 색인 도중 SIGINT.** 6000문서(전건 색인 4.58초) 적재 후 실제 CLI
`python3 -m websearch.indexer <db>` 를 띄우고 2.0초에 SIGINT.

```
rc            = -2            (셸에서 130)
종료까지      = 0.01s
stdout        = ''            ← "무슨 일이 있었나" 를 한 글자도 안 말한다
stderr        = KeyboardInterrupt 트레이스백 (extract.py:60 프레임까지 노출)
DB            = pages 6000 · docs 0 · integrity_check ok   ← 색인은 무변경(롤백)
```

**탐침 B — 스키마 재구축 도중 SIGINT.** 같은 DB 를 6000행 색인해 두고 `docs` 를 옛 정의
(2-gram 열 없는 `fts5(title, body, url)`)로 바꿔 드리프트를 만든 뒤 같은 방식으로 2.0초에 SIGINT.

```
rc            = -2
pages         = 6000
docs          = 0            ← 있던 6000행이 사라졌다
docs 정의     = CREATE VIRTUAL TABLE docs USING fts5(title, body, title_ng, body_ng, url …)
                             ← 새 정의는 커밋됐고 내용만 없다
```

**뿌리 확인(맨 sqlite3, 같은 3.9.6).** `DROP TABLE` + `CREATE TABLE` 을 하고 **commit 없이
close** 했더니 되돌아가지 않았다 — 옛 테이블의 행은 사라지고 새 정의가 남는다. DML 과 달리
**DDL 은 암묵 트랜잭션을 열지 않는다**는 것이 ①의 기계적 원인이다.

## 4. 오늘의 검증이 이 변화를 재는가 — **못 잰다**

| 무엇 | 오늘 | 판정 |
|---|---|---|
| 단위 452건 | `indexer` 중단을 재는 것 **0건** | 못 잰다 |
| e2e 18종 | `indexer_e2e.py` 는 정상 경로만. 중단은 `crawl` 쪽 둘(`interrupt_e2e`·`deadline_e2e`)뿐 | 못 잰다 |
| 스키마 드리프트 | 재구축·`StaleIndexError` 단언은 있다. **중단된 재구축은 없다** | 못 잰다 |

→ **본체는 코드가 아니라 단언이 아니다. 이번엔 코드도 바뀐다**(계획 31·36 과 다른 점).
제품 수정과 새 단언이 함께 간다.

## 5. 스텝 분해 (작업 그래프 — 노드 2개, 엣지 0개)

두 노드는 **의존이 없다.** ①은 `index_pages` 의 트랜잭션 경계, ②는 `main` 의 종료 갈래다.
같은 파일이라 같은 트리에서 순차로 돈다(worktree 로 안 가른다 — `plan.md` 3-1 셋 중
"파일이 안 겹친다" 가 거짓).

**스텝 1 — 재구축을 한 트랜잭션으로 묶는다** (임계경로. 데이터가 걸린 쪽이 먼저다) — **완료**(`indexer.py:92`)
- RED: `tests/test_indexer.py` 에 "재구축 도중 예외가 나면 옛 `docs` 가 그대로 살아 있다"
  단언. 중단은 `extract.extract_text` 가 `KeyboardInterrupt` 를 던지게 해서 만든다
  (탐침 B 의 실제 중단 지점과 같은 프레임).
- GREEN: `index_pages` 가 `DROP TABLE docs` 앞에서 `db.execute("BEGIN")` 으로 명시
  트랜잭션을 연다. `db.commit()` 자리는 그대로다.
- 시작점: `src/websearch/indexer.py:88-90`(`_docs_sql(db) not in (None, _CURRENT_SQL)` 갈래).

**스텝 2 — `main` 이 중단을 관용구로 받는다** — **완료**(`indexer.py:255`)
- RED: `indexer.main` 이 `KeyboardInterrupt` 에서 rc **130** 과 안내를 내는 단언
  (`index_pages` 를 목으로 던지게 한다).
- GREEN: 21 이 세운 `except NoCrawlDataError` / `except StaleIndexError` 옆에
  `except KeyboardInterrupt` 한 갈래. **문구는 참인 것만 적는다** — 스텝 1 뒤에는
  "색인은 바뀌지 않았다" 가 두 갈래 모두에서 참이다(스텝 1 전에는 거짓이라 순서가 이렇다).
- 시작점: `src/websearch/indexer.py:236-249`.

## 6. 완료 기준 (측정 가능)

1. 단위 **452 → 455건 내외 OK**(`PYTHONPATH=src python3 -m unittest discover tests`),
   기존 452건 중 **깨지는 것 0**.
2. 탐침 B 재실행: 재구축 도중 SIGINT → `docs` 행수 **6000 유지** · 정의는 옛것 그대로
   (다음 실행이 다시 재구축한다).
3. 탐침 A 재실행: 정상 색인 도중 SIGINT → `pages 6000 · docs 0 · integrity ok`(오늘과 동일).
4. 두 탐침 다 rc **130** · stderr 에 `Traceback` 문자열 **0회** · 안내 한 줄.
5. 색인 성능 회귀 없음: 6000문서 전건 색인 **4.58초 ±10%**(명시 `BEGIN` 이 느리게 만들지 않는다).
6. e2e `PYTHONPATH=src python3 e2e/indexer_e2e.py` rc **0**, 그리고 색인·검색을 지나는
   `search_api_e2e`·`tokenizer_e2e`·`pagination_ui_e2e` rc **0**.
7. `data/crawl.db` sha256 **무변경**.

**테스트 phase 실측(2026-08-31)** — 7개 전부 통과. 단위는 **456건**(계획의 "455건 내외"에
갭 하나를 더했다): 기대 결과 2번(정상 색인 중단은 색인을 안 바꾼다)을 탐침이 아니라 단언이
잡게 했다 — `TestIndexPages.test_interrupted_incremental_run_indexes_nothing`, 변이
**M7**(행마다 `db.commit()`)이 그 단언만 죽인다. 5번(성능)은 개발 phase 의 A/B 판정 그대로다.

## 7. 변이 목록 (심기 전 `count(원문)==1` 을 먼저 단언한다 — `digest [8]`)

| # | 변이 | 죽어야 하는 것 |
|---|---|---|
| M1 | `db.execute("BEGIN")` 삭제 | 스텝 1 단언 **만**. 다른 452건 전부 초록이어야 한다 — 초록이 아니면 이 자리를 이미 누가 재고 있었다는 뜻 |
| M2 | `except KeyboardInterrupt` 갈래를 `return 0` 으로 | rc 단언 |
| M3 | rc `130` → `1` | 종료 코드 단언(경계를 값으로 못박는다) |
| M4 | 안내 문구를 고정 문자열로 치환 | 문구를 재는 단언. **없으면 32 의 교훈대로 아무것도 안 재고 있는 것** |
| M5 | **더 잡는 쪽** — `except KeyboardInterrupt` → `except BaseException` | 대조군이 죽어야 한다. `SystemExit` 까지 삼키면 다른 계약이다(27 의 M4 교훈) |
| M6 | `BEGIN` 을 `DROP` **뒤로** 옮긴다 | 스텝 1 단언. 순서가 계약이다 — 늦게 열면 DROP 은 이미 커밋됐다 |
| M7 | (테스트 phase 추가) `indexed += 1` 뒤에 `db.commit()` 한 줄 | 평소 색인 경로의 중단 단언 **만**. 안내 "색인은 바뀌지 않았다" 가 재구축 아닌 갈래에서도 참인지를 잰다 |

## 8. 설계 phase 트리거 판정 — **걸리지 않는다. 설계 생략**

| 트리거 | 판정 |
|---|---|
| 새 모듈 | 아니다 — `indexer.py` 안 |
| 공개 인터페이스 변경 | rc 가 `-2` → `130`. **저장소 선례가 정한다** — `crawl` 이 34 에서 같은 값을 골랐다. 갈리지 않는다 |
| 데이터 구조 변경 | 아니다 — 스키마·행 정의 무변경. 바뀌는 것은 **트랜잭션 경계**뿐 |
| 3파일 이상 | 아니다 — `src/websearch/indexer.py` · `tests/test_indexer.py` 둘 |
| 되돌리기 어려운 선택 | 아니다 — `BEGIN` 한 줄과 `except` 한 갈래 |
| 대안이 갈림 | 아니다. `BEGIN` 대신 "새 이름으로 만들고 마지막에 rename" 도 되지만 **줄 수가 늘고 같은 것을 산다** (ponytail 6번) |

**짧은 경로 판정 — 아니다.** 다섯 중 넷은 참이지만(한 스텝은 아니고 두 스텝) 다섯째
**"보안·데이터·의존성·스키마와 무관"이 거짓**이다 — ①이 색인 유실이다. 애매하면 평소
경로이고(`SKILL.md` 4-1) 이건 애매하지도 않다. 계획 36 이 짧은 경로였으니 이번이
짧은 경로였으면 2연속이 됐을 것이고, 3연속 규정에는 어차피 안 걸렸다. **길을 고른 이유는
연속 수가 아니라 데이터다.**

## 9. 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마를 안 건드린다. 탐침·e2e 는 임시 디렉터리에서만.
- 기존 단언을 낮추지 않는다. 특히 21 의 `NoCrawlDataError`·`StaleIndexError` 갈래.
- `except KeyboardInterrupt` 가 **다른 예외를 같이 삼키면 RED**(M5 가 그것을 잰다).
- 색인 성능 10% 이상 회귀면 RED.
- 외부 네트워크 금지. `docs/specs/` 는 읽기만. `--no-verify` 금지. `main` 직접 커밋 금지.

## 10. 하지 않을 것

- **`serve` 의 rc 0 은 안 건드린다.** 서버는 Ctrl-C 가 정상 종료 수단이고 e2e 넷이 그
  rc 에 서 있다. `indexer` 와 통일하려는 것은 다른 계약이다.
- **부분 색인 이어가기(체크포인트) 안 한다.** 중단이 남기는 것은 "무변경" 하나면 족하다.
  증분 재개는 `recrawl`(사양 8번, 사용자 승인 항목)의 색인 상태 컬럼이 생겨야 값이 있다.
- **`store.py`·`crawl.py` 의 트랜잭션 경계는 안 본다.** 이 계획의 근거는 `index_pages`
  한 곳의 실측이다. 다른 자리는 근거가 생기면 그때 연다.
- 진행 표시(진행률 출력) 안 한다 — 근거가 없다.

## 11. 이번 탐색이 **반증한** 것 (digest 로 간다)

계획을 고르는 동안 후보 다섯을 실측으로 다시 쟀고 넷이 틀렸다. `digest [7]`("기록된 답을
실행 전에 다시 재라")의 다섯 번째 사례다.

- `[5]`+`[6]` **`_fetch_one` 위치 인자 순서 무단언** → **틀렸다.** 인자 삽입 변이를 세
  자리에 심었더니 전부 죽는다: `now`↔`floor` 사이 **58건**, `floor`↔`sleep` 사이 **8건**,
  `sleep`↔`stop` 사이 **1건**. digest 가 "조용해진다" 고 지목한 바로 그 자리가 8건이다.
- `[4]` **간격 시계가 pop 시각에서 시작한다** → **011 이 닫았다**(`frontier.py:70`
  "시계는 `mark_sent()` 만 건다" · `crawl.py:304` `mark_sent(domain, sent_at)`).
- `[7]` **OFFSET 페이지네이션** → 게이트("지금 화면이 없다")가 013·015 로 **열렸는데 아무도
  안 봤다.** 실측: 25문서·페이지당 10에서 요청 사이에 문서 하나가 증분 색인되면 **중복 1건
  (`/09`)·누락 1건(`/19`)**. 실재하지만 고치려면 `?page=N` 공개 API 를 커서로 바꿔야 해
  015 가 고른 이전/다음 화면과 정면으로 부딪힌다 — **계획이 아니라 사람 판정으로 올린다.**
- `[6]` **`serve.do_GET` 의 400 이 내부 메시지를 싣는다** → **도달 경로 없음을 실측했다.**
  FTS5 문법·주입·제어문자·서로게이트 등 16질의를 JSON·HTML 두 경로에 던져 **500 0건 ·
  유출 0건**(100k 질의만 stdlib 이 414 를 낸다).
