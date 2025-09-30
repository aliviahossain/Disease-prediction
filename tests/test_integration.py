import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test if home page loads correctly"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Probability Calculator' in rv.data

def test_preset_disease_calculation(client):
    """Test preset disease endpoint with valid data"""
    data = {'disease': 'Influenza'}
    rv = client.post('/preset', 
                     data=json.dumps(data),
                     content_type='application/json')
    assert rv.status_code == 200
    response = json.loads(rv.data)
    assert 'p_d_given_pos' in response
    assert isinstance(response['p_d_given_pos'], float)

def test_preset_invalid_disease(client):
    """Test preset disease endpoint with invalid disease"""
    data = {'disease': 'NonExistentDisease'}
    rv = client.post('/preset', 
                     data=json.dumps(data),
                     content_type='application/json')
    assert rv.status_code == 404

def test_custom_disease_calculation(client):
    """Test custom disease calculation endpoint"""
    data = {
        'pD': 0.05,
        'sensitivity': 0.9,
        'falsePositive': 0.1
    }
    rv = client.post('/disease',
                     data=json.dumps(data),
                     content_type='application/json')
    assert rv.status_code == 200
    response = json.loads(rv.data)
    assert 'p_d_given_pos' in response
    assert isinstance(response['p_d_given_pos'], float)