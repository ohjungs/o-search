---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 205
updated: 2026-09-01
ctx: 47
night_iterations: 68
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 41 `crawl-db-guard` 개발 1/1 완료 — `crawl` 의 환경 오류가 안내 한 줄 + rc 1 이다.**
설계서 `docs/design_crawl-db-guard.md` · 계획서 `docs/plan_crawl-db-guard.md`
제품 diff 는 `src/websearch/crawl.py` **한 파일 · 실질 8줄**. 다음은 테스트 1스텝.

## 방금 한 것 (2026-09-01 · 개발 1/1 · 반복 205)

### ① 설계 계약을 글자 그대로 넣었다 — `crawl.py` 만 바뀐다

`class StoreOpenError` 를 `NoUsableSeedsError` 옆에 두고(docstring: "환경이라 rc 1,
명령줄 오류 2 와 가른다"), `crawl()` 의 `Store(db_path)` **한 줄**을
`except (sqlite3.Error, OSError) as err: raise StoreOpenError(...) from err` 로 감싸고,
`main()` 이 `except NoUsableSeedsError` **아래에서** 그것만 잡아 rc **1**.
문구는 `indexer.py:264` 와 글자까지 같다. `store.py`·`indexer.py`·`serve.py` **0줄**,
`README.md` 는 `단위 462건`→`465건` **한 줄**(rc 1 칸은 계획 40 이 이미 참으로 만들었다).

### ② 스텝의 주장을 실제 CLI 로 확인했다 — 14~16줄 → **1줄**

임시 디렉터리 4곳에서 `python3 -m websearch.crawl`(cwd 도 거기, 네트워크 미도달):
비 DB 파일 · 쓰기 불가 `data/` · `data` 가 일반 파일 · `crawl.db` 가 디렉터리 —
**넷 다 rc 1 · stderr 1줄 · 트레이스백 없음**이다.
`DB 를 열 수 없다: data/crawl.db — file is not a database` / `unable to open database file`
(둘) / `[Errno 17] File exists: 'data'`.

### ③ 변이가 설계의 예측 한 칸을 정정했다

M1(`OSError` 제거)→**2번만** · M2(`return 1`→`2`)→**3번만** 은 설계표 그대로다.
그런데 **M3(`try` 통째 제거)는 "셋 다" 가 아니라 1·2번만** 죽인다 — 3번은 `crawl.crawl`
을 목으로 갈아 **`main` 의 번역만** 재기 때문이다. 그물과 번역은 다른 축이라 같은 변이에
함께 죽을 이유가 없었다. 셋 다 사망이라 결론은 안 바뀌고, **설계가 예측한 변이표도
실측 대상**이라는 것만 남는다.

곁가지: **RED 셋이 같은 줄에서 죽었다**(클래스가 없어 전부 `AttributeError`). 실패는 봤지만
셋이 서로 다른 것을 재는지는 그때 증명되지 않았고, 그것을 증명한 것은 **변이 셋**이다.

### ④ 또 밟았다 — 러너를 `| tail -5` 로 감쌌다. **여섯 번째다**

README 를 고친 뒤 **재확인** 실행에서 나왔다(첫 실행은 맨몸이었고 README 1건 FAIL 을
그것으로 봤다). 맨몸 재실행으로 465 OK 확인. `digest ## 반복 실패` 를 5 → **6회**.
**새 사실**: 앞 다섯과 달리 방아쇠가 "조항을 잊었다" 가 아니라 **두 번째 실행**이다 —
"이미 봤으니 끝만 보면 된다" 가 파이프를 부른다.

**검증**: 단위 462 → **465건 OK 11.732초** · e2e `crawl_e2e`(수집 15, 최소 간격 1.002s) ·
`indexer_e2e` 통과 · `data/crawl.db` sha256 무변경(`85c96744…5bda18` 대조) ·
`digest` 50항목 · **정확히 200줄**.

## 다음 스텝 (테스트 1)

붙일 곳을 찾는다. 세 축이 각각 몇 건에 붙들려 있나 —
그물(`sqlite3.Error`·`OSError` 갈래) · 번역(rc 1 대 2) · **문구 동일성**.
셋째가 지금 **아무도 안 잰다**: `crawl.py` 와 `indexer.py:264` 의 문구가 같아야 한다는
계약은 설계서에만 있고, 한쪽만 고치면 조용히 갈린다. 변이로 확인한다.
락 갈래(`database is locked`)는 **열지 않는다** — `Store` 의 `timeout=30` 이 한도 밖이다.

**집안일 예고**: `history_current.md` 가 **291줄**이다(상한 300). 다음 반복이 회전 자리다 —
`## 반복 실패` 가 네 번 적은 "회전이 늦는다" 를 되풀이하지 않는다.

---

## 이전 (2026-09-01 · 계획 41 설계 — 반복 204)

**대안 C 확정**(`ccb5932` "가장 짧은 그물이 가장 넓은 그물이었다"). 탐침이 계획의 표를
두 칸 넓혔다 — 다섯째 상황(**락**)과 셋째 던지는 줄(`store.py:24` `execute(SCHEMA)`,
30.68초 뒤 `database is locked`). 199 는 *값*을, 203 은 *예외 타입*을, 204 는 ***던지는
줄***을 안 세었다 — 그래서 그물을 줄이 아니라 **생성자 호출 한 줄 전체**에 걸었다.
A(넓은 그물)는 크롤 도중의 `store.upsert` 락 사망까지 오진해 탈락, B 는 `Store(...)`
호출이 한 곳뿐이라 값이 없어 탈락. 락은 따로 안 가른다(검사 하나가 30.6초).
전문은 `history_current.md` 반복 204.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 반복 205 에서 대조함).
- **탐침은 임시 디렉터리에서만, `cwd` 도 거기다** — 이 계획은 특히 그렇다.
  `crawl` 은 `cwd` 밑에 `data/` 를 만들고 거기 쓴다. `chmod 500` 으로 만든 디렉터리는
  탐침 끝에 반드시 되돌린다.
- 단위 **465건**이 기준선이다(11.7초). 465 미만이면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`)이 줄면 RED · **200줄(상한 200,
  지금 정확히 200)**. `[6]` 은 계획 41 이 DONE 될 때만 닫는다(그때 49).
  **항목을 더하려면 먼저 압축한다** — 205 가 `## 반복 실패` 를 늘리며 두 줄을 도로 줄였다.
- 제품 diff 는 **`src/websearch/crawl.py` 한 파일**이다(설계가 대안 C 로 확정).
  `store.py`·`indexer.py`·`serve.py` 가 바뀌면 RED. `README.md` 는 **건수 줄만** 바뀐다.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- **러너를 파이프로 감싸지 않는다**(`## 반복 실패` **6회** — 205 가 여섯째다.
  읽는 것으로는 안 막힌다. **특히 재확인 실행에서 나온다** — 두 번째 실행을 조심한다).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
