# 🛡️ AI Cargo Risk Intelligence Platform

> **Dual-Model AI System** for cargo smuggling detection using **YOLOv8** (Object Detection) and **Vision Transformer ViT-B/16** (Attention-Based Pattern Analysis).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│                     http://localhost:3000                        │
│  Login → Upload → Dashboard → Scan History → Results (Dual AI)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (Node.js + Express)                   │
│                     http://localhost:5000                        │
│         Authentication │ File Upload │ SQLite Storage            │
└────────────────────────────┬────────────────────────────────────┘
                             │ Multipart POST
┌────────────────────────────▼────────────────────────────────────┐
│                  ML SERVICE (Python + FastAPI)                    │
│                     http://localhost:8000                        │
│                                                                  │
│  ┌──────────────┐    ┌───────────────────────────────────────┐  │
│  │   YOLOv8n    │    │  Vision Transformer (ViT-B/16)        │  │
│  │              │    │                                       │  │
│  │ • Object     │    │ • Attention Map Extraction             │  │
│  │   Detection  │    │ • Hidden Layering Detection            │  │
│  │ • Bounding   │    │ • Density Cluster Analysis             │  │
│  │   Boxes      │    │ • Concealment Pattern Detection        │  │
│  │ • Class      │    │ • INFERNO Heatmap Generation           │  │
│  │   Labels     │    │                                       │  │
│  └──────────────┘    └───────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|:---|:---|
| **Object Detection** | YOLOv8 detects and localizes cargo objects with bounding boxes |
| **Object Classification** | Items classified as Normal, Suspicious, or Prohibited |
| **Smuggling Pattern Detection** | ViT attention maps detect hidden layering, density clusters, concealment |
| **Cargo Mismatch Detection** | Compares declared cargo type vs detected objects |
| **Risk Scoring** | Composite 0–100 score combining both models |
| **Heatmap Visualization** | YOLO overlay + ViT INFERNO attention heatmap side-by-side |
| **AI Briefing** | Natural language explanation of all findings |
| **Image Preprocessing** | CLAHE contrast enhancement for X-ray clarity |
| **Admin Authentication** | Secure login with session management |
| **Scan History & Dashboard** | Full audit trail with statistics |

---

## 🧠 How the Models Work

### Model 1: YOLOv8 — Object Detection
- Detects specific objects (knife, phone, laptop, etc.)
- Assigns confidence scores and bounding boxes
- Classifies objects as **Normal** / **Suspicious** / **Prohibited**

### Model 2: Vision Transformer (ViT-B/16) — Pattern Analysis
- Splits image into 196 patches (14×14 grid)
- 12 encoder layers with multi-head self-attention (86M parameters)
- Extracts CLS token attention → reveals where the AI "focuses"
- Detects 3 smuggling patterns:
  - **Hidden Layering** — multiple overlapping attention zones
  - **Density Clusters** — high attention variance (σ)
  - **Intentional Concealment** — abnormal edge-vs-center ratio

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | Next.js 14, React, Tailwind CSS, Lucide Icons, Axios |
| **Backend API** | Node.js, Express.js, SQLite, Multer, CORS |
| **ML Service** | Python, FastAPI, Uvicorn |
| **Object Detection** | YOLOv8n (Ultralytics) |
| **Pattern Analysis** | ViT-B/16 (PyTorch + TorchVision) |
| **Image Processing** | OpenCV, Pillow, NumPy |
| **Database** | SQLite (zero-config, embedded) |

---

## 📁 Project Structure

```
CargoAi/
├── frontend/               # Next.js Dashboard
│   ├── components/
│   │   └── Layout.js       # Protected sidebar layout
│   ├── pages/
│   │   ├── login.js        # Admin authentication
│   │   ├── index.js        # Upload scan (with declared cargo)
│   │   ├── dashboard.js    # Command center stats
│   │   ├── history.js      # Scan audit log
│   │   └── results/[id].js # Dual-model results view
│   ├── services/
│   │   └── api.js          # API client
│   └── styles/
│       └── globals.css     # Tailwind config
│
├── backend/                # Node.js API Server
│   ├── index.js            # Express routes + ML proxy
│   ├── db.js               # SQLite schema + connection
│   └── package.json
│
├── ml-service/             # Python ML Engine
│   ├── app.py              # FastAPI (YOLOv8 + ViT pipeline)
│   ├── vit_analyzer.py     # Vision Transformer module
│   ├── requirements.txt
│   └── yolov8n.pt          # YOLOv8 weights
│
└── storage/
    └── uploads/            # Raw + annotated + ViT images
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** ≥ 18
- **Python** ≥ 3.9
- **pip** + **venv**

### 1. ML Service (Terminal 1)
```bash
cd ml-service
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app:app --port 8000
```

### 2. Backend (Terminal 2)
```bash
cd backend
npm install
node --watch index.js
```

### 3. Frontend (Terminal 3)
```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard
Visit **http://localhost:3000**

**Login:** `admin@cargo.ai` / `password123`

---

## 🔄 System Flow

```
1. Analyst logs in → admin@cargo.ai
2. Uploads cargo image + selects declared cargo category
3. Backend receives image → forwards to ML Service
4. ML Service runs:
   a. CLAHE preprocessing (contrast enhancement)
   b. YOLOv8 object detection → bounding boxes + labels
   c. ViT-B/16 attention analysis → heatmap + patterns
   d. Mismatch check (declared vs detected)
   e. Risk score computation (0–100)
5. Results stored in SQLite
6. Frontend displays dual-model results:
   - YOLOv8 annotated image + ViT attention heatmap
   - Smuggle score + pattern cards + AI briefing
```

---

## 📊 Results Dashboard Preview

The results page shows:
- ⚡ **Risk Level** (LOW / MEDIUM / HIGH) with composite score
- 🔴 **Mismatch Alert** (if declared cargo doesn't match detected objects)
- 🔵 **YOLOv8 Output** — annotated image with bounding boxes
- 🟣 **ViT Attention Map** — INFERNO heatmap highlighting suspicious regions
- 📋 **Smuggling Patterns** — Hidden Layering / Density Clusters / Concealment
- 📈 **Stats** — Hotspot count, Attention Variance (σ), Concealment Ratio
- 💬 **AI Briefing** — natural language explanation

---

## 👥 Team

Built for hackathon demonstration of AI-powered cargo intelligence.

---

## 📜 License

MIT
