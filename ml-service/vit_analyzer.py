import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms

# ─── Vision Transformer Smuggling Pattern Analyzer ────────────────────────────
# Uses a pretrained ViT model to extract multi-head self-attention maps.
# These attention maps reveal where the transformer "looks" in the image,
# naturally highlighting:
#   • Hidden Layering: overlapping attention zones indicate stacked objects
#   • Density Clusters: high-attention regions suggest unusual concentrations
#   • Intentional Concealment: scattered attention in uniform areas = anomaly

class ViTSmuggleAnalyzer:
    """
    Uses Vision Transformer (ViT) attention maps to detect
    cargo smuggling patterns: hidden layering, density clusters, concealment.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load pretrained ViT-Base from torchvision
        from torchvision.models import vit_b_16, ViT_B_16_Weights
        self.model = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1)
        self.model.eval().to(self.device)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Register hooks on ALL encoder attention layers
        self.attention_weights = []
        for block in self.model.encoder.layers:
            block.self_attention.register_forward_hook(self._attn_hook)

    def _attn_hook(self, module, input, output):
        """Capture attention weights from each transformer block."""
        # ViT self_attention returns (attn_output, attn_weights)
        # We need to manually compute attention weights
        pass

    def _get_attention_maps(self, img_tensor):
        """Extract attention maps by manually computing through the encoder."""
        with torch.no_grad():
            # Get patch embeddings
            x = self.model._process_input(img_tensor)
            n = x.shape[0]

            # Expand the class token
            batch_class_token = self.model.class_token.expand(n, -1, -1)
            x = torch.cat([batch_class_token, x], dim=1)

            # Add position embeddings
            x = x + self.model.encoder.pos_embedding

            # Process through encoder blocks, capturing attention
            attention_maps = []
            for block in self.model.encoder.layers:
                # LayerNorm
                ln_out = block.ln_1(x)

                # Manually compute multi-head self-attention
                qkv = block.self_attention.in_proj_weight
                bias = block.self_attention.in_proj_bias
                num_heads = block.self_attention.num_heads
                head_dim = ln_out.shape[-1] // num_heads

                qkv_out = torch.nn.functional.linear(ln_out, qkv, bias)
                q, k, v = qkv_out.chunk(3, dim=-1)

                # Reshape for multi-head
                B, N, C = q.shape
                q = q.reshape(B, N, num_heads, head_dim).transpose(1, 2)
                k = k.reshape(B, N, num_heads, head_dim).transpose(1, 2)
                v = v.reshape(B, N, num_heads, head_dim).transpose(1, 2)

                # Compute attention weights
                attn = (q @ k.transpose(-2, -1)) * (head_dim ** -0.5)
                attn = torch.softmax(attn, dim=-1)
                attention_maps.append(attn.cpu().numpy())

                # Continue forward pass normally
                x = block(x)

        return attention_maps

    def analyze(self, image_path: str) -> dict:
        """
        Run ViT attention analysis on an image.
        Returns smuggling pattern indicators and generates a heatmap.
        """
        img = Image.open(image_path).convert("RGB")
        original = cv2.imread(image_path)
        h, w = original.shape[:2]

        img_tensor = self.transform(img).unsqueeze(0).to(self.device)

        # Get attention maps from all layers
        attention_maps = self._get_attention_maps(img_tensor)

        # Use the LAST layer's attention (most semantically meaningful)
        last_attn = attention_maps[-1]  # Shape: (1, num_heads, num_tokens, num_tokens)

        # Average across heads, take CLS token's attention to patches
        cls_attn = last_attn[0, :, 0, 1:]  # (num_heads, num_patches)
        avg_attn = cls_attn.mean(axis=0)     # (num_patches,)

        # Reshape to 14x14 grid (ViT-B/16 with 224x224 input = 14x14 patches)
        grid_size = int(np.sqrt(avg_attn.shape[0]))
        attn_map = avg_attn.reshape(grid_size, grid_size)

        # Normalize to 0-255
        attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)
        attn_map = (attn_map * 255).astype(np.uint8)

        # Upsample to original image size
        attn_resized = cv2.resize(attn_map, (w, h), interpolation=cv2.INTER_CUBIC)

        # ─── Pattern Detection Logic ──────────────────────────────────────
        patterns = []
        pattern_scores = {}

        # 1. HIDDEN LAYERING: Multiple distinct high-attention peaks
        threshold = int(attn_resized.max() * 0.6)
        _, binary = cv2.threshold(attn_resized, threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        num_hotspots = len(contours)

        if num_hotspots >= 3:
            patterns.append({
                "pattern": "Hidden Layering",
                "severity": "HIGH",
                "detail": f"ViT detected {num_hotspots} distinct attention layers — indicates multi-layer concealment"
            })
            pattern_scores["hidden_layering"] = min(100, num_hotspots * 20)
        elif num_hotspots >= 2:
            patterns.append({
                "pattern": "Hidden Layering",
                "severity": "MEDIUM",
                "detail": f"ViT detected {num_hotspots} overlapping attention zones — possible dual-layer stacking"
            })
            pattern_scores["hidden_layering"] = num_hotspots * 15

        # 2. DENSITY CLUSTERS: High variance in attention map
        attn_std = float(np.std(attn_resized))
        attn_max = float(np.max(attn_resized))
        density_score = int((attn_std / 80) * 100)

        if attn_std > 60:
            patterns.append({
                "pattern": "Unusual Density Cluster",
                "severity": "HIGH",
                "detail": f"Attention variance σ={attn_std:.1f} — transformer focused on concentrated density anomalies"
            })
            pattern_scores["density_cluster"] = min(100, density_score)
        elif attn_std > 35:
            patterns.append({
                "pattern": "Unusual Density Cluster",
                "severity": "MEDIUM",
                "detail": f"Moderate attention clustering σ={attn_std:.1f} — potential density irregularity"
            })
            pattern_scores["density_cluster"] = min(80, density_score)

        # 3. INTENTIONAL CONCEALMENT: Attention in normally-uniform regions
        # Check if high-attention zones exist in the image periphery
        center_attn = attn_resized[h//4:3*h//4, w//4:3*w//4].mean()
        border_attn = (attn_resized.mean() * attn_resized.size - center_attn * (h//2)*(w//2)) / (attn_resized.size - (h//2)*(w//2))
        concealment_ratio = float(border_attn / (center_attn + 1e-8))

        if concealment_ratio > 0.8:
            patterns.append({
                "pattern": "Intentional Concealment",
                "severity": "HIGH",
                "detail": f"Peripheral attention ratio {concealment_ratio:.2f} — objects concealed at cargo edges/walls"
            })
            pattern_scores["concealment"] = min(100, int(concealment_ratio * 60))
        elif concealment_ratio > 0.5:
            patterns.append({
                "pattern": "Intentional Concealment",
                "severity": "MEDIUM",
                "detail": f"Edge attention ratio {concealment_ratio:.2f} — possible wall-cavity concealment"
            })
            pattern_scores["concealment"] = min(80, int(concealment_ratio * 50))

        # ─── Generate ViT Attention Heatmap ───────────────────────────────
        heatmap_color = cv2.applyColorMap(attn_resized, cv2.COLORMAP_INFERNO)
        vit_overlay = cv2.addWeighted(original, 0.5, heatmap_color, 0.5, 0)

        # Draw contour outlines for detected hotspots
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                cv2.drawContours(vit_overlay, [cnt], -1, (0, 255, 255), 2)

        # Add label
        cv2.putText(vit_overlay, "ViT ATTENTION MAP", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        vit_output_path = image_path.replace(
            os.path.basename(image_path),
            "vit_" + os.path.basename(image_path)
        )
        cv2.imwrite(vit_output_path, vit_overlay)

        # Overall smuggling score
        smuggle_score = min(100, sum(pattern_scores.values()))

        return {
            "smuggle_score": smuggle_score,
            "patterns": patterns,
            "pattern_scores": pattern_scores,
            "hotspot_count": num_hotspots,
            "attention_variance": round(attn_std, 2),
            "concealment_ratio": round(concealment_ratio, 2),
            "vit_heatmap_path": vit_output_path
        }


import os
