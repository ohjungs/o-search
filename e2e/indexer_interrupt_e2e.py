"""색인 중단 e2e — `plan_indexer-interrupt.md` e2e phase. 계획 6절 기대 결과를 실물로 잰다.

**단위 456건이 구조적으로 못 보는 것: 진짜 SIGINT 를 진짜 색인 프로세스에.**
단위는 `extract.extract_text` 가 `KeyboardInterrupt` 를 던지게 만들어 그 자리를 잰다 —
신호가 프로세스에 도착해 재구축 트랜잭션이 접히고 rc 가 셸에 닿기까지의 **전 구간**은
아직 아무도 안 봤다. 계획 3절의 탐침은 사람이 손으로 한 번 돌린 것이라 회귀를 못 막는다.
계획 020 의 변이 M6(CLI 가 인자를 안 넘긴다)이 단위에 안 잡힌 전례도 같은 자리다.

  시나리오 0  대조군 — 신호를 **안 보내면** 재구축이 끝까지 간다(rc 0 · N행 · 새 정의). 잣대다.
  시나리오 1  재구축 중단 — `DROP TABLE docs` 뒤 SIGINT. **옛 N행이 그대로 살아 있다** ·
              옛 정의 그대로(다음 실행이 다시 재구축한다) · rc 130 · stderr 한 줄 · 트레이스백 0.
  시나리오 2  평소 색인 중단 — 증분 `INSERT` 중 SIGINT. 색인도 원본도 무변경 · rc 130.
  시나리오 3  중단 뒤 재실행이 복구한다 — 같은 DB 를 다시 색인하면 rc 0 · N행 · 새 정의.
  시나리오 4  중단 뒤 검색이 살아 있다 — (a) 재구축 중단 DB 는 **재색인 안내**(rc 2)를 내지
              `결과 없음` 으로 침묵하지 않는다 (b) 평소 중단 DB 는 옛 색인으로 그냥 답한다.

**고정 sleep 으로 신호 시점을 잡지 않는다.** 색인이 쓰기 트랜잭션에 들어간 것을 **쓰기 락으로
보고** 보낸다(`wait_until_writing`) — 재구축 갈래는 `DROP TABLE docs` 에서, 평소 갈래는 첫
`INSERT` 에서 락을 잡고 커밋까지 쥔다. sleep 이면 어떤 날은 트랜잭션이 열리기도 전에 신호가
가고, 그때 이 e2e 는 아무것도 안 재고 초록을 켠다(`interrupt_e2e.py` 가 서버 수신을 보는 것과
같은 이유). 창을 놓치면 초록이 아니라 **측정 불능(2)** 이다.

DB 는 전부 `tempfile.TemporaryDirectory()` 안에서 만들고 CLI 는 `cwd` 를 거기로 잡는다 —
저장소의 `data/crawl.db` 는 안 건드린다.

종료 코드: 0 통과 / 1 위반 / 2 측정 불능(잴 대상이 사라졌다 — 계획 4절).

  PYTHONPATH=src python3 e2e/indexer_interrupt_e2e.py
  PYTHONPATH=src python3 e2e/indexer_interrupt_e2e.py --control   # 옛 색인을 안 심는다 → 2
"""
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from websearch import indexer  # noqa: E402
from websearch.store import Store  # noqa: E402

PAGES = 2000  # 색인 한 번이 1초대여야 신호를 넣을 창이 생긴다(6000문서 전건이 4.58초 — 계획 3절)
TERM = "물푸레나무"  # 시나리오 4 의 질의어. 모든 문서에 있다
OLD_DOCS_SQL = "CREATE VIRTUAL TABLE docs USING fts5(title, body, url)"  # 2-gram 열이 없는 옛 정의
CURRENT_SQL = indexer._CURRENT_SQL  # 드리프트 판정의 원본. 문자열을 두 벌 두면 언젠가 갈라진다
INTERRUPT_MESSAGE = "중단 — 색인은 바뀌지 않았다"

