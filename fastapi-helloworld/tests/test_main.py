# test_main.py
import pytest
from httpx import AsyncClient
from sqlmodel import Session, SQLModel, create_engine
from main import app, get_session, Todo

# Create an in-memory SQLite database for testing
test_engine = create_engine("sqlite:///test.db")

# Override the get_session dependency to use the test database
def override_get_session():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="module", autouse=True)
def create_test_database():
    # Create the database and tables
    SQLModel.metadata.create_all(test_engine)
    yield
    # Drop the database and tables
    SQLModel.metadata.drop_all(test_engine)

@pytest.mark.asyncio
async def test_read_root(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

@pytest.mark.asyncio
async def test_create_todo(async_client):
    response = await async_client.post("/todos/", json={"content": "Test Todo"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test Todo"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_todos(async_client):
    # First, create a todo
    await async_client.post("/todos/", json={"content": "Test Todo 1"})
    await async_client.post("/todos/", json={"content": "Test Todo 2"})
    
    response = await async_client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["content"] == "Test Todo 1"
    assert data[1]["content"] == "Test Todo 2"

@pytest.mark.asyncio
async def test_read_todo_by_id(async_client):
    # First, create a todo
    response = await async_client.post("/todos/", json={"content": "Test Todo"})
    todo_id = response.json()["id"]
    
    response = await async_client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["content"] == "Test Todo"

@pytest.mark.asyncio
async def test_delete_todo_by_id(async_client):
    # First, create a todo
    response = await async_client.post("/todos/", json={"content": "Test Todo"})
    todo_id = response.json()["id"]
    
    response = await async_client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json() == {"Succesfully deleted todo": todo_id}
    
    # Verify the todo is deleted
    response = await async_client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json() is None
