const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');
const path = require('path');

let dbInstance = null;

async function getDb() {
  if (dbInstance) return dbInstance;
  
  dbInstance = await open({
    filename: path.join(__dirname, 'cargoai.db'),
    driver: sqlite3.Database
  });

  await dbInstance.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cargo_scans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT,
      declared_cargo TEXT,
      risk_score INTEGER,
      risk_level TEXT,
      risk_explanation TEXT,
      vit_analysis TEXT,
      anomaly_score REAL,
      annotated_image_path TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS detections (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      scan_id INTEGER,
      object_name TEXT,
      confidence REAL,
      bbox TEXT,
      threat_category TEXT,
      threat_label TEXT,
      FOREIGN KEY(scan_id) REFERENCES cargo_scans(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      scan_id INTEGER,
      alert_type TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(scan_id) REFERENCES cargo_scans(id) ON DELETE CASCADE
    );

    -- Insert Demo Admin if not exists
    INSERT OR IGNORE INTO users (email, password) VALUES ('admin@cargo.ai', 'password123');
  `);
  
  return dbInstance;
}

module.exports = {
  getDb
};
