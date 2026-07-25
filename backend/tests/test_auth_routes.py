import pytest  # noqa


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

    # Verify the request succeeds and redirects to the login page
    assert response.status_code == 200
    assert b"sign in / register" in response.data.lower()


def test_login_rate_limit(client):
    for _ in range(6):
        client.post(
            "/login",
            data={"email": "invalid@test.com", "password": "wrongpassword"},
            follow_redirects=True,
        )

    response = client.post(
        "/login",
        data={"email": "invalid@test.com", "password": "wrongpassword"},
        follow_redirects=True,
    )

    assert b"Too many failed login attempts" in response.data
