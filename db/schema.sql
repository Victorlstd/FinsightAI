CREATE TABLE IF NOT EXISTS assets (
  id BIGSERIAL PRIMARY KEY,
  asset_code TEXT NOT NULL UNIQUE,
  asset_type TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS candle_series (
  id BIGSERIAL PRIMARY KEY,
  asset_id BIGINT REFERENCES assets(id),
  timeframe TEXT NOT NULL,
  df_start TIMESTAMP,
  df_end TIMESTAMP,
  row_count INT,
  meta JSONB,
  UNIQUE (asset_id, timeframe)
);

CREATE TABLE IF NOT EXISTS candles (
  id BIGSERIAL PRIMARY KEY,
  series_id BIGINT NOT NULL REFERENCES candle_series(id) ON DELETE CASCADE,
  ts TIMESTAMP NOT NULL,
  open DOUBLE PRECISION,
  high DOUBLE PRECISION,
  low DOUBLE PRECISION,
  close DOUBLE PRECISION,
  volume DOUBLE PRECISION,
  UNIQUE (series_id, ts)
);

CREATE TABLE IF NOT EXISTS pattern_series (
  id BIGSERIAL PRIMARY KEY,
  asset_id BIGINT REFERENCES assets(id),
  timeframe TEXT NOT NULL,
  meta JSONB,
  message TEXT,
  UNIQUE (asset_id, timeframe)
);

CREATE TABLE IF NOT EXISTS patterns (
  id BIGSERIAL PRIMARY KEY,
  series_id BIGINT NOT NULL REFERENCES pattern_series(id) ON DELETE CASCADE,
  pattern_code TEXT NOT NULL,
  start_ts TIMESTAMP,
  end_ts TIMESTAMP,
  df_start TIMESTAMP,
  df_end TIMESTAMP,
  points JSONB,
  extra_points JSONB,
  UNIQUE (series_id, pattern_code, start_ts, end_ts)
);

CREATE TABLE IF NOT EXISTS news_items (
  id BIGSERIAL PRIMARY KEY,
  asset_id BIGINT REFERENCES assets(id),
  asset_ticker TEXT,
  asset_type TEXT,
  query_keyword TEXT,
  news_category TEXT,
  title TEXT,
  description TEXT,
  source TEXT,
  published_at TIMESTAMPTZ,
  sentiment TEXT,
  confidence DOUBLE PRECISION,
  prob_negative DOUBLE PRECISION,
  prob_positive DOUBLE PRECISION,
  url TEXT,
  is_financial BOOLEAN,
  financial_confidence DOUBLE PRECISION,
  financial_label TEXT,
  UNIQUE (url)
);

CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ,
  onboarding_done BOOLEAN
);

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  age INT,
  horizon TEXT,
  experience TEXT,
  capital NUMERIC,
  risk INT,
  strategy TEXT,
  goals TEXT
);

CREATE TABLE IF NOT EXISTS sectors (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_sectors (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sector_id BIGINT NOT NULL REFERENCES sectors(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, sector_id)
);

CREATE TABLE IF NOT EXISTS anomaly_reports (
  id BIGSERIAL PRIMARY KEY,
  generated_at TIMESTAMPTZ,
  stats JSONB,
  severity_breakdown JSONB,
  UNIQUE (generated_at)
);

CREATE TABLE IF NOT EXISTS anomalies (
  id BIGSERIAL PRIMARY KEY,
  report_id BIGINT NOT NULL REFERENCES anomaly_reports(id) ON DELETE CASCADE,
  asset_id BIGINT REFERENCES assets(id),
  asset_label TEXT,
  anomaly_date DATE,
  severity TEXT,
  variation_pct DOUBLE PRECISION,
  news_count INT,
  UNIQUE (report_id, asset_label, anomaly_date)
);

CREATE TABLE IF NOT EXISTS anomaly_news (
  id BIGSERIAL PRIMARY KEY,
  anomaly_id BIGINT NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
  timing TEXT,
  score INT,
  title TEXT,
  description TEXT,
  source TEXT,
  url TEXT
);

CREATE INDEX IF NOT EXISTS idx_candles_series_ts ON candles (series_id, ts);
CREATE INDEX IF NOT EXISTS idx_patterns_series ON patterns (series_id);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_items (published_at);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON anomalies (severity);
