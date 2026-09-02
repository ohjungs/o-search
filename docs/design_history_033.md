# 설계 47 `db-open-atomic` — DB 를 여는 자리 하나

**계획**: `docs/plan_db-open-atomic.md` · **브랜치**: `loop/db-open-atomic` · **기점**: `3d4eaba`
**고치는 파일**: `src/websearch/indexer.py` 하나. `serve.py` **0줄**. 의존성 **0**(stdlib).
**바깥 계약(400·404·500·503·200)은 한 칸도 안 바뀐다** — 지금 거짓인 칸을 참으로 만든다.

## 계약 — 새 자리 하나

```python
def _connect(db_path):
    """있는 DB 만 연다. 없으면 FileNotFoundError — 빈 파일을 절대 만들지 않는다."""
```

| | |
|---|---|
| 반환 | `sqlite3.Connection` (`timeout=30`). 호출부의 `try/finally: db.close()` 는 그대로 |
| 던짐 ① | `FileNotFoundError(db_path)` — 열기가 실패했고 **그 순간에도 파일이 없다** |
| 던짐 ② | `sqlite3.OperationalError` **원문 그대로** — 열기는 실패했는데 파일은 있다(권한·디렉터리·락) |
| 안 던짐 | 손상 DB. 여는 것은 성공하고 **첫 질의**에서 `DatabaseError` 다 — 오늘과 같다(→500) |

**호출부 셋 전부 이 자리를 지난다.** `index_pages`·`search` 는 `os.path.exists` 2줄을 지우고
`db = _connect(db_path)`. `_doc_count` 만 `except FileNotFoundError: return 0` 로 감싼다.

## 갈림길 넷 — 골랐다

### 1. 어떻게 원자적으로 여나 → **A: `file:…?mode=rw` URI**

| 대안 | 출발점 | 판정 |
|---|---|---|
| **A URI `mode=rw`** | 네이티브(사다리 4) | **고른다.** 한 번의 `open(2)` 로 존재·열기가 같은 호출이 된다. 없으면 `OperationalError`, **파일 안 생김**(실측) |
| B `connect` 뒤 `getsize()==0` 이면 지운다 | 최소 | **접는다.** 사후 청소는 원자화가 아니고, 계획 5절의 «파일을 지우지 않는다» 를 정면으로 어긴다 |
| C `os.open(O_RDONLY)` 로 errno 를 먼저 본다 | 정공법 | **접는다.** 열기가 **두 번**이 되어 TOCTOU 가 그 사이로 되돌아온다. 고치려는 것을 다시 만든다 |

**`urllib.request.pathname2url` 로 인용한다 — 선택이 아니라 필수다.** 날 경로를 URI 에 붙이면
`a b#c?d.db` 에서 `#` 이 프래그먼트를 열어 **`?mode=rw` 가 통째로 무시되고**, 실측에서 `rwc` 기본값으로
떨어져 **`a b` 라는 빈 DB 를 새로 만들었다**(고치려던 바로 그 버그가 인용 하나 빠져 부활한다).
`%` 도 같다. 한글·공백은 인용 없이도 우연히 돌아가서 **기존 495건은 이 구멍을 못 본다**(변이 M2).
상대 경로(`data/crawl.db`, 제품 기본값)도 실측 OK.

### 2. `OperationalError` 를 어디까지 `FileNotFoundError` 로 번역하나 → **실패한 뒤 한 번만 되본다**

없는 파일과 **권한 거부(EACCES)와 디렉터리**가 메시지까지 똑같다(`unable to open database file`).
`e.sqlite_errorcode` 는 파이썬 3.11+ 이고 여기는 **3.9.6** 이라 errno 로 가를 수 없다(실측).

```python
except sqlite3.OperationalError:
    if os.path.exists(db_path):
        raise                              # 권한·디렉터리 — 오늘과 같이 500
    raise FileNotFoundError(db_path) from None
```

**이 `exists` 는 TOCTOU 가 아니다.** 열기는 이미 원자적으로 **실패**했고, 남은 일은 실패한 것을
어느 칸으로 부를지 **분류**뿐이다. 최악의 오분류라도 응답 코드 하나가 503↔500 사이에서 흔들릴 뿐,
파일이 생기거나 없는 것이 있는 것으로 보이지 않는다. 무조건 번역하면 **권한 오류가 503(재시도하라)**
이 되는데 그것은 기다려도 안 낫는 상태라 계획 46 이 500 에 못박은 것과 어긋난다.

### 3. 세 자리를 한 뿌리로 → **`_connect()` 하나**

세 곳이 **같은 두 줄**을 복붙하고 있었고 그래서 **세 곳 다** 틀렸다. 따로 고치면 다음에 넷째
호출부가 생길 때 또 복붙한다. 사다리 2번(이미 있는 것) 대상이 없으니 함수 하나를 만든다 —
호출부 하나짜리 추상화가 아니라 **셋짜리**다.

