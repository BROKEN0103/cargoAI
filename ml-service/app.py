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

# ═══════════════════════════════════════════════════════════════════════
# CARGO THREAT CLASSIFICATION SYSTEM
# Maps COCO class names → smuggling-relevant threat categories
# ═══════════════════════════════════════════════════════════════════════

THREAT_CATEGORIES = {
    # ── WEAPONS & SHARP OBJECTS ──────────────────────────────────────
    "WEAPON": {
        "coco_classes": ["knife", "scissors", "baseball bat", "tennis racket", "surfboard"],
        "risk_weight": 70,
        "label": "⚠️ WEAPON / SHARP OBJECT",
        "description": "Sharp or blunt weapon capable of causing harm"
    },
    # ── FIREARMS (shape-inferred from gun-like silhouettes) ─────────
    "FIREARM": {
        "coco_classes": [],  # No COCO class — detected via shape analysis
        "risk_weight": 95,
        "label": "🔫 FIREARM / GUN-LIKE OBJECT",
        "description": "Object with firearm-like silhouette detected via contour analysis"
    },
    # ── ALCOHOL & LIQUID CONTAINERS ─────────────────────────────────
    "ALCOHOL": {
        "coco_classes": ["bottle", "wine glass", "cup"],
        "risk_weight": 40,
        "label": "🍾 ALCOHOL / UNDECLARED LIQUIDS",
        "description": "Bottles or liquid containers — possible undeclared alcohol or chemicals"
    },
    # ── DRUGS PARAPHERNALIA ─────────────────────────────────────────
    "DRUGS_PARAPHERNALIA": {
        "coco_classes": ["vase", "potted plant"],
        "risk_weight": 50,
        "label": "💊 DRUGS / NARCOTICS INDICATOR",
        "description": "Item associated with drug concealment (plant matter, containers)"
    },
    # ── UNDECLARED ELECTRONICS ──────────────────────────────────────
    "ELECTRONICS": {
        "coco_classes": ["cell phone", "laptop", "remote", "keyboard", "mouse", "tv", "microwave"],
        "risk_weight": 30,
        "label": "📱 UNDECLARED ELECTRONICS",
        "description": "Electronic device — common smuggling target for tax evasion"
    },
    # ── CONCEALMENT CONTAINERS ─────────────────────────────────────
    "CONCEALMENT": {
        "coco_classes": ["backpack", "handbag", "suitcase", "umbrella", "teddy bear"],
        "risk_weight": 35,
        "label": "🧳 CONCEALMENT CONTAINER",
        "description": "Container that could hide contraband within cargo"
    },
    # ── HUMAN TRAFFICKING INDICATORS ───────────────────────────────
    "HUMAN_INDICATOR": {
        "coco_classes": ["person", "tie", "toothbrush", "hair drier"],
        "risk_weight": 80,
        "label": "🚨 HUMAN PRESENCE INDICATOR",
        "description": "Human or personal item in cargo — possible trafficking"
    },
    # ── ANIMALS (protected species trafficking) ────────────────────
    "ANIMAL": {
        "coco_classes": ["bird", "cat", "dog", "horse", "sheep", "cow", "elephant",
                         "bear", "zebra", "giraffe"],
        "risk_weight": 60,
        "label": "🐾 ANIMAL / WILDLIFE",
        "description": "Animal detected — possible illegal wildlife trafficking"
    },
    # ── FOOD & ORGANIC (biosecurity) ───────────────────────────────
    "ORGANIC": {
        "coco_classes": ["banana", "apple", "sandwich", "orange", "broccoli",
                         "carrot", "hot dog", "pizza", "donut", "cake"],
        "risk_weight": 20,
        "label": "🍎 ORGANIC / FOOD ITEM",
        "description": "Food or organic matter — biosecurity and quarantine concern"
    },
    # ── VEHICLES (stolen / illegal export) ─────────────────────────
    "VEHICLE": {
        "coco_classes": ["bicycle", "car", "motorcycle", "airplane", "bus",
                         "train", "truck", "boat"],
        "risk_weight": 45,
        "label": "🚗 VEHICLE / PARTS",
        "description": "Vehicle or parts — possible stolen goods or undeclared export"
    },
}

