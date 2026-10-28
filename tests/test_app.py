from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Art Club"
    assert email in client.get("/activities").json()["Art Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Atividade não encontrada"


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Estudante já está inscrito nesta atividade"


def test_signup_rejects_full_activity(client):
    activity = app_module.activities["Art Club"]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    response = client.post(
        "/activities/Art Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Atividade cheia"


def test_delete_signup_removes_all_matching_participants(client):
    email = "student@mergington.edu"
    app_module.activities["Art Club"]["participants"] = [email, email, "other@mergington.edu"]

    response = client.delete("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Art Club"
    assert app_module.activities["Art Club"]["participants"] == ["other@mergington.edu"]


def test_delete_signup_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Atividade não encontrada"


def test_delete_signup_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Art Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Estudante não está inscrito nesta atividade"
