# e2e 결과 — 계획 69 `noindex-entity-prefilter` (반복 403 · 2026-09-07)

**판정: 통과 — 전수 `Ran 632 tests in 15.889s` · `OK` · rc 0 · 실물 e2e 스크립트 3개 실행
(전부 rc 0) · 저장소 밖 사본 3판(V0 성한 원본 + 변이 2판) 전부 기대대로 → DONE.**

이번 계획은 **아홉 계획 만에 `src/` 를 고쳤다**(제품 2줄). 그래서 이 phase 는 문서 검사가
아니라 **일꾼 파이프라인이 실제로 다르게 동작하는가**를 끝에서 끝까지 물었다.
**새 e2e 파일은 0개다** — 기존 `e2e/noindex_e2e.py` 가 이미 「로컬 서버 → crawl → indexer」
관통과 「뒤늦은 noindex 는 색인에서 빠진다」를 덮고 있었고, **모자란 것은 엔티티 갈래와
화면(HTTP) 축 둘뿐**이라 그 둘만 그 파일에 더했다(`rules/e2e.md` 5절이 허용하는 자리).
파일을 새로 만들면 `README.md:105` 의 「e2e 21종」이 움직이는데, 오늘 `ls e2e/*.py` 는
어제와 같은 **21**이고 단위 건수도 **632** 그대로다.

## 1. 관통 — crawl → indexer → serve, 임시 DB 하나로

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 e2e/noindex_e2e.py
e2e 통과 — 수집 6페이지 중 3문서 색인(noindex·none·엔티티 인코딩 제외), 화면(HTTP)과
질의 둘 다 허용 문서만, 뒤늦은 엔티티 거부·평범한 거부 모두 색인에서 제거되고 출력으로 알림
rc=0
```

로컬 `http.server`(`127.0.0.1:0`)에 여섯 페이지를 띄우고 `tempfile.TemporaryDirectory()`
안의 `crawl.db` 로만 돌렸다. **바깥 네트워크 접속 0 · `data/crawl.db` 무개봉.**

| 경로 | 심은 것 | 기대 | 실측 |
|---|---|---|---|
| `/` | 목차 (`robots` 없음 · `&#` 없음) | 색인 | 색인 |
| `/open` | `robots` **없고** `&#8212;` 만 있다 | 색인 (오탐 대조군) | 색인 |
| `/noindex` | `<meta name="robots" content="noindex">` | 제외 | 제외 |
| `/none` | `content="none"` | 제외 | 제외 |
| **`/entity`** | **`<meta name="&#114;obots" content="noindex">`** | **제외** | **제외** |
| `/follow` | `content="index, follow"` | 색인 (회귀) | 색인 |

- **색인**: 1회차 stdout `3 문서 색인` — `/`·`/open`·`/follow` 만. 계획 전이라면 여기가
  **4** 였다(아래 3절 V1 이 실물로 그 숫자를 낸다).
- **화면(HTTP)**: `python3 -m websearch.serve <db> --port 0` 을 진짜 서브프로세스로 띄우고
  stdout 첫 줄에서 포트를 읽어 `GET /?q=pyeongsan` 을 실제로 때렸다. 응답 200 ·
  `Traceback` 0 · `href="…/open"`·`href="…/follow"` **있음** ·
  `href="…/noindex"`·`href="…/none"`·**`href="…/entity"` 없음**.
  이 축이 오늘 새로 붙었다 — 전에는 CLI `--query` 까지만 봤다.
- **CLI 질의**: 같은 판정을 `indexer --query pyeongsan` 에서도 확인(중복이 아니라
  화면과 CLI 가 **서로 다른 소비자**라 둘 다 본다).

## 2. 제거 축 — `indexer.py:178` 의 `OR` 가 사는 자리

**이미 색인된 뒤에 선언이 붙는 경우**가 진입 필터와 갈리는 자리다. 크롤 CLI 는 기수집
URL 을 건너뛰므로(`digest [5]`, 별도 사안) `pages.html` 을 직접 갱신해 상황만 만들었다.

1. `/follow` 의 html 을 **엔티티 인코딩 noindex** 로 교체 → 재색인 stdout
   `0 문서 색인` + **`1 문서 색인 제외`** · 질의에서 `/follow` 사라지고 `/open` 은 남는다
   (**무관한 문서까지 빠지지 않는다**는 단언을 같이 걸었다).
2. `/open` 을 **평범한** noindex 로 교체 → `1 문서 색인 제외` · 질의 무결과이되
   안내 문자열은 출력된다(계획 69 가 옛 갈래를 회귀시키지 않았다).

## 3. 대조군 — 저장소 밖 사본 3판 (변이 2판)

저장소를 `mktemp -d` 아래로 `rsync`(`--exclude data --exclude .git`) 하고 **사본만**
파이썬 문자열 치환으로 고쳤다(`sed` 0회 — `digest [8]` 의 BSD `sed` 거짓 초록 대응).
매 판 `PYTHONDONTWRITEBYTECODE=1`. 끝난 뒤 저장소 `git status --porcelain` 은
`M e2e/noindex_e2e.py` **하나뿐**(이 phase 가 의도한 편집).