# Build reverse lookup: COCO class → threat category
COCO_TO_THREAT = {}
for cat_name, cat_data in THREAT_CATEGORIES.items():
    for coco_cls in cat_data["coco_classes"]:
        COCO_TO_THREAT[coco_cls] = cat_name

# Mismatch rules: declared category → what should NOT be found
MISMATCH_RULES = {
    "food items": ["WEAPON", "FIREARM", "ELECTRONICS", "ANIMAL", "HUMAN_INDICATOR", "VEHICLE"],
    "electronics": ["WEAPON", "FIREARM", "ALCOHOL", "DRUGS_PARAPHERNALIA", "ANIMAL", "HUMAN_INDICATOR"],
    "furniture": ["WEAPON", "FIREARM", "ELECTRONICS", "ALCOHOL", "DRUGS_PARAPHERNALIA", "HUMAN_INDICATOR"],
    "textiles": ["WEAPON", "FIREARM", "ELECTRONICS", "ALCOHOL", "DRUGS_PARAPHERNALIA", "ANIMAL"],
    "chemicals": ["WEAPON", "FIREARM", "HUMAN_INDICATOR", "ANIMAL", "ORGANIC"],
    "general goods": ["WEAPON", "FIREARM", "DRUGS_PARAPHERNALIA", "HUMAN_INDICATOR", "ANIMAL"],
}


def preprocess_image(image_path):
    """CLAHE contrast enhancement for X-ray / low-contrast images."""
    img = cv2.imread(image_path)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    cv2.imwrite(image_path, final)
    return final


