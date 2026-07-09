
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
    assert by_id["leg-press"]["muscle_group"] == "Piernas"


# 2. GET /exercises — response items match ExerciseResponse schema
async def test_list_exercises_items_have_expected_fields(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    first = r.json()[0]
    assert set(first.keys()) == {"id", "name", "muscle_group", "is_bodyweight"}


# 2b. GET /exercises — bodyweight exercises are flagged in the catalog
async def test_list_exercises_marks_bodyweight_exercises(client):
    r = await client.get("/exercises")
    assert r.status_code == 200
    by_id = {item["id"]: item for item in r.json()}
    assert by_id["bench-press"]["is_bodyweight"] is False
    assert by_id["leg-press"]["is_bodyweight"] is False
    assert by_id["deadlift"]["is_bodyweight"] is False


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
