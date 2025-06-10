# Notipy Backend

This directory contains the FastAPI server that powers Notipy.

## HTTP 204 Responses
Some endpoints return `204 No Content` when the request succeeds but the database has no information to provide. The call was processed correctly; there is simply nothing to return.

## 🚀 Adding New Features

When adding new features to the backend, follow the modular structure based on **routers** and **services**.

### 🧩 Step-by-Step Guide

1. **Create a new router**  
   - Add a new file under `routers/`, e.g., `example.py`.
   - Define a FastAPI router object:
     ```python
     from fastapi import APIRouter
     router = APIRouter()

     @router.get("/example")
     async def example_endpoint():
         return {"message": "This is an example route"}
     ```
   - **You Don't need to change the `main.py`file. All routers are included dynamically.**

2. **Create a corresponding service module**
   - Add a new file under `services/`, e.g., `exampleservice.py`.
   - Move your logic (e.g., database access, processing, etc.) into this service file to keep routers clean.
     ```python
     async def get_example_data():
         return {"example": "data"}
     ```

3. **Use dependency injection if needed**
   - You can inject dependencies or DB sessions into service functions or routers as appropriate.

4. **Keep naming consistent**
   - If you name your router `routers/feedback.py`, name your service `services/feedbackservice.py`.

5. **Test endpoints locally**
   - Run the server (`main.py`) and test the new endpoint using Swagger UI (`http://localhost:8000/docs`).

---

### ✅ Tips

- Keep your `routers/` focused on **API definition** and input validation.
- Keep your `services/` focused on **business logic and processing**.
- If the service layer becomes complex, you may split it further or introduce helper modules.

---

This structure makes the backend easier to maintain, extend, and test.


For full setup and usage details, see the [root README](../README.md).