BROKEN = False  # `--control`: 옛 색인이 없는 세계. 잴 대상이 없으면 초록이 아니라 2 다


def unmeasurable(why):
    """실패(1)와 다른 코드로 나간다 — 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.

    `interrupt_e2e.py`·`deadline_e2e.py` 와 같은 규약. 옛 색인이 0행이면 아래 단언
    ("있던 행이 살아 있다")은 **아무 일도 안 일어난 세계에서도 참**이 된다.
    """
    print("측정 불능 — %s" % why, file=sys.stderr)
    raise SystemExit(2)


def html_for(i):
    """추출·2-gram 이 실제로 일할 만큼의 본문(약 4KB — 실제 크롤 페이지 크기대).

    짧게 하면 1,200문서 색인이 0.1초에 끝나 **신호를 넣을 창이 사실상 없다.**
    창이 없으면 이 e2e 는 트랜잭션 밖에서 신호를 보내고도 초록을 켤 수 있다.
    """
    return ("<html><title>문서 %d %s</title><body>"
            "<p>김치찌개 보관법 tuples and handling notes %d</p>" % (i, TERM, i)
            + "<p>%s 그늘 아래 오래된 이야기 ash tree shade story</p>" % TERM * 60
            + "</body></html>")


def add_pages(db_path, start, count):
    """`pages` 에 크롤 결과를 넣는다. 스키마·WAL 은 제품 코드(`Store`)가 만든다."""
    Store(db_path)  # 파일·스키마·journal_mode=WAL
    db = sqlite3.connect(db_path)
    try:
        db.executemany(
            "INSERT INTO pages(url, html, status) VALUES (?, ?, 200)",
            [("http://a.test/%d" % i, html_for(i)) for i in range(start, start + count)])
        db.commit()
    finally:
        db.close()


def docs_state(db_path):
    """(색인 행수, `docs` 정의 원문). 아직 없으면 (0, None)."""
    db = sqlite3.connect(db_path)
    try:
        row = db.execute("SELECT sql FROM sqlite_master WHERE name = 'docs'").fetchone()
        if row is None:
            return 0, None
        return db.execute("SELECT count(*) FROM docs").fetchone()[0], row[0]
    finally:
        db.close()


def integrity(db_path):
    db = sqlite3.connect(db_path)
    try:
        return db.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        db.close()


def page_count(db_path):
    return Store(db_path).count()


def build_db(tmp, drift, extra_pages=0):
    """`data/crawl.db` 에 pages N행 + 색인 1회. 시나리오들이 서는 바닥이다.

    drift=True 면 색인을 옛 정의로 바꿔 담는다 — 다음 실행이 재구축하는 세계다.
    extra_pages 는 색인 **뒤**에 넣는다 — 다음 실행에 증분으로 할 일을 남긴다.
    """
    db_path = os.path.join(tmp, "data", "crawl.db")
    add_pages(db_path, 0, PAGES)
    if not BROKEN:  # --control: 옛 색인을 안 심는다 → 아래 잣대가 0행을 보고 2 로 나간다
        indexer.index_pages(db_path)
    if drift:
        plant_drift(db_path)
    if extra_pages:
        add_pages(db_path, PAGES, extra_pages)
    rows, sql = docs_state(db_path)
    if rows != PAGES:
        unmeasurable("바닥 색인이 %d행이다(필요 %d) — 지울 것이 없으면 중단이 지웠는지 못 잰다"
                     % (rows, PAGES))
    expected = OLD_DOCS_SQL if drift else CURRENT_SQL
    if sql != expected:
        unmeasurable("바닥 `docs` 정의가 기대와 다르다: %s" % sql)
    return db_path


