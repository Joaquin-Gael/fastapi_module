# FastAPI

FastAPI is a modern, high-performance web framework for building APIs with Python based on standard Python type hints. It leverages Starlette for web handling and Pydantic for data validation, achieving performance on par with NodeJS and Go while providing automatic interactive API documentation via Swagger UI and ReDoc. The framework uses Python type annotations to provide editor support, automatic data validation, serialization, and OpenAPI schema generation.

FastAPI dramatically reduces development time through its intuitive design that eliminates boilerplate code. With features like automatic request validation, dependency injection, OAuth2/JWT security, WebSocket support, and background tasks, developers can build production-ready APIs with minimal code while maintaining type safety and comprehensive documentation.

## Creating a Basic FastAPI Application

Create a FastAPI app instance and define path operations using decorators. The framework automatically handles request parsing, validation, and JSON response serialization.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

```bash
# Run the development server
fastapi dev main.py

# Test the endpoints
curl http://127.0.0.1:8000/
# {"message":"Hello World"}

curl http://127.0.0.1:8000/items/5?q=test
# {"item_id":5,"q":"test"}

# Access interactive docs at http://127.0.0.1:8000/docs
```

## Path Parameters

Declare path parameters using Python format string syntax. Type annotations enable automatic validation and conversion.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}
```

```bash
curl http://127.0.0.1:8000/items/42
# {"item_id":42}

curl http://127.0.0.1:8000/items/foo
# {"detail":[{"type":"int_parsing","loc":["path","item_id"],"msg":"Input should be a valid integer"}]}
```

## Query Parameters

Function parameters not declared in the path are automatically interpreted as query parameters with optional default values.

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

@app.get("/search/")
async def search_items(q: str, category: str | None = None):
    results = {"query": q}
    if category:
        results["category"] = category
    return results
```

```bash
curl "http://127.0.0.1:8000/items/?skip=1&limit=2"
# [{"item_name":"Bar"},{"item_name":"Baz"}]

curl "http://127.0.0.1:8000/search/?q=laptop&category=electronics"
# {"query":"laptop","category":"electronics"}
```

## Request Body with Pydantic Models

Declare request bodies using Pydantic models for automatic validation, serialization, and JSON Schema generation.

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        item_dict["price_with_tax"] = item.price + item.tax
    return item_dict

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result["q"] = q
    return result
```

```bash
curl -X POST "http://127.0.0.1:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "tax": 50.0}'
# {"name":"Laptop","description":null,"price":999.99,"tax":50.0,"price_with_tax":1049.99}

curl -X PUT "http://127.0.0.1:8000/items/1?q=update" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Laptop", "price": 899.99}'
# {"item_id":1,"name":"Updated Laptop","description":null,"price":899.99,"tax":null,"q":"update"}
```

## Response Model and Data Filtering

Use response models to filter output data, ensuring sensitive fields like passwords are never exposed in API responses.

```python
from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn) -> Any:
    # Password is automatically filtered from response
    return user
```

```bash
curl -X POST "http://127.0.0.1:8000/user/" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123", "email": "john@example.com"}'
# {"username":"john","email":"john@example.com","full_name":null}
# Note: password is NOT in the response
```

## Error Handling with HTTPException

Raise HTTPException to return HTTP error responses with custom status codes and details.

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}

@app.delete("/items/{item_id}")
async def delete_item(item_id: str, token: str):
    if token != "valid-token":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    del items[item_id]
    return {"message": "Item deleted"}
```

```bash
curl http://127.0.0.1:8000/items/foo
# {"item":"The Foo Wrestlers"}

curl http://127.0.0.1:8000/items/bar
# {"detail":"Item not found"}
# HTTP 404 status code
```

## Dependency Injection

Use the Depends function to declare reusable dependencies that can be shared across multiple path operations.

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

CommonParams = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonParams):
    return {"message": "Items endpoint", **commons}

@app.get("/users/")
async def read_users(commons: CommonParams):
    return {"message": "Users endpoint", **commons}
```

```bash
curl "http://127.0.0.1:8000/items/?q=search&skip=10&limit=50"
# {"message":"Items endpoint","q":"search","skip":10,"limit":50}

curl "http://127.0.0.1:8000/users/?limit=20"
# {"message":"Users endpoint","q":null,"skip":0,"limit":20}
```

## OAuth2 Security with Bearer Token

Implement OAuth2 password flow authentication using FastAPI's security utilities.

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    "johndoe": {"username": "johndoe", "hashed_password": "fakehashedsecret"}
}

class User(BaseModel):
    username: str

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != "fake-valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(username="johndoe")

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_users_db.get(form_data.username)
    if not user or form_data.password != "secret":
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    return {"access_token": "fake-valid-token", "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

```bash
# Get access token
curl -X POST "http://127.0.0.1:8000/token" \
  -d "username=johndoe&password=secret"
