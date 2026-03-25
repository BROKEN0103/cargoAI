const express = require('express');
const cors = require('cors');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const { getDb } = require('./db');

const app = express();
app.use(cors());
app.use(express.json());

const UPLOAD_DIR = path.join(__dirname, '../storage/uploads');
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOAD_DIR);
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname); // Keep original for ML annotated copy match
  }
});
const upload = multer({ storage });

app.post('/api/login', async (req, res) => {
  const { email, password } = req.body;
  try {
    const db = await getDb();
    const user = await db.get('SELECT * FROM users WHERE email = ? AND password = ?', [email, password]);
    if (user) {
      res.json({ success: true, user: { email: user.email } });
    } else {
      res.status(401).json({ error: 'Invalid credentials' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create APIs
app.post('/api/scan-cargo', upload.single('image'), async (req, res) => {
  const { declared_cargo } = req.body;
  if (!req.file) return res.status(400).json({ error: 'No image provided' });

  try {
    const db = await getDb();
    // 1. Send image to ML service
    const formData = new FormData();
    formData.append('file', fs.createReadStream(req.file.path), req.file.filename);
    formData.append('declared_cargo', declared_cargo || '');

    const mlResponse = await axios.post('http://127.0.0.1:8000/detect', formData, {
        headers: {
            ...formData.getHeaders()
        }
    });

    const { detections, risk_score, risk_level, explanation, mismatch_found, vit_analysis } = mlResponse.data;

    // 2. Store results in DB
    const insertScanQuery = `
      INSERT INTO cargo_scans (image_url, risk_score, risk_level, risk_explanation, declared_cargo, mismatch_found, vit_analysis)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `;
    const scanResult = await db.run(insertScanQuery, [
      req.file.filename, 
      risk_score, 
      risk_level, 
      explanation, 
      declared_cargo, 
      mismatch_found ? 1 : 0,
      JSON.stringify(vit_analysis || {})
    ]);
    const scanId = scanResult.lastID;

    // Insert detections
    if (detections && detections.length > 0) {
      for (const d of detections) {
         await db.run(
           'INSERT INTO detections (scan_id, object_name, confidence) VALUES (?, ?, ?)',
           [scanId, d.object, d.confidence]
         );
      }
    }

    res.json({
      scan_id: scanId,
      risk_score,
      risk_level,
      detections,
      image_filename: req.file.filename
    });
  } catch (err) {
    console.error("ML or DB Error:", err);
    res.status(500).json({ error: 'Internal Server Error', details: err.message });
  }
});

app.get('/api/history', async (req, res) => {
  try {
    const db = await getDb();
    const result = await db.all('SELECT * FROM cargo_scans ORDER BY created_at DESC');
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/dashboard', async (req, res) => {
  try {
    const db = await getDb();
    const total = await db.get('SELECT COUNT(*) as count FROM cargo_scans');
    const highRisk = await db.get("SELECT COUNT(*) as count FROM cargo_scans WHERE risk_level = 'HIGH'");
    const recent = await db.all('SELECT * FROM cargo_scans ORDER BY created_at DESC LIMIT 5');

    res.json({
      total_scans: parseInt(total.count),
      high_risk_scans: parseInt(highRisk.count),
      recent_activity: recent
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/results/:id', async (req, res) => {
  try {
    const db = await getDb();
    const scanId = req.params.id;
    const scanRow = await db.get('SELECT * FROM cargo_scans WHERE id = ?', [scanId]);
    if (!scanRow) return res.status(404).json({ error: 'Not found' });

    const detectionsRows = await db.all('SELECT * FROM detections WHERE scan_id = ?', [scanId]);

    res.json({
      scan: scanRow,
      detections: detectionsRows
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.use('/uploads', express.static(UPLOAD_DIR));

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Node backend running on port ${PORT}`);
});
