# e2e 결과: crawler-core — 통과 (2026-08-25 야간)

명령: `PYTHONPATH=src python3 e2e/crawl_e2e.py` (이 phase 에서 신설 — 계획 범위 밖 예외 3곳 중 e2e 디렉터리)

| 시나리오 (plan_crawler-core.md) | 결과 |
|---|---|
| 로컬 서버(20페이지, /secret robots 차단), 시드 1, max 15 → DB 성공 15행 | 통과 (exit 0, stdout "수집 15 페이지", DB 15행) |
| robots 차단 URL 요청 로그 0건 | 통과 (0건) |
| 같은 도메인 연속 요청 간격 전부 ≥ 1초 | 통과 (페이지 요청 15건, 최소 간격 1.002s) |

- 판단 메모: 간격 검증에서 `/robots.txt` 1회는 제외(도메인당 1회 메타 요청). 서버 수신 시각 기준이라 0.95s 하한 적용 — 실측 최소 1.002s 로 여유 있음
- e2e 앞 관문: 전체 테스트 37/37 통과 0.007s · 린트 없음(project.md) · 품질 기준(경량·성능·디자인·검색 품질) **미검증 — 측정 명령이 아직 없다** (search-api·search-ui·quality-eval 계획에서 생성)
- 만든 파일: e2e/crawl_e2e.py, docs/e2e/crawler-core/result.md
- 소요: 14.7s (요청 간격 1초 정책에 의한 정상 소요. tests/ 와 분리돼 매 스텝 딸려 돌지 않음)
