from dataclasses import dataclass
from typing import Dict

CV_WEIGHTS = {
    "technical_skills": 0.4,
    'experience_level': 0.25,
    'achievements': 0.2,
    'culture_fit': 0.15,
}

PROJECT_WEIGHTS = {
    'correctness': 0.3,
    'code_quality': 0.25,
    'resilience': 0.2,
    'documentation': 0.15,
    'creativity': 0.1,
}

def weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(scores.get(k, 0) * w for k, w in weights.items())

def to_percentage(score: float) -> float:
    return max(0, min(100, score * 20.0))
