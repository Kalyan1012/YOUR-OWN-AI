import pytest
import numpy as np
from app.search import BruteForceEngine, KDTreeEngine

@pytest.fixture
def sample_data():
    # Provide a consistent, predictable set of 2D coordinates for testing
    return [
        {"name": "Point_A", "vector": [0.1, 0.2], "content": "Apple data"},
        {"name": "Point_B", "vector": [0.9, 0.8], "content": "Cake data"},
        {"name": "Point_C", "vector": [0.15, 0.25], "content": "Close to Apple data"}
    ]

def test_brute_force_engine(sample_data):
    engine = BruteForceEngine()
    for item in sample_data:
        engine.add(item["name"], item["vector"], item["content"])
        
    # Query point [0.11, 0.21] is physically closest to Point_A
    name, dist, content = engine.search([0.11, 0.21])
    
    assert name == "Point_A"
    assert content == "Apple data"
    assert dist < 0.05

def test_kd_tree_engine(sample_data):
    engine = KDTreeEngine()
    # Build the structural tree splits from our data list
    engine.root = engine.build(sample_data)
    
    # Query point [0.88, 0.79] is physically closest to Point_B
    name, dist, content = engine.search([0.88, 0.79])
    
    assert name == "Point_B"
    assert content == "Cake data"
    assert dist < 0.05