### 4. `_doc_count()` 독스트링이 거짓이 된 것 → **문서가 아니라 동작을 고친다**

*"DB 파일을 만들지 않는다"* 는 지켜야 할 약속이지 관찰 기록이 아니다. `except FileNotFoundError:
return 0` 세 줄이면 참이 된다. 독스트링을 사실에 맞춰 낮추는 것은 **버그를 사양으로 승격**하는 것이라
안 한다. 문서는 0줄 고친다.

## 안 고치는 것 (범위 밖)

`serve.py` 번역표 · `_fts_query` 의 제어문자 처리 · 스키마·`data/crawl.db` · 새 e2e 파일 ·
`mode=ro` 분리(444 파일도 `mode=rw` 로 열린다 — SQLite 가 알아서 읽기 전용으로 떨어진다, 실측) ·
TOCTOU 가 이미 남긴 빈 파일 청소.

## 스텝 경계 — 2 스텝 유지, 다만 **엣지는 없다**

계획서는 스텝 2 를 *"스텝 1 이 끝나 여는 자리가 하나"* 를 전제로 적었지만 **의존이 아니다.**
스텝 1 은 `os.path.exists`+`connect` 짝을, 스텝 2 는 `if not match: return []` 의 **위치**를 건드리고
둘은 겹치지 않는다. 짝 검사(`digest [8]` 0초 회수): **어느 하나만 고쳐도 회수가 0 이 아니다** —
1 만 고치면 손상 DB + `q=%01` 이 그대로 200 이고, 2 만 고치면 레이스가 그대로 빈 파일을 만든다.
그래서 **둘 다 필요하고 순서는 아무래도 좋다.** 각자 검증 가능하므로 스텝은 둘로 둔다.

**스텝 2 의 새 자리는 `sql != _CURRENT_SQL`(옛 색인) 검사 *뒤*다.** 앞에 두면 옛 색인 + `q=%01` 이
`[]`→200 으로 새 나가 고치려던 구멍이 절반 남는다(변이 M6).
비용은 실측 **0.066ms/회**(무토큰 질의가 이제 DB 를 연다). p95 8.71ms · 예산 300ms 대비 무시 가능.

## 변이 표 — 여덟 개를 심는다 (**여섯이 좁힌다**)

| # | 심는 변이 | 죽어야 하는 단언 | 오늘 495건이 잡나 |
|---|---|---|---|
| M1 | `mode=rw` → `mode=rwc` | 레이스 3건(`search`·`_doc_count`·`index_pages`): `connect` 직전 삭제 훅 뒤 `FileNotFoundError` + **`os.path.exists` 거짓 유지** | **아니오** ← 좁힌다 |
| M2 | `pathname2url()` 제거(날 경로) | `a b#c?d.db` 경로에서 정상 검색 1건 + 그 옆에 **빈 `a b` 안 생김** | **아니오** ← 좁힌다 |
| M3 | `except` 안의 `if os.path.exists: raise` 삭제 | 권한 0 인 DB 가 `OperationalError`(→500) — `FileNotFoundError`(503) 아님 | **아니오** ← 좁힌다 |
| M4 | `_doc_count` 의 `except FileNotFoundError: return 0` 삭제 | `_doc_count(없는경로) == 0` **직접 호출** | **아니오** ← 좁힌다. CLI 로만 보면 rc·문구가 같아 통과한다 |
| M5 | 무토큰 조기 반환을 `connect` **앞**으로 되돌림 | 손상 DB + `q=%01` → `DatabaseError`(→**500**) · 옛 색인 + `q=%01` → `StaleIndexError`(→**503**) | **아니오** ← 좁힌다 |
| M6 | 무토큰 반환을 **옛 색인 검사 앞**에 둠 | 옛 색인 + `q=%01` → `StaleIndexError`(→503) | **아니오** ← 좁힌다 |
| M7 | `timeout=30` 삭제 | `test_every_connection_waits_the_same_thirty_seconds` | **예** — 대조군 |
| M8 | `FileNotFoundError` 로 안 바꾸고 `OperationalError` 를 흘림 | `test_missing_db_raises` 2건 | **예** — 대조군 |

M7 은 새 `_connect` 가 `timeout=30` 을 **키워드로** `indexer.sqlite3.connect` 에 넘겨야 산다
(그 테스트가 모듈 속성을 패치하고 `kw["timeout"]` 을 센다 · 연결 3회 이상도 그대로).

## 되돌리기

커밋 하나 revert. 새 파일·새 의존성·스키마 변경·마이그레이션 **없음**(`project.md` 마이그레이션 항목
공란 — 해당 없음). 피처 플래그 안 쓴다: 되돌릴 것이 한 파일의 함수 하나다.

## 판단 필요 (사람)

없다. 갈림길 넷 전부 실측으로 갈렸고 `concept.md`(*"계약 안정성이 색인 규모보다 위"*)와
계획 46 의 상태 코드 표가 방향을 이미 정해 뒀다.
