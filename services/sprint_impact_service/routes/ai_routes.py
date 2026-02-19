from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import re
from collections import Counter
import math

router = APIRouter()

class StoryPointRequest(BaseModel):
    title: str
    description: str

class StoryPointResponse(BaseModel):
    suggested_points: int
    confidence: float
    reasoning: List[str]
    complexity_indicators: Dict[str, int]

# Complexity keywords and their weights
COMPLEXITY_KEYWORDS = {
    # High complexity (5-8 points)
    "algorithm": 8,
    "optimization": 7,
    "migration": 7,
    "refactor": 6,
    "integration": 7,
    "api": 5,
    "database": 6,
    "authentication": 7,
    "authorization": 7,
    "security": 7,
    "performance": 6,
    "scalability": 7,
    "architecture": 8,
    "framework": 6,
    "third-party": 6,
    "multiple": 5,
    "complex": 7,
    
    # Medium complexity (3-5 points)
    "implement": 4,
    "create": 3,
    "add": 3,
    "update": 4,
    "modify": 4,
    "enhance": 4,
    "improve": 4,
    "feature": 4,
    "component": 4,
    "service": 5,
    "endpoint": 4,
    "validation": 4,
    "testing": 4,
    
    # Low complexity (1-3 points)
    "fix": 2,
    "bug": 2,
    "typo": 1,
    "update": 3,
    "change": 2,
    "remove": 2,
    "delete": 2,
    "simple": 2,
    "minor": 2,
    "small": 2,
    "text": 2,
    "label": 2,
    "styling": 2,
    "css": 2,
    "ui": 3
}

# Interface/Integration indicators
INTERFACE_KEYWORDS = [
    "frontend", "backend", "ui", "ux", "interface", "screen", 
    "page", "form", "modal", "dialog", "api", "endpoint",
    "rest", "graphql", "websocket", "microservice"
]

# Technology stack indicators
TECH_KEYWORDS = [
    "react", "vue", "angular", "node", "python", "java",
    "mongodb", "postgresql", "mysql", "redis", "docker",
    "kubernetes", "aws", "azure", "gcp"
]

def extract_text_features(text: str) -> Dict[str, any]:
    """Extract features from text using TF-IDF-like approach"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    
    # Tokenize
    words = text.split()
    
    # Count word frequencies
    word_freq = Counter(words)
    
    # Calculate complexity score
    complexity_score = 0
    matched_keywords = {}
    
    for word in words:
        if word in COMPLEXITY_KEYWORDS:
            complexity_score += COMPLEXITY_KEYWORDS[word]
            matched_keywords[word] = matched_keywords.get(word, 0) + 1
    
    # Count interface indicators
    interface_count = sum(1 for word in words if word in INTERFACE_KEYWORDS)
    
    # Count tech stack mentions
    tech_count = sum(1 for word in words if word in TECH_KEYWORDS)
    
    # Calculate text length factor
    text_length = len(words)
    length_factor = min(text_length / 20, 2.0)  # Cap at 2x multiplier
    
    return {
        "complexity_score": complexity_score,
        "matched_keywords": matched_keywords,
        "interface_count": interface_count,
        "tech_count": tech_count,
        "text_length": text_length,
        "length_factor": length_factor
    }

def calculate_story_points(title_features: Dict, desc_features: Dict) -> tuple:
    """Calculate story points based on extracted features"""
    
    # Combine scores
    total_complexity = title_features["complexity_score"] * 2 + desc_features["complexity_score"]
    total_interfaces = title_features["interface_count"] + desc_features["interface_count"]
    total_tech = title_features["tech_count"] + desc_features["tech_count"]
    
    # Base score
    base_score = total_complexity / 10
    
    # Add interface complexity
    if total_interfaces > 3:
        base_score += 3
    elif total_interfaces > 1:
        base_score += 1.5
    
    # Add tech stack complexity
    if total_tech > 2:
        base_score += 2
    elif total_tech > 0:
        base_score += 1
    
    # Apply length factor
    avg_length_factor = (title_features["length_factor"] + desc_features["length_factor"]) / 2
    base_score *= avg_length_factor
    
    # Normalize to 3-15 range
    if base_score < 3:
        suggested_points = 3
    elif base_score > 15:
        suggested_points = 15
    else:
        suggested_points = round(base_score)
    
    # Calculate confidence (0-1)
    keyword_count = len(title_features["matched_keywords"]) + len(desc_features["matched_keywords"])
    confidence = min(keyword_count / 5, 1.0)
    
    # Generate reasoning
    reasoning = []
    
    all_keywords = {**title_features["matched_keywords"], **desc_features["matched_keywords"]}
    if all_keywords:
        top_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        reasoning.append(f"Detected complexity keywords: {', '.join([k for k, v in top_keywords])}")
    
    if total_interfaces > 0:
        reasoning.append(f"Involves {total_interfaces} interface(s)/integration(s)")
    
    if total_tech > 0:
        reasoning.append(f"Uses {total_tech} technology stack(s)")
    
    avg_length = (title_features["text_length"] + desc_features["text_length"]) / 2
    if avg_length > 30:
        reasoning.append("Detailed description suggests higher complexity")
    elif avg_length < 10:
        reasoning.append("Brief description suggests simpler task")
    
    if not reasoning:
        reasoning.append("Limited information - conservative estimate")
    
    return suggested_points, confidence, reasoning, all_keywords

@router.post("/predict", response_model=StoryPointResponse)
async def predict_story_points(request: StoryPointRequest):
    """Predict story points using TF-IDF-like NLP analysis"""
    
    if not request.title or not request.description:
        raise HTTPException(status_code=400, detail="Title and description are required")
    
    # Extract features
    title_features = extract_text_features(request.title)
    desc_features = extract_text_features(request.description)
    
    # Calculate story points
    suggested_points, confidence, reasoning, keywords = calculate_story_points(
        title_features, desc_features
    )
    
    return StoryPointResponse(
        suggested_points=suggested_points,
        confidence=confidence,
        reasoning=reasoning,
        complexity_indicators=keywords
    )

@router.post("/analyze-batch")
async def analyze_batch(items: List[StoryPointRequest]):
    """Analyze multiple items at once"""
    results = []
    
    for item in items:
        title_features = extract_text_features(item.title)
        desc_features = extract_text_features(item.description)
        
        suggested_points, confidence, reasoning, keywords = calculate_story_points(
            title_features, desc_features
        )
        
        results.append({
            "title": item.title,
            "suggested_points": suggested_points,
            "confidence": confidence
        })
    
    return {"results": results}

@router.get("/complexity-keywords")
async def get_complexity_keywords():
    """Get list of complexity keywords and their weights"""
    return {
        "keywords": COMPLEXITY_KEYWORDS,
        "interfaces": INTERFACE_KEYWORDS,
        "technologies": TECH_KEYWORDS
    }