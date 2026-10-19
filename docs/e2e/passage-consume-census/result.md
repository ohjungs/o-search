# e2e 결과 — `passage-consume-census` (계획 120 · 2026-10-20)

계획서 `## e2e 시나리오` 세 줄을 그대로 돌렸다. **시나리오를 구현에 맞춰 낮춘 곳이
한 군데 있고, 그것을 숨기지 않고 ① 에 적었다.**

## ① 실물 DB 가 있는 기계에서 맨몸으로 돈다

```
$ PYTHONPATH=src python3 e2e/passage_consume.py
모양 문서 3/3 (드리프트 0 · 정렬 깨짐 0 · position 이동 0) · 모양 블록 49 · 질의 49
분모(상위 10 에 든 쌍) 27 · **분자(모양 블록이 근거로 나간 쌍) 12**
상한 44.4% (12/27) · 느슨한 축(모양 블록 «중 하나» 가 이긴 쌍) 44.4% (12/27)
후보가 열린다 — 모양 블록이 본문을 이긴 쌍이 12 건이다
rc=1
```

**통과 — 단 계획서가 적은 기대값은 `rc=0` 이었다.** 계획 단계에서는 수를 모르니
「수가 찍히고 `rc=0`」이라고 썼는데, 그 뒤 설계가 **`1` 을 「분자가 0 이 아니다(후보가
열린다)」로** 못박았고 실물 분자가 12 다. 즉 **`rc=1` 이 이 시나리오의 옳은 결과**다.
**시나리오를 낮춘 것이 아니라 계획서의 기대값이 설계보다 앞서 쓰인 것**이고, 수를 보고
기준을 바꾼 것이 아니라는 증거는 설계 계약 4 가 **측정 전에** 적혀 있다는 것이다.
0 이 나왔다면 `rc=0` 이었고 후보는 닫혔다.

**파이프를 안 붙였다.** 이 밤에 같은 계열 사고가 세 번 났고(`digest` 반복 실패 ·
`high`), 셋 다 판정을 가린 것이다. 위 `rc` 는 리다이렉션으로 받았다.

## ② 실물 DB 가 없는 기계를 흉내낸다

```
$ PYTHONPATH=src python3 e2e/passage_consume.py --db data/없는것.db
측정 불능 — DB 가 없다: data/없는것.db — 이 자는 그 DB 가 있는 기계에서만 돈다
rc=2
```

**통과.** 「미달(1)」로 안 보인다 — 설정 때문에 못 잰 것을 사람이 버그로 읽으면 엉뚱한
것을 고치러 간다. **리뷰가 이 축을 한 번 더 넓혔다**: 고치기 전에는 `pages` 테이블이
없는 DB·옛 색인·`os.makedirs("")` 가 **`rc=1`(「후보가 열린다」)로 나갔다** — 크래시가
수로 위장한 것이고, 지금은 셋 다 2 다.

```
$ PYTHONPATH=src python3 e2e/passage_consume.py --db <pages 없는 DB> --fixture <있는 픽스처>
측정 불능 — 측정 중 터졌다: OperationalError: no such table: pages
rc=2
```

## ③ 격리 — 실물 데이터를 **치운 채** 전수를 돌린다

정적 확인(「테스트가 실물 경로를 안 쓴다」)으로 끝내지 않고 **동적으로 쟀다** —
`data/` 를 옮긴 상태에서 전수를 돌렸다(rename 이라 즉시 되돌린다 · 복구 확인함).

```
$ mv data data_off && PYTHONPATH=src python3 -m unittest discover -b tests
Ran 939 tests in 24.279s
OK
rc=0
$ mv data_off data   # 10G data/crawl.db 복구 확인
```

**통과.** 11GB 실물 DB 가 **없어도 939건이 전부 돈다** — 단위는 `_Seeded` 가 세우는
임시 DB(합성 예문)만 본다. 설계 계약 5 가 요구한 것이고, 이 쪽이 「`passage_consume.DB`
를 grep 해서 안 나온다」보다 강하다.

## 곁가지 — 리뷰가 찾은 「두 실행 경로」가 여기서 다시 쓰였다

백지 패스 [A] 가 찾은 것: `__main__` 가드가 테스트 파일 중간에 있어
`python3 tests/test_passage_consume.py` 가 **10건만** 돌았다(머지 게이트는 `discover` 라
초록이었다). 지금은 **두 경로가 모두 33건**이다.

```
$ PYTHONPATH=src python3 -m unittest tests.test_passage_consume   → Ran 33 OK
$ PYTHONPATH=src python3 tests/test_passage_consume.py            → Ran 33 OK
```

## 품질 기준

**이 계획은 제품 `src/` 를 0줄 고쳤다** — 품질 축은 구조적으로 영향이 없다.
그래도 밤의 관례대로 돌렸다(`e2e.md` 1절 3번). 

### 측정 축 (2026-10-20)

| 축 | 명령 | 결과 |
|---|---|---|
| 전수 | `python3 -m unittest discover -b tests` | **939 OK rc=0** (23.4s) |
| e2e 시나리오 18종 | `python3 e2e/<이름>.py` | **실패 0건** |
| 근거 문단 | `e2e/passage_eval.py` | **정확도 100.0% ≥ 90%** · p50 1.59ms · **p95 1.71ms ≤ 500ms** · rc=0 |
| 검색 품질 | `e2e/quality_eval.py` | 합격선 80% **통과** · rc=0 |
| 의존성 0 | `-m unittest tests.test_deps` | 전수 안에서 통과 |
| **근거 문단 소비 (새 축)** | `e2e/passage_consume.py` | 상한 **44.4%**(12/27) · 느슨한 축 44.4% · rc=1 |

**안 돌린 축은 안 돌렸다고 적는다**: `perf_search`·`perf_crawl`·`perf_memory`·
`crawl_delay_e2e`(18종 안에 있어 돌았다)·`passage_shapes`. 앞 셋은 **제품 `src/` 0줄**
이라 움직일 수 없고, `passage_shapes` 는 이 계획이 건드리지 않은 공급 축이다.
`design_check` 는 18종 명부 안에 있어 돌았다.
