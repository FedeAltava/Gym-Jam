import pytest


# Helper
async def create_workout(client, name="Push Day", training_days=None):
    payload = {"name": name, "description": None, "training_days": training_days or []}
    r = await client.post("/workouts", json=payload)
    assert r.status_code == 201
    return r.json()


# 1. POST /workouts — happy path
async def test_create_workout_returns_201(client):
    r = await client.post("/workouts", json={"name": "Push Day", "training_days": []})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Push Day"
    assert data["is_active"] is True
    assert data["training_days"] == []


# 2. POST /workouts — with training days
async def test_create_workout_with_training_days(client):
    r = await client.post("/workouts", json={"name": "Full Body", "training_days": ["MONDAY", "WEDNESDAY"]})
    assert r.status_code == 201
    data = r.json()
    assert len(data["training_days"]) == 2


# 3. POST /workouts — invalid name
async def test_create_workout_empty_name_returns_422(client):
    r = await client.post("/workouts", json={"name": "", "training_days": []})
    assert r.status_code == 422


# 4. POST /workouts — invalid day
async def test_create_workout_invalid_day_returns_422(client):
    r = await client.post("/workouts", json={"name": "Test", "training_days": ["FUNDAY"]})
    assert r.status_code == 422


# 5. GET /workouts/{id} — happy path
async def test_get_workout_returns_200(client):
    created = await create_workout(client, "Leg Day")
    r = await client.get(f"/workouts/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Leg Day"


# 6. GET /workouts/{id} — not found
async def test_get_workout_not_found_returns_404(client):
    r = await client.get("/workouts/00000000-0000-0000-0000-000000000999")
    assert r.status_code == 404


# 7. POST /workouts/{id}/training-days — happy path
async def test_add_training_day_returns_201(client):
    created = await create_workout(client, "Upper")
    r = await client.post(f"/workouts/{created['id']}/training-days", json={"day_of_week": "TUESDAY"})
    assert r.status_code == 201
    assert r.json()["day_of_week"] == "TUESDAY"


# 8. POST /workouts/{id}/training-days — lowercase normalized
async def test_add_training_day_lowercase_normalized(client):
    created = await create_workout(client, "Lower")
    r = await client.post(f"/workouts/{created['id']}/training-days", json={"day_of_week": "friday"})
    assert r.status_code == 201
    assert r.json()["day_of_week"] == "FRIDAY"


# 9. POST /workouts/{id}/training-days — workout not found
async def test_add_training_day_not_found_returns_404(client):
    r = await client.post("/workouts/00000000-0000-0000-0000-000000000999/training-days", json={"day_of_week": "MONDAY"})
    assert r.status_code == 404


# 10. DELETE /workouts/{id}/training-days/{day} — happy path
async def test_remove_training_day_returns_204(client):
    created = await create_workout(client, "Day Remove Test")
    wid = created["id"]
    await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "WEDNESDAY"})
    r = await client.delete(f"/workouts/{wid}/training-days/WEDNESDAY")
    assert r.status_code == 204


# 11. DELETE /workouts/{id}/training-days/{day} — not found
async def test_remove_training_day_not_found_returns_404(client):
    r = await client.delete("/workouts/00000000-0000-0000-0000-000000000999/training-days/MONDAY")
    assert r.status_code == 404


# 12. POST exercises — happy path
async def test_add_exercise_returns_201(client):
    created = await create_workout(client, "Exercise Add Test")
    wid = created["id"]
    await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "THURSDAY"})
    r = await client.post(f"/workouts/{wid}/training-days/THURSDAY/exercises", json={"exercise_id": "bench-press"})
    assert r.status_code == 201
    assert r.json()["exercise_id"] == "bench-press"
    assert r.json()["order"] == 1


# 13. POST exercises — workout not found
async def test_add_exercise_workout_not_found_returns_404(client):
    r = await client.post("/workouts/00000000-0000-0000-0000-000000000999/training-days/MONDAY/exercises", json={"exercise_id": "squat"})
    assert r.status_code == 404


