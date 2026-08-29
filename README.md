# O-Search

표준 라이브러리만으로 만든 웹 검색 엔진. 크롤러 · 색인 · 검색 API · 검색 UI 까지 한 저장소에 있다.

## 무엇으로 만들었나

의존성이 없다. `urllib` · `html.parser` · `sqlite3` · `concurrent.futures` 만 쓴다.
색인은 SQLite FTS5, 한국어는 2-gram 으로 자른다.

## 써보기

```bash
python -m websearch.cli crawl https://example.com --max 100   # 수집
python -m websearch.cli index                                  # 색인
python -m websearch.cli serve                                  # http://localhost:8000
```

## 크롤 윤리

성능과 부딪히면 성능을 포기한다.

- 도메인당 요청 간격 **1초 하한**
- `robots.txt` 준수, 선언된 `Crawl-delay` 준수
- `robots.txt` 읽기 상한 512KB, 잘렸으면 마지막 줄을 버린다 (잘린 규칙은 원문보다 후하므로)

이 약속은 크롤러 내부 상태가 아니라 **서버가 실제로 받은 요청 로그**로 검증한다.

## 품질 기준

| 축 | 기준 | 측정 |
|---|---|---|
| 검색 정확도 | recall@10 ≥ 80% | `e2e/quality_eval.py` |
| 검색 지연 | p95 ≤ 300ms | `e2e/perf_search.py` |
| 수집 속도 | ≥ 5 docs/s | `e2e/perf_crawl.py` |
| UI 무게 | JS ≤ 50KB gzip | `e2e/design_check.py` |
| 명암비 | ≥ 4.5:1 | 〃 |

## 검증

```bash
python -m unittest discover -s tests   # 단위
ls e2e/*.py                            # e2e 시나리오
```

## 개발 방식

`docs/` 에 상태가 전부 있다. `docs/status.md` 가 현재 신호등, `docs/index.md` 가 계획 목록,
`docs/digest.md` 가 반복된 실패 기록이다. 계획 하나 = 브랜치 하나(`loop/<슬러그>`).

테스트는 **변이로 검증한다** — 코드를 일부러 망가뜨려 테스트가 실제로 잡는지 확인하지 않으면
통과로 치지 않는다. 이 저장소의 거짓 초록불 여러 건이 그 절차에서 나왔다.
