import argparse
import datetime as dt
import json
import os
from glob import glob

import pymysql

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_timestamp(value):
    if not value:
        return None
    if isinstance(value, (dt.datetime, dt.date)):
        return value
    value = str(value).strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def parse_variation_pct(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_schema(cur):
    schema_path = os.path.join(ROOT, "db", "schema_mysql.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        cur.execute(stmt)


def ensure_assets(cur, asset_map):
    rows = [(code, asset_map.get(code)) for code in asset_map.keys() if code]
    if not rows:
        return
    cur.executemany(
        """
        INSERT INTO assets (asset_code, asset_type)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
          asset_type = COALESCE(assets.asset_type, VALUES(asset_type))
        """,
        rows,
    )


def fetch_asset_cache(cur):
    cur.execute("SELECT id, asset_code FROM assets")
    return {code: _id for _id, code in cur.fetchall()}


def upsert_candle_series(cur, asset_id, timeframe, df_range, meta):
    cur.execute(
        """
        INSERT INTO candle_series (asset_id, timeframe, df_start, df_end, row_count, meta)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          df_start = VALUES(df_start),
          df_end = VALUES(df_end),
          row_count = VALUES(row_count),
          meta = VALUES(meta)
        """,
        (
            asset_id,
            timeframe,
            parse_timestamp(df_range.get("start")) if df_range else None,
            parse_timestamp(df_range.get("end")) if df_range else None,
            df_range.get("rows") if df_range else None,
            json.dumps(meta) if meta else None,
        ),
    )
    cur.execute(
        "SELECT id FROM candle_series WHERE asset_id = %s AND timeframe = %s",
        (asset_id, timeframe),
    )
    return cur.fetchone()[0]


def upsert_pattern_series(cur, asset_id, timeframe, meta, message):
    cur.execute(
        """
        INSERT INTO pattern_series (asset_id, timeframe, meta, message)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          meta = VALUES(meta),
          message = VALUES(message)
        """,
        (asset_id, timeframe, json.dumps(meta) if meta else None, message),
    )
    cur.execute(
        "SELECT id FROM pattern_series WHERE asset_id = %s AND timeframe = %s",
        (asset_id, timeframe),
    )
    return cur.fetchone()[0]


def load_candles(cur, asset_cache):
    candle_paths = glob(os.path.join(ROOT, "PFE_MVP", "stock-pattern", "src", "candles", "*_daily.json"))
    for path in candle_paths:
        data = load_json(path)
        sym = str(data.get("sym", "")).strip()
        if not sym:
            continue
        asset_id = asset_cache.get(sym)
        if not asset_id:
            continue
        timeframe = str(data.get("timeframe", "")).strip() or "daily"
        series_id = upsert_candle_series(cur, asset_id, timeframe, data.get("df_range"), data.get("meta"))
        candles = data.get("candles") or []
        rows = []
        for c in candles:
            if not c:
                continue
            ts = parse_timestamp(c.get("t"))
            if not ts:
                continue
            rows.append(
                (
                    series_id,
                    ts,
                    c.get("open"),
                    c.get("high"),
                    c.get("low"),
                    c.get("close"),
                    c.get("volume"),
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO candles (series_id, ts, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  open = VALUES(open),
                  high = VALUES(high),
                  low = VALUES(low),
                  close = VALUES(close),
                  volume = VALUES(volume)
                """,
                rows,
            )


def load_patterns(cur, asset_cache):
    pattern_paths = glob(os.path.join(ROOT, "PFE_MVP", "stock-pattern", "src", "patterns", "*_patterns.json"))
    for path in pattern_paths:
        data = load_json(path)
        sym = str(data.get("sym", "")).strip()
        if not sym:
            continue
        asset_id = asset_cache.get(sym)
        if not asset_id:
            continue
        timeframe = str(data.get("timeframe", "")).strip() or "daily"
        series_id = upsert_pattern_series(cur, asset_id, timeframe, data.get("meta"), data.get("message"))
        patterns = data.get("patterns") or []
        rows = []
        for p in patterns:
            if not p:
                continue
            pattern_code = str(p.get("pattern", "")).strip()
            if not pattern_code:
                continue
            rows.append(
                (
                    series_id,
                    pattern_code,
                    parse_timestamp(p.get("start")),
                    parse_timestamp(p.get("end")),
                    parse_timestamp(p.get("df_start")),
                    parse_timestamp(p.get("df_end")),
                    json.dumps(p.get("points")) if p.get("points") else None,
                    json.dumps(p.get("extra_points")) if p.get("extra_points") else None,
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO patterns (series_id, pattern_code, start_ts, end_ts, df_start, df_end, points, extra_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  df_start = VALUES(df_start),
                  df_end = VALUES(df_end),
                  points = VALUES(points),
                  extra_points = VALUES(extra_points)
                """,
                rows,
            )


def load_news(cur, asset_cache):
    news_paths = glob(os.path.join(ROOT, "NLP", "hybrid_news_financial_classified_*.json"))
    for path in news_paths:
        data = load_json(path)
        rows = []
        for item in data or []:
            if not item:
                continue
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title and not description:
                continue
            asset_ticker = str(item.get("asset_ticker", "")).strip() or None
            asset_id = asset_cache.get(asset_ticker) if asset_ticker else None
            rows.append(
                (
                    asset_id,
                    asset_ticker,
                    item.get("asset_type"),
                    item.get("query_keyword"),
                    item.get("news_category"),
                    title or None,
                    description or None,
                    item.get("source"),
                    parse_timestamp(item.get("published_at")),
                    item.get("sentiment"),
                    item.get("confidence"),
                    item.get("prob_negative"),
                    item.get("prob_positive"),
                    item.get("url"),
                    bool(item.get("is_financial")) if item.get("is_financial") is not None else None,
                    item.get("financial_confidence"),
                    item.get("financial_label"),
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO news_items (
                  asset_id, asset_ticker, asset_type, query_keyword, news_category,
                  title, description, source, published_at, sentiment, confidence,
                  prob_negative, prob_positive, url, is_financial, financial_confidence, financial_label
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  title = VALUES(title),
                  description = VALUES(description)
                """,
                rows,
            )


def load_users(cur):
    path = os.path.join(ROOT, "users_db.json")
    data = load_json(path)
    user_rows = []
    profiles = []
    sectors = set()
    user_sector_pairs = []

    for email, u in (data or {}).items():
        if not email:
            continue
        user_rows.append(
            (
                email,
                u.get("password"),
                parse_timestamp(u.get("created_at")),
                u.get("onboarding_done"),
            )
        )

    if user_rows:
        cur.executemany(
            """
            INSERT INTO users (email, password_hash, created_at, onboarding_done)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              password_hash = VALUES(password_hash),
              created_at = VALUES(created_at),
              onboarding_done = VALUES(onboarding_done)
            """,
            user_rows,
        )

    cur.execute("SELECT id, email FROM users")
    user_map = {email: _id for _id, email in cur.fetchall()}

    for email, u in (data or {}).items():
        user_id = user_map.get(email)
        if not user_id:
            continue
        profile = u.get("profile") or {}
        profiles.append(
            (
                user_id,
                profile.get("age"),
                profile.get("horizon"),
                profile.get("experience"),
                profile.get("capital"),
                profile.get("risk"),
                profile.get("strategy"),
                profile.get("goals"),
            )
        )
        for sector in profile.get("sectors") or []:
            sector = str(sector).strip()
            if sector:
                sectors.add(sector)
                user_sector_pairs.append((user_id, sector))

    if profiles:
        cur.executemany(
            """
            INSERT INTO user_profiles (user_id, age, horizon, experience, capital, risk, strategy, goals)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              age = VALUES(age),
              horizon = VALUES(horizon),
              experience = VALUES(experience),
              capital = VALUES(capital),
              risk = VALUES(risk),
              strategy = VALUES(strategy),
              goals = VALUES(goals)
            """,
            profiles,
        )

    if sectors:
        cur.executemany(
            """
            INSERT INTO sectors (name)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE name = VALUES(name)
            """,
            [(s,) for s in sorted(sectors)],
        )

    if user_sector_pairs:
        cur.execute("SELECT id, name FROM sectors")
        sector_map = {name: _id for _id, name in cur.fetchall()}
        link_rows = [(user_id, sector_map[sector]) for user_id, sector in user_sector_pairs if sector in sector_map]
        cur.executemany(
            """
            INSERT INTO user_sectors (user_id, sector_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
            """,
            link_rows,
        )


def load_anomalies(cur, asset_cache):
    path = os.path.join(ROOT, "Prediction_Anomalies", "reports", "anomaly_report.json")
    data = load_json(path)
    generated_at = parse_timestamp(data.get("generated_at"))
    cur.execute(
        """
        INSERT INTO anomaly_reports (generated_at, stats, severity_breakdown)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
          stats = VALUES(stats),
          severity_breakdown = VALUES(severity_breakdown)
        """,
        (
            generated_at,
            json.dumps(data.get("stats")) if data.get("stats") else None,
            json.dumps(data.get("severity_breakdown")) if data.get("severity_breakdown") else None,
        ),
    )
    cur.execute("SELECT id FROM anomaly_reports WHERE generated_at = %s", (generated_at,))
    report_id = cur.fetchone()[0]

    anomalies = data.get("anomalies") or []
    for a in anomalies:
        if not a:
            continue
        title = str(a.get("title", "")).strip()
        if not title:
            continue
        parts = [p.strip() for p in title.split(" - ", 1)]
        asset_label = parts[0] if parts else title
        anomaly_date = parse_date(parts[1]) if len(parts) > 1 else None
        asset_id = asset_cache.get(asset_label)
        cur.execute(
            """
            INSERT INTO anomalies (report_id, asset_id, asset_label, anomaly_date, severity, variation_pct, news_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              severity = VALUES(severity),
              variation_pct = VALUES(variation_pct),
              news_count = VALUES(news_count)
            """,
            (
                report_id,
                asset_id,
                asset_label,
                anomaly_date,
                a.get("severity"),
                parse_variation_pct(a.get("variation")),
                a.get("news_count"),
            ),
        )
        cur.execute(
            "SELECT id FROM anomalies WHERE report_id = %s AND asset_label = %s AND anomaly_date <=> %s",
            (report_id, asset_label, anomaly_date),
        )
        anomaly_id = cur.fetchone()[0]
        top_news = a.get("top_news") or []
        rows = []
        for n in top_news:
            if not n:
                continue
            n_title = str(n.get("title", "")).strip()
            n_desc = str(n.get("description", "")).strip()
            if not n_title and not n_desc:
                continue
            rows.append(
                (
                    anomaly_id,
                    n.get("timing"),
                    n.get("score"),
                    n_title or None,
                    n_desc or None,
                    n.get("source"),
                    n.get("url"),
                )
            )
        if rows:
            cur.executemany(
                """
                INSERT INTO anomaly_news (anomaly_id, timing, score, title, description, source, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )


def build_asset_map():
    asset_map = {}

    candle_paths = glob(os.path.join(ROOT, "PFE_MVP", "stock-pattern", "src", "candles", "*_daily.json"))
    for path in candle_paths:
        data = load_json(path)
        sym = str(data.get("sym", "")).strip()
        if sym:
            asset_map.setdefault(sym, None)

    pattern_paths = glob(os.path.join(ROOT, "PFE_MVP", "stock-pattern", "src", "patterns", "*_patterns.json"))
    for path in pattern_paths:
        data = load_json(path)
        sym = str(data.get("sym", "")).strip()
        if sym:
            asset_map.setdefault(sym, None)

    news_paths = glob(os.path.join(ROOT, "NLP", "hybrid_news_financial_classified_*.json"))
    for path in news_paths:
        data = load_json(path)
        for item in data or []:
            ticker = str(item.get("asset_ticker", "")).strip()
            if ticker:
                asset_map.setdefault(ticker, item.get("asset_type"))

    anomaly_path = os.path.join(ROOT, "Prediction_Anomalies", "reports", "anomaly_report.json")
    if os.path.exists(anomaly_path):
        data = load_json(anomaly_path)
        for a in data.get("anomalies") or []:
            title = str(a.get("title", "")).strip()
            if not title:
                continue
            asset_label = title.split(" - ", 1)[0].strip()
            if asset_label:
                asset_map.setdefault(asset_label, None)

    return asset_map


def main():
    parser = argparse.ArgumentParser(description="Create schema and load local data into MySQL")
    parser.add_argument("--host", default=os.getenv("MYSQL_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument("--password", default=os.getenv("MYSQL_PASSWORD", ""))
    parser.add_argument("--database", default=os.getenv("MYSQL_DATABASE"))
    args = parser.parse_args()

    if not args.database:
        raise SystemExit("Missing --database or MYSQL_DATABASE")

    conn = pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        autocommit=False,
        charset="utf8mb4",
    )

    try:
        with conn.cursor() as cur:
            run_schema(cur)
            assets = build_asset_map()
            ensure_assets(cur, assets)
            asset_cache = fetch_asset_cache(cur)
            load_candles(cur, asset_cache)
            load_patterns(cur, asset_cache)
            load_news(cur, asset_cache)
            load_users(cur)
            load_anomalies(cur, asset_cache)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
