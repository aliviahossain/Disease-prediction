import pytest


def test_logout_post_succeeds(client):
    # login first
    client.post(
        "/login",
        data={
            "email": "profile@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    # logout via POST
    response = client.post(
        "/logout",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"logged out" in response.data.lower()