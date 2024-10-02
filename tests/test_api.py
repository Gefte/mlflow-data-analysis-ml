from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Estou saudável"}

def test_validate_model():
    response = client.get("/api/validate_model")
    assert response.status_code == 200
    assert "Modelo existe" in response.json()["status"]

def test_predict():
    # Dados de teste para previsão
    test_data = {
        "alcohol": 13.0,
        "malic_acid": 1.0,
        "ash": 2.0,
        "alcalinity_of_ash": 15.0,
        "magnesium": 100.0,
        "total_phenols": 2.5,
        "flavanoids": 1.5,
        "nonflavanoid_phenols": 0.2,
        "proanthocyanins": 1.0,
        "hue": 0.5,
        "od280_od315_of_diluted_wines": 2.0,
        "proline": 3.0
    }
    
    response = client.post("/api/predict", json=test_data)
    assert response.status_code == 200
    assert "prediction" in response.json()
