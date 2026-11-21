import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data(monkeypatch):
    data = {
        "Chess Club": {
            "description": "Chess",
            "schedule": "Friday",
            "max_participants": 4,
            "participants": ["first@example.com"],
        },
        "Art Club": {
            "description": "Art",
            "schedule": "Monday",
            "max_participants": 4,
            "participants": ["first@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", data)
    return data


@pytest.fixture
def client(activity_data):
    with TestClient(app_module.app) as client:
        yield client


def test_signup_adds_only_to_selected_activity(client):
    email = "new+student@example.com"
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    activities = client.get("/activities").json()
    assert activities["Chess Club"]["participants"] == ["first@example.com", email]
    assert activities["Art Club"]["participants"] == ["first@example.com"]


def test_duplicate_signup_is_rejected(client, activity_data):
    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": "first@example.com"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == ["first@example.com"]


def test_unregister_removes_only_from_selected_activity(client):
    email = "first@example.com"
    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    activities = client.get("/activities").json()
    assert activities["Chess Club"]["participants"] == []
    assert activities["Art Club"]["participants"] == [email]


def test_unregister_unknown_participant_is_rejected(client, activity_data):
    response = client.delete(
        "/activities/Chess%20Club/signup", params={"email": "missing@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == ["first@example.com"]


@pytest.mark.parametrize("method", ["post", "delete"])
def test_unknown_activity_is_rejected(client, activity_data, method):
    response = getattr(client, method)(
        "/activities/Missing/signup", params={"email": "first@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data["Chess Club"]["participants"] == ["first@example.com"]
    assert activity_data["Art Club"]["participants"] == ["first@example.com"]


@pytest.mark.parametrize("method", ["post", "delete"])
def test_missing_email_is_rejected(client, activity_data, method):
    response = getattr(client, method)("/activities/Chess%20Club/signup")

    assert response.status_code == 422
    assert activity_data["Chess Club"]["participants"] == ["first@example.com"]
