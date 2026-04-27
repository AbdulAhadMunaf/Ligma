from rest_framework.reverse import reverse


def test_login_with_correct_cred_superuser(user, secret_pwd, api_client):
    # Make user a superuser
    user.is_superuser = True
    user.is_active = True
    user.save()

    data = {
        "email": user.email,
        "password": secret_pwd,
    }
    url = reverse("login_api")
    response = api_client.post(url, data)
    assert response.status_code == 200

    json_resp = response.json()
    assert json_resp["data"]["user"]["id"] == user.id
    assert json_resp["data"]["user"]["name"] == user.name
    assert json_resp["data"]["user"]["email"] == user.email


def test_login_with_correct_cred_regular_user(user, secret_pwd, api_client):
    user.is_active = True
    user.save()

    data = {
        "email": user.email,
        "password": secret_pwd,
    }
    url = reverse("login_api")
    response = api_client.post(url, data)
    assert response.status_code == 200

    json_resp = response.json()
    assert json_resp["data"]["user"]["id"] == user.id
    assert json_resp["data"]["user"]["name"] == user.name
    assert json_resp["data"]["user"]["email"] == user.email


def test_login_with_inactive_user(user, secret_pwd, api_client):
    user.is_active = False
    user.save()

    data = {
        "email": user.email,
        "password": secret_pwd,
    }
    url = reverse("login_api")
    response = api_client.post(url, data)
    assert response.status_code == 401


def test_login_with_incorrect_cred(user, api_client):
    data = {
        "email": user.email,
        "password": "invalid_cred",
    }
    url = reverse("login_api")
    response = api_client.post(url, data)
    assert response.status_code == 401


def test_login_with_validation_error(user, secret_pwd, api_client):
    data = {
        "email": "invalid-email",
        "password": secret_pwd,
    }
    url = reverse("login_api")
    response = api_client.post(url, data)
    assert response.status_code == 400
