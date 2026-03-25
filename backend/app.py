from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolov8n.pt")

WEAPONS = {'knife', 'scissors', 'gun'}
ELECTRONICS = {'tv', 'laptop', 'mouse', 'keyboard', 'cell phone'}

@app.post("/upload")
async def process_cargo_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {e}")

    results = model(image)
    
    detected_objects = []
    has_weapon = False
    has_electronics = False

    names = model.names

    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = names[cls_id]
            
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            detected_objects.append({
                "name": name,
                "confidence": conf,
                "box": [x1, y1, x2, y2]
            })
            
            if name in WEAPONS:
                has_weapon = True
            if name in ELECTRONICS:
                has_electronics = True

    # Risk Logic
    risk_level = "LOW"
    explanation = "Routine cargo detected. No anomalies found."
    score = 10
    
    context_mismatch = len(detected_objects) > 8

    if has_weapon:
        risk_level = "HIGH"
        score = 95
        explanation = "High-risk object detected (weapon-like). Immediate inspection required."
    elif has_electronics and context_mismatch:
        risk_level = "HIGH"
        score = 85
        explanation = "Dense object cluster detected in cargo containing electronics. Potential smuggling attempt."
    elif has_electronics:
        risk_level = "MEDIUM"
        score = 65
        explanation = "Electronics detected. Verify documentation matches manifest."
    elif context_mismatch:
        risk_level = "MEDIUM"
        score = 55
        explanation = "High density of random objects detected. Possible context mismatch."

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "explanation": explanation,
        "objects": detected_objects,
        "count": len(detected_objects)
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
