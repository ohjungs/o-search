# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

---

## 2026-08-25 | crawler-core | 계획 1 | 시도1
- 한 일: 초기화(템플릿 7개 배치, 훅 설치) + concept.md 를 계획 6개로 분할(index.md) + plan_crawler-core.md 작성(스텝 7)
- 결과: project.md 명령 절은 "없음"(코드 0줄) — 스텝 1에서 갱신 예정
- 다음: 설계 phase — design_crawler-core.md (스택·모듈 경계)

## 2026-08-25 | crawler-core | 설계 | 시도1
- 한 일: design_crawler-core.md — 대안 3개(stdlib만/의존성 추가/Node) 비교, A 선택. 가정 탐침: 시스템 Python 3.9.6 sqlite3 FTS5 생성 성공
- 결과: 의존성 0 → 설계룰 4절 보류 사안 없음. 계약(시그니처·스키마) 확정
- 다음: 개발 스텝 1 — 스캐폴드 + unittest 러너 확인

## 2026-08-25 야간1 | crawler-core | 개발 1/7 | 시도1
- 한 일: 스캐폴드 — src/websearch/__init__.py, tests/test_smoke.py, .gitignore(data/·reports/), project.md 명령 갱신
- 결과: unittest 1/1 통과. 실패 먼저 확인(네임스페이스 패키지 탓에 1차 시도는 실패를 못 봐 단언 교체)
- 다음: 개발 2/7 robots
