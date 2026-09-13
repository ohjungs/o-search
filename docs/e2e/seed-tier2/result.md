# 결과 — 계획 96 `seed-tier2` — 편중을 낮추려고 도메인을 두 배로

## 1. 왜 — 편중이 윤리 문제가 됐다

```
코퍼스 136,819장 중 위키미디어 계열 41% (56,058장)
8만 장 크롤 한 번에 429 가 3,554건 · 백오프가 4개 도메인에서 손을 뗐다
```

**컨셉 2단계(100만)를 지금 12도메인으로 가면 88만 장을 같은 곳에 더 요청하는 것이다.**
컨셉 성능 2 가 *"도메인 다양성으로 해결하는 문제이지 간격을 줄여 해결하는 문제가
아니다"* 라고 못박은 방향의 반대다. **간격을 안 깎아도, 같은 곳을 더 오래 두드리는 것
자체가 예의의 문제다.**

## 2. 실물 결과

```
수집 60 페이지 · 12 도메인 · 7.4초 = 8.06 문서/초 (지속 상한 12.00)
scikit-learn 6 · docs.kernel 6 · datatracker.ietf 6 · numpy 6 · rfc-editor 5 ·
gitlab 5 · pandas 5 · android 5 · tldp 5 · gutenberg 4 · postgresql 4 · man7 3
```

**12도메인 전부에서 실제로 수집된다.** robots 허용과 「깊은 문서」는 다른 질문이라
따로 쟀다 — 허용만 보고 넣었으면 죽은 시드가 섞였을 것이다.

## 3. robots 실측 — 12/12 허용 · 전부 비-위키미디어

| 도메인 | 라이선스 | | 도메인 | 라이선스 |
|---|---|---|---|---|
| docs.kernel.org | GPL-2.0 | | scikit-learn.org | BSD-3 |
| tldp.org | TLDP 자유 | | numpy.org | BSD-3 |
| www.postgresql.org | PostgreSQL | | pandas.pydata.org | BSD-3 |
| www.rfc-editor.org | IETF Trust | | docs.gitlab.com | CC BY-SA 4.0 |
| datatracker.ietf.org | IETF | | developer.android.com | CC BY 2.5 |
| man7.org | GPL/자유 | | www.gutenberg.org | 퍼블릭 도메인 |

`Crawl-delay` 를 선언한 곳이 없다. **그래도 `DOMAIN_INTERVAL` 1초는 그대로다** —
사양의 1초는 사이트가 풀어 줄 수 있는 것이 아니라 우리 쪽 전제 조건이다.

## 4. 효과 — 지속 상한이 두 배, 폐기 내성이 다섯 배

실측(2026-09-09)으로 처리량은 도메인 수에 **정비례**한다(1·2·4·8 → 1.03·2.08·4.40·9.86).

| | tier1 만 | **tier1+tier2** |
|---|---|---|
| 도메인 | 12 | **24** |
| 지속 상한 | 12 문서/초 | **24 문서/초** |
| 위키미디어 4개가 폐기되면 | 8개 남음 | **20개 남음** |

## 5. 코드 0줄

`grep -hv '^#' seeds/tier1.txt seeds/tier2.txt` 로 둘을 합쳐 넘기면 된다.
파일을 나눈 이유는 **tier1 이 「왜 이 열둘인가」의 기록**이고 tier2 는 그와 다른 이유
(편중 해소)로 골랐기 때문이다 — 한 파일에 섞으면 그 구분이 사라진다.