def plant_drift(db_path):
    """`docs` 를 옛 정의로 바꾼다 — **행은 그대로 옮겨 담는다.**

    재구축 중단이 '있던 행' 을 지우는지가 이 파일의 요점이라, 빈 채로 심으면 아무것도 못 잰다.
    """
    db = sqlite3.connect(db_path)
    try:
        rows = []
        if docs_state(db_path)[1] is not None:  # --control 은 색인을 안 심는다
            rows = db.execute("SELECT title, body, url FROM docs").fetchall()
            db.execute("DROP TABLE docs")
        db.execute(OLD_DOCS_SQL)
        db.executemany("INSERT INTO docs(title, body, url) VALUES (?, ?, ?)", rows)
        db.commit()
    finally:
        db.close()


def start_indexer(tmp, *extra):
    """**CLI 서브프로세스**로 띄운다 — `index_pages()` 직접 호출은 rc 도 신호도 못 잰다."""
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"),
               PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen(
        [sys.executable, "-m", "websearch.indexer", "data/crawl.db"] + list(extra),
        env=env, cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def run_indexer(tmp, *extra, **kw):
    proc = start_indexer(tmp, *extra)
    out, err = finish(proc, kw.get("timeout", 120), kw.get("what", "색인"))
    return proc.returncode, out, err


def finish(proc, timeout, what):
    """끝나기를 기다린다. **안 끝나면 죽이고 위반으로 친다** — 중단이 안 먹은 것을 e2e 가
    같이 매달려 숨기면 안 된다."""
    try:
        return proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise AssertionError("%s: %g초 안에 안 끝났다 — 중단이 안 먹었다" % (what, timeout))


def wait_until_writing(proc, db_path, timeout=60.0):
    """색인이 **쓰기 트랜잭션 안에 들어간 것을 보고** True. 창을 놓치면 False.

    볼 수 있는 사건은 쓰기 락이다 — 재구축 갈래는 `DROP TABLE docs`, 평소 갈래는 첫
    `INSERT` 에서 잡고 `commit()` 까지 쥔다. 그래서 락이 잡힌 순간의 SIGINT 는 **되돌릴
    것이 있는 지점**의 SIGINT 다. `timeout=0` 이라 탐침은 기다리지 않고 바로 튕긴다.

    **연속 두 번 잠긴 것을 본다** — 한 번이면 순간 잠금(암묵 트랜잭션의 커밋 경계)을
    긴 트랜잭션으로 착각할 수 있다. 그 착각은 신호가 창 밖으로 나가도 초록이 켜지는 길이다.
    """
    probe = sqlite3.connect(db_path, timeout=0)
    limit = time.monotonic() + timeout
    try:
        locked = 0
        while time.monotonic() < limit:
            if proc.poll() is not None:
                return False  # 신호를 넣기 전에 끝났다 — 잰 것이 없다
            try:
                probe.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError:
                locked += 1
                if locked == 2:
                    return True
                time.sleep(0.02)
                continue
            probe.rollback()
            locked = 0
            time.sleep(0.005)
    finally:
        probe.close()
    return False


def interrupt(tmp, db_path, what):
    """색인을 띄우고 트랜잭션 안에서 SIGINT. (rc, stdout, stderr, 신호~종료 초)."""
    proc = start_indexer(tmp)
    if not wait_until_writing(proc, db_path):
        proc.kill()
        proc.communicate()
        unmeasurable("%s: 색인이 쓰기 트랜잭션에 들어가는 것을 못 봤다 — 신호를 "
                     "넣을 창이 없었다(PAGES 를 키운다)" % what)
    sent_at = time.monotonic()
    proc.send_signal(signal.SIGINT)
    out, err = finish(proc, 60, what)
    return proc.returncode, out, err, time.monotonic() - sent_at


def assert_interrupt_report(rc, out, err, elapsed, what):
    """중단이 사용자에게 내는 것 — 계획 6절 4번. 네 시나리오가 같은 계약을 본다."""
    assert rc == 130, "%s: 종료 코드가 130 이 아니라 %d 다\n%s" % (what, rc, err.strip()[-400:])
    assert "Traceback" not in err, "%s: 트레이스백이 나왔다\n%s" % (what, err.strip()[-400:])
    assert err.strip() == INTERRUPT_MESSAGE, (
        "%s: 안내가 한 줄 %r 이 아니다: %r" % (what, INTERRUPT_MESSAGE, err.strip()))
    assert out.strip() == "", "%s: 중단인데 색인했다고 찍었다: %r" % (what, out.strip())
    assert elapsed <= 10.0, "%s: SIGINT 뒤 %.1f초 걸렸다" % (what, elapsed)


def scenario_0_control():
    """대조군 — 신호를 안 보내면 재구축이 끝까지 간다. **없으면 아래가 근거를 잃는다**:
    재구축이 아예 안 도는 세계에서도 "옛 행이 살아 있다" 는 참이다."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = build_db(tmp, drift=True)
        started = time.monotonic()
        rc, out, err = run_indexer(tmp, what="대조군")
        elapsed = time.monotonic() - started
        rows, sql = docs_state(db_path)
    if rc != 0 or rows != PAGES or sql != CURRENT_SQL:
        unmeasurable("대조군이 rc %d · %d행이다(기대 rc 0 · %d행). 재구축이 도는 세계가 "
                     "아니면 중단을 잴 수 없다\n%s" % (rc, rows, PAGES, err.strip()[-400:]))
    assert "중단" not in err, "신호를 안 보냈는데 중단으로 끝났다: %s" % err.strip()[-200:]
    return elapsed, rows


def scenario_1_3_4a_rebuild():
    """재구축 중단 → 옛 색인 생존 → 재실행 복구 → 그 사이 검색은 침묵하지 않는다.

    한 DB 의 연속된 사건이라 나누면 같은 바닥을 두 번 더 깔 뿐이다.
    **이 계획이 산 이유가 여기 있다**: 고치기 전에는 `DROP` 이 그 자리에서 커밋돼
    옛 N행이 사라지고 0행이 남았다(계획 3절 탐침 B).
    """
    with tempfile.TemporaryDirectory() as tmp:
        db_path = build_db(tmp, drift=True)
        rc, out, err, elapsed = interrupt(tmp, db_path, "시나리오 1")
        rows, sql = docs_state(db_path)
        ok = integrity(db_path)
        q_rc, q_out, q_err = run_indexer(tmp, "--query", TERM, what="시나리오 4a")
        heal_rc, heal_out, heal_err = run_indexer(tmp, what="시나리오 3")
        healed_rows, healed_sql = docs_state(db_path)
        q2_rc, q2_out, q2_err = run_indexer(tmp, "--query", TERM, what="시나리오 4a 복구 뒤")

    assert_interrupt_report(rc, out, err, elapsed, "시나리오 1")
    assert rows == PAGES, (
        "재구축 중단이 옛 색인을 %d행으로 만들었다(있던 것 %d행) — DROP 이 커밋됐다"
        % (rows, PAGES))
    assert sql == OLD_DOCS_SQL, (
        "옛 정의가 안 남았다 — 다음 실행이 재구축을 안 한다: %s" % sql)
    assert ok == "ok", "중단 뒤 DB 무결성이 %r 이다" % ok

    # [4a] 옛 정의로 남은 색인은 **재색인 안내**를 낸다. `결과 없음` 은 크롤을 안 한 DB 와
    #      구별이 안 되는 침묵이다 — 21·26·29 가 세 번 닫은 실패 모양이 그것이다.
    assert q_rc == 2, "중단 뒤 질의가 rc %d 다(기대 2)\n%s" % (q_rc, q_err.strip()[-300:])
    assert "결과 없음" not in q_out, "옛 색인이 살아 있는데 `결과 없음` 으로 침묵했다"
    assert "색인을 다시 돌린다" in q_err, "복구법을 안 알려 준다: %r" % q_err.strip()

    # [3] 재실행이 복구한다 — 중단은 되돌리기만 하고 막다른 골목을 안 만든다
    assert heal_rc == 0, "재실행이 rc %d 다\n%s" % (heal_rc, heal_err.strip()[-400:])
    assert (healed_rows, healed_sql) == (PAGES, CURRENT_SQL), (
        "재실행이 복구를 못 했다 — %d행 / %s" % (healed_rows, healed_sql))
    assert "%d 문서 색인" % PAGES in heal_out, "재실행 보고가 %r" % heal_out.strip()
    assert q2_rc == 0 and "http://a.test/" in q2_out, (
        "복구 뒤 질의가 rc %d · %r" % (q2_rc, q2_out.strip()[:200]))
    return elapsed, rows


def scenario_2_4b_incremental():
    """평소(증분) 색인 중단 — 색인도 원본도 안 바뀐다. 그리고 **검색이 그냥 답한다.**

    여기는 고치기 전에도 색인은 무사했다(계획 3절 탐침 A). 잰 적이 없었을 뿐이다 —
    회귀(행마다 `commit()`)를 막는 자리이자, rc 130 계약이 두 갈래 모두에 걸린다는 증거다.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db_path = build_db(tmp, drift=False, extra_pages=PAGES)
        rc, out, err, elapsed = interrupt(tmp, db_path, "시나리오 2")
        rows, sql = docs_state(db_path)
        pages = page_count(db_path)
        ok = integrity(db_path)
        q_rc, q_out, q_err = run_indexer(tmp, "--query", TERM, what="시나리오 4b")

    assert_interrupt_report(rc, out, err, elapsed, "시나리오 2")
    assert (rows, sql) == (PAGES, CURRENT_SQL), (
        "증분 중단이 색인을 %d행으로 바꿨다(있던 것 %d행)" % (rows, PAGES))
    assert pages == 2 * PAGES, "중단이 원본 pages 를 %d행으로 바꿨다(기대 %d)" % (pages, 2 * PAGES)
    assert ok == "ok", "중단 뒤 DB 무결성이 %r 이다" % ok
    # [4b] 옛 색인이 그대로 답한다 — 중단이 검색을 못 쓰게 만들지 않는다
    assert q_rc == 0, "중단 뒤 질의가 rc %d 다\n%s" % (q_rc, q_err.strip()[-300:])
    assert "결과 없음" not in q_out and "http://a.test/" in q_out, (
        "중단 뒤 검색이 안 답한다: %r" % q_out.strip()[:200])
    return elapsed, rows, pages


def main():
    global BROKEN
    BROKEN = "--control" in sys.argv[1:]

    s0_elapsed, s0_rows = scenario_0_control()
    s1_elapsed, s1_rows = scenario_1_3_4a_rebuild()
    s2_elapsed, s2_rows, s2_pages = scenario_2_4b_incremental()

    print("e2e 통과 — 문서 %d개 · 진짜 SIGINT 를 진짜 색인 프로세스에" % PAGES)
    print("  [0] 대조군(신호 없음): 재구축 완주 %d행 · rc 0 · %.1fs — 아래의 잣대" % (s0_rows, s0_elapsed))
    print("  [1] 재구축 중단: SIGINT 뒤 %.2fs 에 rc 130 · 옛 색인 %d행 그대로 · 옛 정의 그대로"
          % (s1_elapsed, s1_rows))
    print("  [3] 재실행 복구: rc 0 · %d행 · 새 정의" % s1_rows)
    print("  [4a] 중단 뒤 질의: rc 2 + 재색인 안내(`결과 없음` 아님) · 복구 뒤 rc 0")
    print("  [2] 평소 색인 중단: SIGINT 뒤 %.2fs 에 rc 130 · 색인 %d행 · pages %d행 무변경"
          % (s2_elapsed, s2_rows, s2_pages))
    print("  [4b] 그 DB 의 질의: rc 0 · 옛 색인이 그대로 답한다")


if __name__ == "__main__":
    main()
