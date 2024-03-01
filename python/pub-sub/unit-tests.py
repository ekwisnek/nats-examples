import pytest
import json
from unittest.mock import patch, AsyncMock
from poster import app  # Adjust this import to your application's structure

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_valid_post_request(client):
    data = {"name": "John Doe", "age": 30, "email": "john.doe@example.com"}
    with patch('poster.nats.connect', AsyncMock()) as mock_connect:
        mock_nc = AsyncMock()
        mock_connect.return_value = mock_nc
        
        response = client.post('/v1/api', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 200
        assert response.json == {"message": "Data received and published successfully"}
        mock_nc.publish.assert_awaited_once()  # Use assert_awaited_once for async methods

def test_invalid_post_request(client):
    data = {"name": "John Doe", "age": "not an integer", "email": "john.doe@example.com"}
    response = client.post('/v1/api', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert "error" in response.json

def test_nats_timeout_error(client):
    data = {"name": "John Doe", "age": 30, "email": "john.doe@example.com"}
    with patch('poster.nats.connect', AsyncMock()) as mock_connect:
        mock_nc = AsyncMock()
        mock_nc.publish.side_effect = TimeoutError("NATS Timeout")
        mock_connect.return_value = mock_nc
        
        response = client.post('/v1/api', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 500
        assert "error" in response.json
        assert response.json['error'] == 'NATS Timeout'

