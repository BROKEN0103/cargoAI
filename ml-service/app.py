import shutil
import os
import cv2
import numpy as np
import torch
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from vit_analyzer import ViTSmuggleAnalyzer
from anomaly_detector import CargoAnomalyDetector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard YOLO and Specialized Cargo Detector
model = YOLO("yolov8n.pt") 

# Load the custom cargo detector if it exists, otherwise fall back to yolo8n
CARGO_MODEL_PATH = "model/cargo_detector.pt"
if os.path.exists(CARGO_MODEL_PATH):
    cargo_model = YOLO(CARGO_MODEL_PATH)
    print(f"[INIT] Loaded Specialized Cargo Detector from {CARGO_MODEL_PATH}")
else:
    cargo_model = model
    print("[INIT] Specialized Cargo Detector not found. Using baseline YOLOv8n.")

vit_analyzer = ViTSmuggleAnalyzer()
anomaly_engine = CargoAnomalyDetector()

UPLOAD_FOLDER = "../storage/uploads"
ANNOTATED_FOLDER = "../storage/annotated_results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANNOTATED_FOLDER, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# CARGO THREAT CLASSIFICATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════

THREAT_CATEGORIES = {
    "WEAPON": {"risk_weight": 40, "label": "⚠️ WEAPON / SHARP OBJECT"},
    "FIREARM": {"risk_weight": 60, "label": "🔫 FIREARM detected"},
    "DRUGS": {"risk_weight": 50, "label": "💊 DRUG PACKET CLUSTER"},
    "ALCOHOL": {"risk_weight": 20, "label": "🍾 ALCOHOL BOTTLE detected"},
    "SUSPICIOUS": {"risk_weight": 30, "label": "❓ SUSPICIOUS OBJECT"},
}

def detect_packet_clusters(detections):
    """Detects clusters of rectangular packets (potential drugs)."""
    packet_bboxes = [d["bounding_box"] for d in detections if "packet" in d["object_name"].lower() or "drug" in d["object_name"].lower()]
    if len(packet_bboxes) < 3:
        return False, 0
    
    # Calculate average proximity
    # For simplicity, if > 3 packets are detected, we flag it as a cluster
    return True, min(100, len(packet_bboxes) * 15)

# ═══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.post("/detect")
async def detect_legacy(file: UploadFile = File(...), declared_cargo: str = Form("")):
    # Kept for backward compatibility with frontend
    return await detect_cargo(file, declared_cargo)

@app.post("/detect-cargo")
async def detect_cargo(file: UploadFile = File(...), declared_cargo: str = Form("")):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Run Baseline + Specialized Detections
    results = cargo_model(file_path)
    detections = []
    threat_found = set()

    for r in results:
        for box in r.boxes:
            cls_name = cargo_model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            bbox = box.xyxy.tolist()[0]
            
            # Simple mapping to threat categories
            threat_cat = "SUSPICIOUS"
            if "gun" in cls_name.lower() or "firearm" in cls_name.lower() or "pistol" in cls_name.lower():
                threat_cat = "FIREARM"
            elif "knife" in cls_name.lower() or "weapon" in cls_name.lower():
                threat_cat = "WEAPON"
            elif "bottle" in cls_name.lower():
                threat_cat = "ALCOHOL"
            elif "drug" in cls_name.lower() or "packet" in cls_name.lower():
                threat_cat = "DRUGS"

            detections.append({
                "object_name": cls_name,
                "confidence": conf,
                "bounding_box": bbox,
                "threat_category": threat_cat
            })
            threat_found.add(threat_cat)

    # 2. Risk Scoring Logic
    risk_score = 0
    reasons = []

    if "FIREARM" in threat_found:
        risk_score += 60
        reasons.append("HIGH RISK: Firearm detected in cargo.")
    if "WEAPON" in threat_found:
        risk_score += 40
        reasons.append("MODERATE RISK: Sharp weapon or tool identified.")
    
    # Drug Cluster Logic
    has_packet_cluster, cluster_score = detect_packet_clusters(detections)
    if has_packet_cluster or "DRUGS" in threat_found:
        risk_score += 50
        reasons.append(f"DRUG ALERT: suspicious rectangular packet cluster (score: {cluster_score}).")

    # Alcohol Logic
    if "ALCOHOL" in threat_found:
        if declared_cargo.lower() in ["food items", "general goods"]:
            risk_score += 20
            reasons.append("ALCOHOL ALERT: Bottle-shaped objects found in restricted shipment.")

    # Multiple Objects
    if len(detections) > 4:
        risk_score += 30
        reasons.append("ANOMALY: High density of objects in internal compartment.")

    # 3. Anomaly & ViT Analysis
    anomaly_score, anomaly_details = anomaly_engine.detect_anomalies(file_path)
    if anomaly_score > 0.4:
        risk_score += int(anomaly_score * 40)
        reasons.extend(anomaly_details)

    vit_result = vit_analyzer.analyze(file_path)
    if vit_result["smuggle_score"] > 30:
        risk_score += 20
        reasons.append(f"Pattern Analysis: ViT detected anomalous layering (score: {vit_result['smuggle_score']})")

    # Final Score Normalization
    risk_score = min(100, risk_score)
    risk_level = "LOW"
    if risk_score > 60: risk_level = "HIGH"
    elif risk_score > 30: risk_level = "MEDIUM"

    # 4. Visual Output (Annotation + Heatmap)
    img = cv2.imread(file_path)
    # Density Heatmap
    heatmap = np.zeros(img.shape[:2], dtype=np.uint8)
    for d in detections:
        b = d["bounding_box"]
        cv2.rectangle(heatmap, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), 255, -1)
    
    heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
    heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    annotated = cv2.addWeighted(img, 0.7, heatmap_color, 0.3, 0)

    # Draw Boxes
    for d in detections:
        b = d["bounding_box"]
        color = (0, 0, 255) if d["threat_category"] in ["FIREARM", "WEAPON", "DRUGS"] else (0, 255, 255)
        cv2.rectangle(annotated, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
        cv2.putText(annotated, f"{d['object_name']} {d['confidence']:.2f}", 
                    (int(b[0]), int(b[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    annotated_path = os.path.join(ANNOTATED_FOLDER, "annotated_" + file.filename)
    cv2.imwrite(annotated_path, annotated)

    return {
        "detections": detections,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "explanation": " | ".join(reasons) if reasons else "No immediate threats detected.",
        "anomaly_score": anomaly_score,
        "vit_analysis": vit_result,
        "annotated_path": annotated_path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
