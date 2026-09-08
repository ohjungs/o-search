---
signal: GREEN
phase: 개발
step: 2/3
attempt: 0
iteration: 472
updated: 2026-09-08
ctx: 43
night_iterations: 4
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 개발 2/3 완료.** 재크롤로 본문이 갈리면 색인이 **갈아 끼워진다** — 어제까지
새 본문은 영영 0건이었다. 전수 **699 OK**.

다음 반복은 **개발 3/3** — **삭제**. 계약은 `design_recrawl.md` 3절 1번 갈래
(404·410 → `DELETE FROM docs`, `pages` 는 묘비로 남긴다)와 5절(CLI 문구).

## 이번 스텝이 놓은 것

- 워터마크 루프의 판정이 셋이 됐다: `html IS NULL` → 그대로 둔다(일시 장애를 영구
  삭제로 만들지 않는다) · `is_noindex` → 뺀다 · 그 밖 → `DELETE` 후 재추출·`INSERT`.
- **설계가 예고한 잠복 크래시가 실제로 재현됐다** — `is_noindex(None)` 의
  `AttributeError`. NULL 갈래를 `is_noindex` 앞에 두어 닫았고 테스트가 붙든다.
- **갱신 루프를 신규 색인 루프 앞으로 옮겼다.** 방금 넣은 문서도 워터마크 뒤라 그
  집합에 들어, 뒤에 두면 신규 문서가 매 실행 두 번 추출된다. 순서로 푼 것이라
  「방금 넣은 URL」 집합을 들고 다니지 않는다.
- 변이 다섯이 전부 죽는 것을 직접 봤다(NULL 갈래·마크 문·갱신·덧쓰기·루프 순서).

## 다음 반복이 알아야 할 것 둘

1. **`removed = before + indexed - after` 는 갱신에서 안 움직인다**(`DELETE`+`INSERT`).
   스텝 3 이 404 삭제를 더하면 그 수가 비로소 움직이고, 그때 CLI 문구
   `"%d 문서 색인 제외 — noindex 선언"` 이 거짓말이 된다 — 문구만 넓힌다.
2. **`git checkout <파일>` 로 변이를 되돌리지 않는다.** 이번에 미커밋 구현이 통째로
   날아갔다. 되돌리기는 `cp` 백업으로만 한다.

전문: `docs/design_recrawl.md` · 스텝: `docs/plan_recrawl.md` 4절
