import shutil
import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from vit_analyzer import ViTSmuggleAnalyzer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolov8n.pt")

# Initialize Vision Transformer Smuggling Analyzer
print("[INIT] Loading Vision Transformer (ViT-B/16) for smuggling pattern detection...")
vit_analyzer = ViTSmuggleAnalyzer()
print("[INIT] ViT model loaded successfully.")

UPLOAD_FOLDER = "../storage/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    cv2.imwrite(image_path, final)
    return final

@app.post("/detect")
async def detect(file: UploadFile = File(...), declared_cargo: str = Form("")):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Preprocess
    img = preprocess_image(file_path)

    results = model(file_path)

    detections = []
    detected_categories = set()

    for r in results:
        for box in r.boxes:
            cls_name = model.names[int(box.cls[0])]
            detections.append({
                "object": cls_name,
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy.tolist()[0]
            })
            detected_categories.add(cls_name.lower())

    # Mismatch Detection
    mismatch_found = False
    if declared_cargo:
        # Simple heuristic: if declared is 'electronics' but we see 'keyboard/cell phone' it's fine
        # If declared is 'food' but we see 'scissors/knife' -> mismatch
        declared_lower = declared_cargo.lower()
        if "food" in declared_lower and any(x in detected_categories for x in ["knife", "scissors", "tool"]):
            mismatch_found = True
        elif "furniture" in declared_lower and any(x in detected_categories for x in ["cell phone", "laptop"]):
            mismatch_found = True

    risk_score = 0
    reasons = []
    
    for d in detections:
        if d["confidence"] > 0.6:
            risk_score += 30
            reasons.append(f"High confidence detection of {d['object']}")
        
        # Category classification
        if d["object"] in ["knife", "scissors", "weapon"]:
            risk_score += 50
            reasons.append(f"PROHIBITED ITEM: {d['object']} detected")

    if len(detections) > 3:
        risk_score += 40
        reasons.append("High object density detected (possible concealment)")

    if mismatch_found:
        risk_score += 60
        reasons.append(f"CARGO MISMATCH: Detected items do not match declared '{declared_cargo}'")

    risk_level = "LOW"
    if risk_score > 80:
        risk_level = "HIGH"
    elif risk_score > 40:
        risk_level = "MEDIUM"
        
    explanation = "; ".join(reasons) if reasons else "No significant risks identified."

    # Heatmap / Annotation
    for r in results:
        annotated = r.plot()
        
        # Add a simple "Heatmap" effect for dense areas
        if len(detections) > 2:
            heatmap = np.zeros(annotated.shape[:2], dtype=np.uint8)
            for d in detections:
                x1, y1, x2, y2 = map(int, d["bbox"])
                cv2.rectangle(heatmap, (x1, y1), (x2, y2), 255, -1)
            heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            annotated = cv2.addWeighted(annotated, 0.7, heatmap_color, 0.3, 0)

        output_path = os.path.join(UPLOAD_FOLDER, "annotated_" + file.filename)
        cv2.imwrite(output_path, annotated)

    # ─── Vision Transformer Smuggling Pattern Analysis ────────────────
    try:
        vit_result = vit_analyzer.analyze(file_path)
        
        # Boost risk score based on ViT smuggling patterns
        if vit_result["smuggle_score"] > 50:
            risk_score += 40
            reasons.append(f"ViT ALERT: Smuggling pattern score {vit_result['smuggle_score']}/100")
        elif vit_result["smuggle_score"] > 25:
            risk_score += 20
            reasons.append(f"ViT WARNING: Anomalous attention patterns detected (score: {vit_result['smuggle_score']})")

        for p in vit_result.get("patterns", []):
            reasons.append(f"[{p['severity']}] {p['pattern']}: {p['detail']}")

        # Recalculate risk level
        if risk_score > 80:
            risk_level = "HIGH"
        elif risk_score > 40:
            risk_level = "MEDIUM"

        explanation = "; ".join(reasons) if reasons else "No significant risks identified."
    except Exception as e:
        print(f"[ViT ERROR] {e}")
        vit_result = {"smuggle_score": 0, "patterns": [], "pattern_scores": {}}

    return {
        "detections": detections,
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "explanation": explanation,
        "mismatch_found": mismatch_found,
        "vit_analysis": {
            "smuggle_score": vit_result.get("smuggle_score", 0),
            "patterns": vit_result.get("patterns", []),
            "hotspot_count": vit_result.get("hotspot_count", 0),
            "attention_variance": vit_result.get("attention_variance", 0),
            "concealment_ratio": vit_result.get("concealment_ratio", 0),
        },
        "file_path": file_path,
        "annotated_path": output_path
    }
