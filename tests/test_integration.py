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

    def test_custom_disease_missing_fields(client):
        # Missing sensitivity
        data = {'pD': 0.05, 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400
        # Missing pD
        data = {'sensitivity': 0.9, 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400
        # Missing falsePositive
        data = {'pD': 0.05, 'sensitivity': 0.9}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400

    def test_custom_disease_invalid_types(client):
        # String values
        data = {'pD': "0.05", 'sensitivity': 0.9, 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400
        data = {'pD': 0.05, 'sensitivity': "0.9", 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400
        data = {'pD': 0.05, 'sensitivity': 0.9, 'falsePositive': "0.1"}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400

    def test_custom_disease_out_of_bounds(client):
        # Negative values
        data = {'pD': -0.1, 'sensitivity': 0.9, 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400
        # Values > 1
        data = {'pD': 1.1, 'sensitivity': 0.9, 'falsePositive': 0.1}
        rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 400

    def test_preset_missing_disease_field(client):
        data = {}
        rv = client.post('/preset', data=json.dumps(data), content_type='application/json')
        assert rv.status_code == 404 or rv.status_code == 400

    def test_invalid_content_type(client):
        # Send form data instead of JSON
        data = {'pD': 0.05, 'sensitivity': 0.9, 'falsePositive': 0.1}
        rv = client.post('/disease', data=data)
        assert rv.status_code in (400, 415)

        def test_custom_disease_random_values(client):
            data = {'pD': 0.25, 'sensitivity': 0.5, 'falsePositive': 0.75}
            rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
            assert rv.status_code == 200
            response = json.loads(rv.data)
            assert 'p_d_given_pos' in response
            assert round(response['p_d_given_pos'], 4) == 0.3636

            data = {'pD': 0.33, 'sensitivity': 0.67, 'falsePositive': 0.89}
            rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
            assert rv.status_code == 200
            response = json.loads(rv.data)
            assert 'p_d_given_pos' in response
            assert round(response['p_d_given_pos'], 4) == 0.6872

            data = {'pD': 0.1234, 'sensitivity': 0.5678, 'falsePositive': 0.9101}
            rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
            assert rv.status_code == 200
            response = json.loads(rv.data)
            assert 'p_d_given_pos' in response
            assert round(response['p_d_given_pos'], 4) == 0.4412

            def test_custom_disease_typical_cases(client):
                data = {'pD': 0.01, 'sensitivity': 0.99, 'falsePositive': 0.95}
                rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                assert rv.status_code == 200
                response = json.loads(rv.data)
                assert 'p_d_given_pos' in response
                assert round(response['p_d_given_pos'], 4) == 0.1664

                data = {'pD': 0.10, 'sensitivity': 0.90, 'falsePositive': 0.90}
                rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                assert rv.status_code == 200
                response = json.loads(rv.data)
                assert 'p_d_given_pos' in response
                assert round(response['p_d_given_pos'], 4) == 0.5

                data = {'pD': 0.20, 'sensitivity': 0.85, 'falsePositive': 0.80}
                rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                assert rv.status_code == 200
                response = json.loads(rv.data)
                assert 'p_d_given_pos' in response
                assert round(response['p_d_given_pos'], 4) == 0.5313

            def test_custom_disease_high_specificity(client):
                data = {'pD': 0.15, 'sensitivity': 0.75, 'falsePositive': 0.99}
                rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                assert rv.status_code == 200
                response = json.loads(rv.data)
                assert 'p_d_given_pos' in response
                assert round(response['p_d_given_pos'], 4) == 0.9195

            def test_custom_disease_high_sensitivity(client):
                data = {'pD': 0.15, 'sensitivity': 0.99, 'falsePositive': 0.75}
                rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                assert rv.status_code == 200
                response = json.loads(rv.data)
                assert 'p_d_given_pos' in response
                assert round(response['p_d_given_pos'], 4) == 0.3951

                def test_custom_disease_mid_range(client):
                    data = {'pD': 0.5, 'sensitivity': 0.5, 'falsePositive': 0.5}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.5

                    data = {'pD': 0.3, 'sensitivity': 0.7, 'falsePositive': 0.6}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.5385

                def test_custom_disease_low_probabilities(client):
                    data = {'pD': 0.01, 'sensitivity': 0.01, 'falsePositive': 0.01}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.0099

                    data = {'pD': 0.05, 'sensitivity': 0.05, 'falsePositive': 0.05}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.0526

                def test_custom_disease_high_probabilities(client):
                    data = {'pD': 0.99, 'sensitivity': 0.99, 'falsePositive': 0.99}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.99

                    data = {'pD': 0.95, 'sensitivity': 0.95, 'falsePositive': 0.95}
                    rv = client.post('/disease', data=json.dumps(data), content_type='application/json')
                    assert rv.status_code == 200
                    response = json.loads(rv.data)
                    assert 'p_d_given_pos' in response
                    assert round(response['p_d_given_pos'], 4) == 0.95