| # | 편집 | 판정 줄 | 뜻 |
|---|---|---|---|
| V0 | 손 안 댐 | `rc=0` · 통과 문구 | 오탐 0 |
| **V1** | `extract.py` 사전 필터에서 `and "&#" not in lowered` 제거 | **rc=1** · `AssertionError: 1회차 stdout: '4 문서 색인\n'` | **진입 축** — 거부 문서가 색인에 들어갔다 |
| **V2** | `indexer.py` 제거 질의에서 `OR p.html LIKE '%&#%'` 제거 | **rc=1** · `AssertionError: 엔티티 거부를 제거하지 않았다: '0 문서 색인\n'` | **제거 축** — 진입만 고치면 옛것이 남는다 |

**두 판이 각각 다른 단언에서 죽는다.** 계획서 3절이 「제품 2줄이 서로 다른 두 자리」라고
적은 문장을, 단위(반복 401)에 이어 **파이프라인 끝에서 끝까지에서도** 실물로 되샀다.
V1 의 실패 문구가 `4 문서 색인` 인 것이 값이다 — 「거부를 무시하고 **한 문서 더**
색인한다」가 사용자에게 보이는 손해의 모양 그 자체다.

## 4. 이번 diff 에 의존하는 다른 e2e

`src/websearch/extract.py`·`indexer.py` 를 건드렸으므로 그 둘을 지나는 축을 골라 돌렸다.

```
PYTHONPATH=src python3 e2e/indexer_e2e.py  → rc 0 (색인 3문서 · 증분 0문서 · 무결과 안내)
PYTHONPATH=src python3 e2e/crawl_e2e.py    → rc 0 (수집 15 · 차단 0 · 최소 간격 1.005s)
```

**안 돌린 것과 사유** — e2e 21종 중 나머지 18종은 이번 diff 가 닿지 않는다
(`design_check.py`·`perf_*.py`·`quality_eval.py`·`passage_eval.py` 등은 디자인·성능·품질
축이고 `extract.is_noindex()`·제거 질의를 지나지 않는다). `quality_eval.py`·
`passage_eval.py` 는 **`data/crawl.db` 를 요구**해서 이번 phase 의 하드 제약(무개봉)과
직접 충돌한다. **안 돌린 것을 통과로 적지 않는다.**

## 5. 전수 — `Ran 632` · `OK` · rc 0 (맨몸 1회)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src \
  python3 -m unittest discover -b -s tests
Ran 632 tests in 15.889s
OK
rc=0
```

파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율). `README.md:104` 「단위
632건」·`:105` 「e2e 21종」과 일치하고 둘 다 이번 phase 에서 **안 움직였다**.

## 6. 완료 기준 — 오늘 실행으로 다시 쟀다

| # | 기준 | 실측 | 판정 |
|---|---|---|---|
| 1 | 엔티티 인코딩 `name` 의 `noindex` 가 **두 자리 모두**에서 먹는다 | 1절(진입 · 3문서 색인) · 2절(제거 · `1 문서 색인 제외`) | 충족 |
| 2 | 빠른 길 유지 — `robots` 도 `&#` 도 없는 문서는 그대로 | `/` 가 파싱 0회로 색인 · 전수 `OK` | 충족 |
| 3 | 오탐 0 | `/open`(`&#` 만) · `/follow`(`index, follow`) 둘 다 색인·검색됨 · V0 rc 0 | 충족 |
| 4 | 변이가 **각각 다른 단언**을 죽인다 | V1 진입 · V2 제거 (3절) | 충족 |
| 5 | 사양·데이터 무변 | `data/crawl.db` sha256 `85c96744…5bda18` **무변**(계획 65~68 e2e 가 적은 값과 한 자도 안 다르다) · `docs/specs/` 무접촉 · 스키마·마이그레이션·재색인·새 의존성 **0** | 충족 |

## 7. e2e 가 잡은 것 — 0건

diff 의 주장과 실물이 어긋난 곳이 없었다. 새로 연 자리도 없다 — 리뷰(반복 402)가
`digest ## 다음 계획 후보` 에 중요도 4 로 등재한 「`</head>` 컷」은 이 계획의 범위 밖이고
오늘 건드리지 않았다.

## 8. 한도 — 지킨 것

- **러너 규율 위반 0회.** 전수 1회 · e2e 스크립트 3회 · 사본 3판을 전부 맨몸으로 돌리고
  판정 줄(`Ran … / OK / rc`)을 눈으로 봤다. `2>&1`·`>/dev/null` **0회**.
- **편집은 저장소 밖에서만**(변이). 실물 워킹트리 변경은 `e2e/noindex_e2e.py` 하나 +
  기록 문서뿐이고 `src/`·`tests/`·`docs/specs/` 는 이 phase 에서 **0줄** 움직였다.
- **바깥 네트워크 접속 0** — 크롤 대상은 로컬 `http.server` 뿐. `data/crawl.db` 무개봉.
- `main` 직접 커밋 0 · PR #7 무접촉(`gh` **0회**) · `--no-verify`·`--force`·`--amend`·
  `rebase` **0회**. 병합은 사람 몫이다.
- 도구 산출물 없음 — 브라우저 도구를 쓰지 않는 프로젝트라 `test-results/` 에 해당하는
  경로가 없다. 위 판정 줄이 실행 출력 전부다.
