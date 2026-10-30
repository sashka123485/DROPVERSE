import os
os.environ.setdefault("DATABASE_URL","sqlite:///./test_dropverse.sqlite3")
os.environ.setdefault("ENVIRONMENT","development")
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health():
    r=client.get('/api/health'); assert r.status_code==200 and r.json()['status']=='ok'
def test_demo_profile():
    r=client.get('/api/dev/profile'); assert r.status_code==200 and 'coins' in r.json()
def test_containers():
    r=client.get('/api/dev/containers'); assert r.status_code==200 and len(r.json())>=3
def test_protected_profile(): assert client.get('/api/profile').status_code==401