# {"access_token":"fake-valid-token","token_type":"bearer"}

# Access protected endpoint
curl "http://127.0.0.1:8000/users/me" \
  -H "Authorization: Bearer fake-valid-token"
# {"username":"johndoe"}
```

## Middleware

Add middleware to process requests before they reach path operations and responses before they're returned.

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

```bash
curl -i http://127.0.0.1:8000/
# HTTP/1.1 200 OK
# x-process-time: 0.000234
# {"message":"Hello World"}
```

## CORS Configuration

Enable Cross-Origin Resource Sharing for frontend applications on different domains.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://myapp.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    return {"message": "Hello World"}
```

## Background Tasks

Execute tasks in the background after returning a response, useful for email notifications or data processing.

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_notification(email: str, message: str = ""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

def send_email(email: str, subject: str, body: str):
    # Simulate sending email
    print(f"Sending email to {email}: {subject}")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    background_tasks.add_task(send_email, email, "Welcome", "Thanks for signing up!")
    return {"message": "Notification sent in the background"}
```

```bash
curl -X POST "http://127.0.0.1:8000/send-notification/user@example.com"
# {"message":"Notification sent in the background"}
# Background tasks execute after response is returned
```

## File Uploads

Handle file uploads using UploadFile for large files or bytes for small files.

```python
from typing import Annotated
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }

@app.post("/multiple-files/")
async def create_multiple_files(files: list[UploadFile]):
    return {"filenames": [f.filename for f in files]}
```

```bash
curl -X POST "http://127.0.0.1:8000/uploadfile/" \
  -F "file=@myfile.txt"
# {"filename":"myfile.txt","content_type":"text/plain","size":1234}

curl -X POST "http://127.0.0.1:8000/multiple-files/" \
  -F "files=@file1.txt" \
  -F "files=@file2.txt"
# {"filenames":["file1.txt","file2.txt"]}
```

## WebSocket Support

Create real-time bidirectional communication with WebSocket endpoints.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left")
```

```javascript
// JavaScript client example
const ws = new WebSocket("ws://localhost:8000/ws/1");
ws.onmessage = (event) => console.log(event.data);
ws.send("Hello from client!");
```

## Lifespan Events

Execute startup and shutdown code using the lifespan context manager for resource initialization and cleanup.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

def load_ml_model():
    return lambda x: x * 42

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load resources
    ml_models["answer_to_everything"] = load_ml_model()
    print("ML model loaded")
    yield
    # Shutdown: Clean up resources
    ml_models.clear()
    print("ML model unloaded")

app = FastAPI(lifespan=lifespan)

@app.get("/predict")
async def predict(x: float):
    result = ml_models["answer_to_everything"](x)
    return {"result": result}
```

```bash
# On startup, model is loaded
# Server: "ML model loaded"

curl "http://127.0.0.1:8000/predict?x=2.0"
# {"result":84.0}

# On shutdown (Ctrl+C), cleanup runs
# Server: "ML model unloaded"
```

## Testing FastAPI Applications

Use TestClient from Starlette for synchronous testing or httpx for async tests.

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

# Test file (test_main.py)
client = TestClient(app)

def test_read_item():
    response = client.get("/items/42?q=test")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "test"}

def test_read_item_not_found():
    response = client.get("/items/foo")
    assert response.status_code == 422  # Validation error
```

```bash
# Run tests with pytest
pytest test_main.py -v
```

## Summary

FastAPI is ideal for building production-ready REST APIs, microservices, and real-time applications that require high performance and automatic documentation. Its integration with Pydantic provides robust data validation while type hints enable excellent IDE support and code maintainability. Common use cases include backend APIs for web and mobile applications, machine learning model serving, IoT data collection endpoints, and real-time WebSocket applications.

The framework's dependency injection system allows for clean separation of concerns, making it easy to implement authentication, database connections, and business logic that can be shared across endpoints. FastAPI applications can be deployed with Uvicorn or Gunicorn with Uvicorn workers for production, and the framework integrates seamlessly with async database libraries, message queues, and cloud services. For deployment, use `fastapi run` for production or deploy to platforms like FastAPI Cloud, Docker containers, or any ASGI-compatible hosting service.