def detect_weapon_shapes(image_path):
    """
    Shape-based firearm/weapon silhouette detection.
    Looks for elongated L-shaped or gun-like contours that YOLO can't classify.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return []

    # Edge detection
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    dilated = cv2.dilate(edges, None, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    weapon_shapes = []
    h, w = img.shape

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < (h * w * 0.005) or area > (h * w * 0.4):
            continue

        # Get bounding rect and aspect ratio
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect_ratio = max(bw, bh) / (min(bw, bh) + 1e-6)

        # Get hull solidity (filled area vs convex hull)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / (hull_area + 1e-6)

        # Gun-like features:
        # - Elongated (aspect ratio > 2.5)
        # - Not fully solid (solidity < 0.8 = has gaps like trigger guard)
        # - Has angular corners (low circularity)
        perimeter = cv2.arcLength(cnt, True)
        circularity = 4 * np.pi * area / (perimeter ** 2 + 1e-6)

        is_weapon_like = (
            aspect_ratio > 2.2 and
            solidity < 0.82 and
            circularity < 0.35
        )

        if is_weapon_like:
            weapon_shapes.append({
                "bbox": [float(x), float(y), float(x + bw), float(y + bh)],
                "aspect_ratio": round(float(aspect_ratio), 2),
                "solidity": round(float(solidity), 2),
                "circularity": round(float(circularity), 3),
                "confidence": round(min(0.85, aspect_ratio * 0.15 + (1 - solidity) * 0.5), 2)
            })

    return weapon_shapes


@app.post("/detect")
async def detect(file: UploadFile = File(...), declared_cargo: str = Form("")):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Preprocess
    img = preprocess_image(file_path)

    # 2. YOLOv8 Detection
    results = model(file_path)

    detections = []
    detected_categories = set()
    threat_flags = []

    for r in results:
        for box in r.boxes:
            cls_name = model.names[int(box.cls[0])]
            conf = float(box.conf[0])
            bbox = box.xyxy.tolist()[0]

            # Map to threat category
            threat_cat = COCO_TO_THREAT.get(cls_name, "UNKNOWN")
            threat_info = THREAT_CATEGORIES.get(threat_cat, {})

            detections.append({
                "object": cls_name,
                "confidence": conf,
                "bbox": bbox,
                "threat_category": threat_cat,
                "threat_label": threat_info.get("label", cls_name),
            })
            detected_categories.add(cls_name.lower())

            if threat_cat != "UNKNOWN":
                threat_flags.append(threat_cat)

    # 3. Shape-based weapon/firearm detection
    weapon_shapes = detect_weapon_shapes(file_path)
    for ws in weapon_shapes:
        detections.append({
            "object": "gun-like silhouette",
            "confidence": ws["confidence"],
            "bbox": ws["bbox"],
            "threat_category": "FIREARM",
            "threat_label": THREAT_CATEGORIES["FIREARM"]["label"],
        })
        threat_flags.append("FIREARM")

    # 4. Mismatch Detection (expanded)
    mismatch_found = False
    mismatch_details = []
    if declared_cargo:
        declared_lower = declared_cargo.lower()
        forbidden = MISMATCH_RULES.get(declared_lower, MISMATCH_RULES.get("general goods", []))
        for flag in set(threat_flags):
            if flag in forbidden:
                mismatch_found = True
                label = THREAT_CATEGORIES[flag]["label"]
                mismatch_details.append(f"{label} found in '{declared_cargo}' shipment")

    # 5. Risk Scoring
    risk_score = 0
    reasons = []

    # Score per detection based on threat category
    scored_categories = set()
    for d in detections:
        cat = d.get("threat_category", "UNKNOWN")
        if cat in THREAT_CATEGORIES and cat not in scored_categories:
            weight = THREAT_CATEGORIES[cat]["risk_weight"]
            risk_score += weight
            reasons.append(f"{THREAT_CATEGORIES[cat]['label']}: {THREAT_CATEGORIES[cat]['description']}")
            scored_categories.add(cat)
        elif d["confidence"] > 0.6 and cat == "UNKNOWN":
            risk_score += 10
            reasons.append(f"Unclassified object: {d['object']} (conf: {d['confidence']:.0%})")

    # Density penalty
    if len(detections) > 5:
        risk_score += 30
        reasons.append(f"High object density ({len(detections)} items) — possible concealment")

    # Mismatch penalty
    if mismatch_found:
        risk_score += 50
        for md in mismatch_details:
            reasons.append(f"CARGO MISMATCH: {md}")

    risk_level = "LOW"
    if risk_score > 80:
        risk_level = "CRITICAL"
    elif risk_score > 50:
        risk_level = "HIGH"
    elif risk_score > 25:
        risk_level = "MEDIUM"

    explanation = "; ".join(reasons) if reasons else "No significant risks identified. Cargo appears compliant."

    # 6. Annotated Image with threat labels
    for r in results:
        annotated = r.plot()

        # Draw weapon shape detections
        for ws in weapon_shapes:
            x1, y1, x2, y2 = map(int, ws["bbox"])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(annotated, f"FIREARM? {ws['confidence']:.0%}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Heatmap overlay for dense areas
        if len(detections) > 2:
            heatmap = np.zeros(annotated.shape[:2], dtype=np.uint8)
            for d in detections:
                bx1, by1, bx2, by2 = map(int, d["bbox"])
                cv2.rectangle(heatmap, (bx1, by1), (bx2, by2), 255, -1)
            heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            annotated = cv2.addWeighted(annotated, 0.7, heatmap_color, 0.3, 0)

        output_path = os.path.join(UPLOAD_FOLDER, "annotated_" + file.filename)
        cv2.imwrite(output_path, annotated)

    # 7. Vision Transformer Smuggling Pattern Analysis
    try:
        vit_result = vit_analyzer.analyze(file_path)

        if vit_result["smuggle_score"] > 50:
            risk_score += 40
            reasons.append(f"ViT ALERT: Smuggling pattern score {vit_result['smuggle_score']}/100")
        elif vit_result["smuggle_score"] > 25:
            risk_score += 20
            reasons.append(f"ViT WARNING: Anomalous attention patterns (score: {vit_result['smuggle_score']})")

        for p in vit_result.get("patterns", []):
            reasons.append(f"[{p['severity']}] {p['pattern']}: {p['detail']}")

        # Recalculate after ViT
        if risk_score > 80:
            risk_level = "CRITICAL"
        elif risk_score > 50:
            risk_level = "HIGH"
        elif risk_score > 25:
            risk_level = "MEDIUM"

        explanation = "; ".join(reasons) if reasons else "No significant risks identified."
    except Exception as e:
        print(f"[ViT ERROR] {e}")
        vit_result = {"smuggle_score": 0, "patterns": [], "pattern_scores": {}}

    # 8. Build unique threat summary
    unique_threats = list(scored_categories)

    return {
        "detections": detections,
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "explanation": explanation,
        "mismatch_found": mismatch_found,
        "mismatch_details": mismatch_details,
        "threat_flags": unique_threats,
        "weapon_shapes_detected": len(weapon_shapes),
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

