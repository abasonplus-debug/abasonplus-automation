#!/usr/bin/env python3
"""Free on-device CLIP semantic gate for licensed AbasonPlus photographs.

Uses two public MIT-licensed ONNX CLIP encoders in fastembed, locally within the
GitHub Actions runner. No paid inference endpoint or external user data upload.
When quality confidence is insufficient, images are rejected (fail closed).
"""
from functools import lru_cache
from pathlib import Path
import os
from tempfile import TemporaryDirectory
import numpy as np
from PIL import Image

class PhotoRelevanceGuard:
    def __init__(self):
        try:
            from fastembed import ImageEmbedding, TextEmbedding
        except ImportError as exc:
            raise RuntimeError("Install fastembed; visual semantic QA is required") from exc
        # No telemetry/network metrics: only approved model/photo GETs are needed.
        import onnxruntime
        onnxruntime.disable_telemetry_events()
        cache=Path(os.getenv("ABASONPLUS_MODEL_CACHE", ".cache/fastembed")).resolve()
        cache.mkdir(parents=True,exist_ok=True)
        self.photo = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision",cache_dir=str(cache))
        self.text = TextEmbedding(model_name="Qdrant/clip-ViT-B-32-text",cache_dir=str(cache))
        self.temp=TemporaryDirectory(prefix="abasonplus-qa-")
        self.index=0

    @staticmethod
    def normalize(vector):
        vec=np.asarray(vector,dtype=np.float32)
        return vec/max(1e-8,float(np.linalg.norm(vec)))

    @lru_cache(maxsize=256)
    def text_vector(self,prompt):
        return self.normalize(next(self.text.embed([prompt])))

    def score(self,image,scene):
        self.index+=1
        filename=str(Path(self.temp.name)/f"candidate_{self.index}.jpg")
        Image.fromarray(np.asarray(image.convert("RGB"))).resize((512,512)).save(filename,quality=82)
        vector=self.normalize(next(self.photo.embed([filename])))
        positive="A natural realistic professional color photograph showing "+scene+"."
        negatives=[
            "An old scanned archival certificate or paper document, flat on the page.",
            "A historical flat map, a diagram, or a screenshot of text.",
            "A cartoon illustration, a digital drawing or a synthetic 3D rendering.",
            "The lunar surface, spacecraft or a space probe on the moon.",
        ]
        target=float(vector@self.text_vector(positive))
        bad=max(float(vector@self.text_vector(n)) for n in negatives)
        return target,bad

    def approved(self,image,scene):
        good,bad=self.score(image,scene)
        print(f"Visual semantic QA: matching={good:.3f}, archival/artwork={bad:.3f}, margin={good-bad:.3f}",flush=True)
        # CLIP scores are heuristics, never a guarantee of factual visual match.
        return good>=0.22 and good-bad>=0.025
