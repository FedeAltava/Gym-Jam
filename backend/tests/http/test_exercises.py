import pytest

from backend.src.infrastructure.persistence.exercise_seed import EXERCISE_SEED


# 1. GET /exercises — returns the seeded catalog
async def test_list_exercises_returns_seeded_catalog(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == len(EXERCISE_SEED)
    by_id = {item["id"]: item for item in data}
    assert by_id["bench-press"]["name"] == "Press de banca"
    assert by_id["bench-press"]["muscle_group"] == "Pecho"
    assert by_id["squat"]["muscle_group"] == "Piernas"


# 2. GET /exercises — response items match ExerciseResponse schema
async def test_list_exercises_items_have_expected_fields(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    first = r.json()[0]
    assert set(first.keys()) == {"id", "name", "muscle_group", "is_bodyweight", "is_custom"}


# 2b. GET /exercises — seeded exercises are not custom
async def test_list_exercises_seeded_exercises_not_custom(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    for item in r.json():
        assert item["is_custom"] is False


# 2c. GET /exercises — bodyweight exercises are flagged in the catalog
async def test_list_exercises_marks_bodyweight_exercises(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    by_id = {item["id"]: item for item in r.json()}
    for slug in ("push-up", "pull-up", "plank", "crunch"):
        assert by_id[slug]["is_bodyweight"] is True, slug
    assert by_id["bench-press"]["is_bodyweight"] is False
    assert by_id["squat"]["is_bodyweight"] is False


# 3. GET /exercises — ordered by muscle_group then name
async def test_list_exercises_ordered_by_muscle_group_then_name(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    keys = [(item["muscle_group"], item["name"]) for item in r.json()]
    assert keys == sorted(keys)


# 4. GET /exercises — requires auth
async def test_list_exercises_without_token_returns_401(auth_client):
    r = await auth_client.get("/exercises")
    assert r.status_code == 401


# 5. POST exercises — unknown exercise id returns 404
async def test_add_exercise_unknown_id_returns_404(client):
    r = await client.post("/workouts", json={"name": "Catalog Check", "training_days": ["MONDAY"]})
    assert r.status_code == 201
    wid = r.json()["id"]
    r = await client.post(
        f"/workouts/{wid}/training-days/MONDAY/exercises",
        json={"exercise_id": "not-a-real-exercise"},
    )
    assert r.status_code == 404


# 6. POST exercises — catalog slug still works (happy path guard)
async def test_add_exercise_known_id_returns_201(client):
    r = await client.post("/workouts", json={"name": "Catalog Happy", "training_days": ["TUESDAY"]})
    wid = r.json()["id"]
    r = await client.post(
        f"/workouts/{wid}/training-days/TUESDAY/exercises",
        json={"exercise_id": "lat-pulldown"},
    )
    assert r.status_code == 201
    assert r.json()["exercise_id"] == "lat-pulldown"


# --- Filter by muscle_group query param ---


async def test_list_exercises_no_filter_returns_all(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    assert len(r.json()) == len(EXERCISE_SEED)


async def test_list_exercises_filter_by_muscle_group(client):
    r = await client.get("/exercises?muscle_group=Pecho")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert all(item["muscle_group"] == "Pecho" for item in data)


async def test_list_exercises_filter_nonexistent_group_returns_empty(client):
    r = await client.get("/exercises?muscle_group=NonExistent")
    assert r.status_code == 200
    assert r.json() == []


# --- Custom exercise CRUD ---


async def test_create_exercise_returns_201_with_is_custom_true(client):
    r = await client.post("/exercises", json={"name": "Mi ejercicio", "muscle_group": "Pecho"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Mi ejercicio"
    assert data["muscle_group"] == "Pecho"
    assert data["is_bodyweight"] is False
    assert data["is_custom"] is True


async def test_create_exercise_bodyweight_flag(client):
    r = await client.post(
        "/exercises",
        json={"name": "Dragon Flag", "muscle_group": "Core", "is_bodyweight": True},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["is_bodyweight"] is True
    assert data["is_custom"] is True


async def test_create_exercise_appears_in_list(client):
    r = await client.post("/exercises", json={"name": "Custom Pull", "muscle_group": "Espalda"})
    assert r.status_code == 201
    created_id = r.json()["id"]

    r = await client.get("/exercises")
    ids = [item["id"] for item in r.json()]
    assert created_id in ids


async def test_create_exercise_not_visible_to_other_user(client, client_user2):
    r = await client.post("/exercises", json={"name": "My Private Exercise", "muscle_group": "Pecho"})
    assert r.status_code == 201
    created_id = r.json()["id"]

    r2 = await client_user2.get("/exercises")
    ids = [item["id"] for item in r2.json()]
    assert created_id not in ids


async def test_delete_custom_exercise_returns_204(client):
    r = await client.post("/exercises", json={"name": "Temp Exercise", "muscle_group": "Pecho"})
    assert r.status_code == 201
    eid = r.json()["id"]

    r = await client.delete(f"/exercises/{eid}")
    assert r.status_code == 204

    r = await client.get("/exercises")
    ids = [item["id"] for item in r.json()]
    assert eid not in ids


async def test_delete_exercise_not_found_returns_404(client):
    r = await client.delete("/exercises/nonexistent-id")
    assert r.status_code == 404


async def test_delete_global_exercise_returns_403(client):
    r = await client.delete("/exercises/bench-press")
    assert r.status_code == 403


async def test_delete_exercise_owned_by_other_user_returns_403(client, client_user2):
    r = await client.post("/exercises", json={"name": "User1 Exercise", "muscle_group": "Pecho"})
    assert r.status_code == 201
    eid = r.json()["id"]

    r2 = await client_user2.delete(f"/exercises/{eid}")
    assert r2.status_code == 403


async def test_delete_exercise_in_use_returns_409(client):
    r = await client.post("/exercises", json={"name": "In Use Exercise", "muscle_group": "Espalda"})
    assert r.status_code == 201
    eid = r.json()["id"]

    r = await client.post("/workouts", json={"name": "Test W", "training_days": ["FRIDAY"]})
    wid = r.json()["id"]
    r = await client.post(
        f"/workouts/{wid}/training-days/FRIDAY/exercises",
        json={"exercise_id": eid},
    )
    assert r.status_code == 201

    r = await client.delete(f"/exercises/{eid}")
    assert r.status_code == 409


async def test_create_exercise_requires_auth(auth_client):
    r = await auth_client.post("/exercises", json={"name": "No auth", "muscle_group": "Pecho"})
    assert r.status_code == 401