# 14. DELETE exercise — happy path
async def test_remove_exercise_returns_204(client):
    created = await create_workout(client, "Exercise Remove Test")
    wid = created["id"]
    await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "SATURDAY"})
    add_r = await client.post(f"/workouts/{wid}/training-days/SATURDAY/exercises", json={"exercise_id": "deadlift"})
    ex_id = add_r.json()["id"]
    r = await client.delete(f"/workouts/{wid}/training-days/SATURDAY/exercises/{ex_id}")
    assert r.status_code == 204


# 15. DELETE exercise — not found
async def test_remove_exercise_not_found_returns_404(client):
    r = await client.delete("/workouts/00000000-0000-0000-0000-000000000999/training-days/MONDAY/exercises/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404


# 16. PUT reorder — happy path
async def test_reorder_exercises_returns_200(client):
    created = await create_workout(client, "Reorder Test")
    wid = created["id"]
    await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "SUNDAY"})
    r1 = await client.post(f"/workouts/{wid}/training-days/SUNDAY/exercises", json={"exercise_id": "ex-a"})
    r2 = await client.post(f"/workouts/{wid}/training-days/SUNDAY/exercises", json={"exercise_id": "ex-b"})
    id1 = r1.json()["id"]
    id2 = r2.json()["id"]
    r = await client.put(f"/workouts/{wid}/training-days/SUNDAY/exercises/reorder", json={"ordered_exercise_ids": [id2, id1]})
    assert r.status_code == 200
    exercises = r.json()["exercises"]
    assert exercises[0]["exercise_id"] == "ex-b"
    assert exercises[1]["exercise_id"] == "ex-a"


# 17. PUT reorder — workout not found
async def test_reorder_exercises_not_found_returns_404(client):
    r = await client.put("/workouts/00000000-0000-0000-0000-000000000999/training-days/MONDAY/exercises/reorder", json={"ordered_exercise_ids": []})
    assert r.status_code == 404


# 18. POST /workouts — description round-trips
async def test_create_workout_description_round_trips(client):
    r = await client.post("/workouts", json={"name": "Desc Test", "description": "My description", "training_days": []})
    assert r.status_code == 201
    assert r.json()["description"] == "My description"


# 19. POST /workouts — None description
async def test_create_workout_none_description(client):
    r = await client.post("/workouts", json={"name": "No Desc", "training_days": []})
    assert r.status_code == 201
    assert r.json()["description"] is None


# 20. GET workout includes training days with exercises
async def test_get_workout_includes_structure(client):
    created = await create_workout(client, "Structure Test")
    wid = created["id"]
    await client.post(f"/workouts/{wid}/training-days", json={"day_of_week": "MONDAY"})
    await client.post(f"/workouts/{wid}/training-days/MONDAY/exercises", json={"exercise_id": "squat"})
    r = await client.get(f"/workouts/{wid}")
    assert r.status_code == 200
    days = r.json()["training_days"]
    assert len(days) == 1
    assert days[0]["exercises"][0]["exercise_id"] == "squat"


# 21. GET /workouts — returns list
async def test_list_workouts_returns_200(client):
    await create_workout(client, "List Test Workout")
    r = await client.get("/workouts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


# 22. GET /workouts — response items match WorkoutResponse schema
async def test_list_workouts_items_have_expected_fields(client):
    await create_workout(client, "Schema Check Workout")
    r = await client.get("/workouts")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    first = items[0]
    assert "id" in first
    assert "name" in first
    assert "is_active" in first
    assert "training_days" in first


# 23. Error detail is a string
async def test_error_detail_is_string(client):
    r = await client.get("/workouts/00000000-0000-0000-0000-000000000999")
    assert r.status_code == 404
    assert "detail" in r.json()
    assert isinstance(r.json()["detail"], str)
