CREATE TABLE IF NOT EXISTS assets (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  asset_code VARCHAR(32) NOT NULL UNIQUE,
  asset_type VARCHAR(64),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candle_series (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  asset_id BIGINT,
  timeframe VARCHAR(16) NOT NULL,
  df_start DATETIME,
  df_end DATETIME,
  row_count INT,
  meta JSON,
  UNIQUE KEY uniq_asset_timeframe (asset_id, timeframe),
  CONSTRAINT fk_candle_series_asset
    FOREIGN KEY (asset_id) REFERENCES assets(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candles (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  series_id BIGINT NOT NULL,
  ts DATETIME NOT NULL,
  open DOUBLE,
  high DOUBLE,
  low DOUBLE,
  close DOUBLE,
  volume DOUBLE,
  UNIQUE KEY uniq_series_ts (series_id, ts),
  KEY idx_series_ts (series_id, ts),
  CONSTRAINT fk_candles_series
    FOREIGN KEY (series_id) REFERENCES candle_series(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pattern_series (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  asset_id BIGINT,
  timeframe VARCHAR(16) NOT NULL,
  meta JSON,
  message TEXT,
  UNIQUE KEY uniq_asset_timeframe (asset_id, timeframe),
  CONSTRAINT fk_pattern_series_asset
    FOREIGN KEY (asset_id) REFERENCES assets(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS patterns (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  series_id BIGINT NOT NULL,
  pattern_code VARCHAR(16) NOT NULL,
  start_ts DATETIME,
  end_ts DATETIME,
  df_start DATETIME,
  df_end DATETIME,
  points JSON,
  extra_points JSON,
  UNIQUE KEY uniq_pattern (series_id, pattern_code, start_ts, end_ts),
  KEY idx_patterns_series (series_id),
  CONSTRAINT fk_patterns_series
    FOREIGN KEY (series_id) REFERENCES pattern_series(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS news_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  asset_id BIGINT,
  asset_ticker VARCHAR(32),
  asset_type VARCHAR(64),
  query_keyword VARCHAR(128),
  news_category VARCHAR(64),
  title TEXT,
  description TEXT,
  source VARCHAR(128),
  published_at DATETIME,
  sentiment VARCHAR(16),
  confidence DOUBLE,
  prob_negative DOUBLE,
  prob_positive DOUBLE,
  url TEXT,
  is_financial BOOLEAN,
  financial_confidence DOUBLE,
  financial_label VARCHAR(32),
  UNIQUE KEY uniq_news_url (url(255)),
  KEY idx_news_published (published_at),
  CONSTRAINT fk_news_asset
    FOREIGN KEY (asset_id) REFERENCES assets(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at DATETIME,
  onboarding_done BOOLEAN
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id BIGINT PRIMARY KEY,
  age INT,
  horizon VARCHAR(64),
  experience VARCHAR(64),
  capital DECIMAL(18,2),
  risk INT,
  strategy VARCHAR(128),
  goals TEXT,
  CONSTRAINT fk_user_profiles_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sectors (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_sectors (
  user_id BIGINT NOT NULL,
  sector_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, sector_id),
  CONSTRAINT fk_user_sectors_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_user_sectors_sector
    FOREIGN KEY (sector_id) REFERENCES sectors(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS anomaly_reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  generated_at DATETIME,
  stats JSON,
  severity_breakdown JSON,
  UNIQUE KEY uniq_generated (generated_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS anomalies (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  asset_id BIGINT,
  asset_label VARCHAR(128),
  anomaly_date DATE,
  severity VARCHAR(32),
  variation_pct DOUBLE,
  news_count INT,
  UNIQUE KEY uniq_anomaly (report_id, asset_label, anomaly_date),
  KEY idx_anomalies_severity (severity),
  CONSTRAINT fk_anomalies_report
    FOREIGN KEY (report_id) REFERENCES anomaly_reports(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_anomalies_asset
    FOREIGN KEY (asset_id) REFERENCES assets(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS anomaly_news (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  anomaly_id BIGINT NOT NULL,
  timing VARCHAR(64),
  score INT,
  title TEXT,
  description TEXT,
  source VARCHAR(128),
  url TEXT,
  CONSTRAINT fk_anomaly_news_anomaly
    FOREIGN KEY (anomaly_id) REFERENCES anomalies(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
