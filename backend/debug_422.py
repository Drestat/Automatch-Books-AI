from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User

def mock_get_current_user():
    return User(id="user_test", email="test@example.com")

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

def test_stats():
    print("🚀 Calling /api/v1/gamification/stats ...")
    response = client.get("/api/v1/gamification/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 422:
        print("❌ Validation Error Details:")
        print(response.json())

if __name__ == "__main__":
    test_stats()
