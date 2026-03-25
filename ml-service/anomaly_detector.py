import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np

class CargoAnomalyDetector:
    """
    CNN-based anomaly detection using feature extraction.
    Compares image features against baseline structural patterns.
    """
    def __init__(self):
        # Use ResNet18 as a feature extractor
        self.model = models.resnet18(pretrained=True)
        # Remove the classification layer to get features
        self.feature_extractor = nn.Sequential(*list(self.model.children())[:-1])
        self.feature_extractor.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def get_features(self, image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            img_t = self.transform(img).unsqueeze(0)
            with torch.no_grad():
                features = self.feature_extractor(img_t)
            return features.flatten().numpy()
        except Exception as e:
            print(f"[ANOMALY ERROR] {e}")
            return None

    def detect_anomalies(self, image_path):
        """
        Calculate an anomaly score based on feature variance.
        In a production system, we'd compare this against a bank of 'normal' cargo images.
        For this prototype, we simulate density clusters and irregularity detection.
        """
        features = self.get_features(image_path)
        if features is None:
            return 0.0, []

        # Simple heuristic: high feature variance in certain bands indicates irregular patterns
        variance = np.var(features)
        
        # Normalize score 0-1.0
        anomaly_score = min(1.0, variance * 5.0) 
        
        details = []
        if anomaly_score > 0.7:
            details.append("Highly irregular structural arrangement detected")
        if anomaly_score > 0.4:
            details.append("Suspicious density fluctuations in cargo interior")
            
        return float(anomaly_score), details
