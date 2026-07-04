# FastAPI Module

**Template modular y extensible para servidores FastAPI con arquitectura limpia.**

Esto no es "otro boilerplate". Es una base pensada para proyectos reales, con separación de responsabilidades en serio, SPI layer, autenticación JWT con Argon2, CRUD automático, sistema de logging enterprise, caché con Redis, colas con Celery, y un CLI con TUI para gestión de modelos.

---

## Stack

| Capa               | Tecnología                                                                 |
|--------------------|---------------------------------------------------------------------------|
| Framework          | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn                        |
| ORM                | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy async             |
| Base de datos      | PostgreSQL (producción) / SQLite (desarrollo)                             |
| Migraciones        | Alembic                                                                   |
| Autenticación      | JWT + [Argon2](https://argon2-cffi.readthedocs.io/) (password hashing)   |
| Caché              | Redis                                                                     |
| Task queue         | Celery                                                                    |
| Documentación API  | Swagger, Redoc, Scalar                                                    |
| CLI / TUI          | [Rich](https://rich.readthedocs.io/) + [Textual](https://textual.textualize.io/) + Click |
| Testing            | pytest + httpx (TestClient)                                               |
| Contenedores       | Docker + docker-compose                                                   |
| Logging            | RichHandler + RedisHandler + File + Sensitive Data Filter                 |

---

## Arquitectura

El proyecto sigue una variante de **Arquitectura Limpia / Hexagonal** adaptada a FastAPI:

```
┌──────────────────────────────────────────────────────┐
│                    SERVER LAYER                       │
│  (routes, schemas, templates, middlewares, forms)     │
│  ─── Depende de Core ───                             │
├──────────────────────────────────────────────────────┤
│                     CORE LAYER                        │
│  (models, database, auth, cache, tasks, spi, utils)  │
│  ─── No depende de Server ───                        │
├──────────────────────────────────────────────────────┤
│                    MANAGER LAYER                      │
│  (CLI, TUI, code generation)                         │
└──────────────────────────────────────────────────────┘
```

**Regla fundamental**: `core/` NO importa nada de `server/`. La dependencia es unidireccional. Esto fuerza a mantener la lógica de negocio desacoplada de la capa de transporte.

### SPI (Service Provider Interface)

Las operaciones de base de datos viven en `core/spi/`, no en los routes. Esto permite:

- Cambiar la implementación de persistencia sin tocar los endpoints.
- Testear la lógica de negocio sin HTTP.
- Reutilizar la misma lógica desde routes, tasks, o CLI.

```python
# core/spi/base/users.py
class SPIBaseUsers:
    async def get_user_by_email(self, email: str, session: AsyncSession): ...
    async def create_user(self, user: User, session: AsyncSession): ...
    async def update_user(self, user: User, session: AsyncSession): ...
```

---

## Estructura del proyecto

```
fastapi_module/
├── core/                          # Capa core — sin dependencia de server/
│   ├── auth/                      # Autenticación JWT + dependencias FastAPI
│   ├── cache/                     # Cliente Redis
│   ├── config.py                  # Configuración base (pydantic-settings)
│   ├── database/                  # Engine, sesiones, init/close
│   ├── main.py                    # Punto de entrada alternativo (exporta app)
│   ├── migrations/                # Alembic
│   │   ├── versions/
│   │   └── env.py
│   ├── models/                    # Modelos SQLModel
│   │   ├── base/                  # User, Group, Scope, Session, Logs, Admin, etc.
│   │   ├── enums/                 # Enumeraciones
│   │   └── links/                 # Tablas pivot (users_groups, groups_scopes, users_scopes)
│   ├── spi/                       # Service Provider Interface
│   │   └── base/                  # SPI de users, logs
│   ├── tasks/                     # Tareas Celery
│   │   └── base/                  # task_save_logs, main (configuración Celery)
│   └── utils/                     # Logger, async_runner
│
├── server/                        # Capa de presentación / API
│   ├── config.py                  # Configuración del servidor (extiende CoreSettings)
│   ├── forms/                     # Formularios / filtros (Pydantic)
│   │   ├── base/
│   │   └── logs/
│   ├── main.py                    # FastAPI app — lifespan, middlewares, router
│   ├── middlewares/               # Middlewares (user_in_request)
│   ├── routes/                    # Endpoints
│   │   ├── admin.py               # Panel de administración
│   │   ├── auth.py                # /auth (register, login, me)
│   │   ├── docs.py                # /scalar (documentación custom + health)
│   │   ├── main.py                # Router principal (agrega todos los routers)
│   │   └── user.py                # /user (CRUD + perfil propio)
│   ├── schemas/                   # Schemas Pydantic para request/response
│   │   └── base/                  # auth, user, logs
│   └── templates/                 # Templates HTML (Scalar docs, admin panel)
│       └── utils.py
│
├── manager/                       # CLI + TUI
│   ├── manager.py                 # Comandos Click + Textual app
│   ├── templates/                 # Templates Mako para generación de código
│   └── styles/                    # hojas de estilo Textual (.tcss)
│
├── libs/                          # Librerías internas
│   └── fastapi_crudrouter/        # CRUD Router automático (fork interno)
│       └── core/                  # SQLModelAsync, SQLAlchemy, Memory, etc.
│
├── tests/                         # Tests
│   ├── core/
│   │   ├── test_logic.py
│   │   └── test_boundaries.py
│   └── server/
│       └── test_main.py
│
├── .env.example                   # Variables de entorno (template)
├── docker-compose.yaml            # PostgreSQL + Redis + Celery + Server
├── Dockerfile                     # Imagen Alpine Python 3.14
├── pyproject.toml                 # Dependencias y metadatos
├── pytest.ini                     # Configuración de pytest
└── setup.{sh|ps1|cmd}             # Scripts de arranque
```

---

## Features

### Autenticación y autorización
- **Registro y login** con JWT + Argon2 (password hashing con time_cost=16, memory_cost=65536).
- **Scopes y grupos** por usuario (relaciones many-to-many con tablas pivot).
- **Dependencia `get_current_user`** para proteger rutas.
- **Dependencia `get_optional_user`** para endpoints públicos con comportamiento condicional.
- **Validación de passwords** por regex configurable.

### CRUD automático
- Librería interna `fastapi_crudrouter` con soporte para múltiples ORMs: SQLModel async, SQLAlchemy, Tortoise, Ormar, Gino, Databases, y Memory.
- Generación automática de rutas GET, POST, PUT, DELETE desde un schema y un modelo.

### Administración
- **Registro automático de modelos** vía decorador `@register` — los modelos se auto-registran en Redis para que el admin panel los descubra dinámicamente.
- Endpoints de administración: listar/actualizar/eliminar usuarios, consultar logs.
- **Admin panel planificado** como SPA Vue 3 + DaisyUI + Vite (ver `ADMIN_PANEL_PLAN.md`).

### Logging
- **`TZFormatter`**: formato con timezone (`2025-12-27T12:34:56Z | INFO | archivo.py:123 | mensaje`).
- **`SensitiveDataFilter`**: redacta passwords, tokens, API keys automáticamente cuando DEBUG está desactivado.
- **`RedisHandler`**: envía logs a Redis para procesamiento asíncrono con Celery.
- **File handler**: logs persistentes en disco.
- **RichHandler**: logs coloreados en consola.

### Caché
- Cliente Redis asíncrono listo para usar como caché o para cualquier otra necesidad.

### Task queue
- Celery configurado con Redis como broker y backend.
- Tareas incluidas: `save_log` (persistencia asíncrona de logs).

### CLI con TUI
- **`python -m manager.manager`** o invocando `manager()`:
  - `info` — muestra estructura del proyecto en árbol.
  - `create-admin-user` — crea usuario admin interactivamente (con generación de password segura).
  - `create-model` — **TUI interactiva con Textual** para generar modelos SQLModel con campos, tipos, constraints.
  - `run-server` — levanta Docker + Celery + Uvicorn.

### Documentación
- Swagger UI en `/docs`
- Redoc en `/redoc`
- Scalar en `/scalar`
- OpenAPI JSON en `/openapi.json`
- Health check en `/scalar/health`

---

## Quick Start

### 1. Clonar e instalar

```bash
git clone <repo-url> fastapi-module
cd fastapi-module

# Con poetry (recomendado)
poetry install

# O con pip
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

Variables mínimas requeridas:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Clave para firmar JWT | `CHANGE_ME` (CAMBIAR en producción) |
| `DATABASE_URL` | URL de conexión | `sqlite+aiosqlite:///./data/app.db` |
| `ADMIN_INITIAL_EMAIL` | Email del admin inicial | `admin@example.com` |
| `ADMIN_INITIAL_PASSWORD` | Password del admin inicial | `CHANGE_ME` |

### 3. Inicializar base de datos

La base de datos se inicializa automáticamente al arrancar el servidor (lifespan startup ejecuta `SQLModel.metadata.create_all`).

Para migraciones con Alembic:

```bash
alembic upgrade head
```

### 4. Levantar el servidor

```bash
# Directo con Uvicorn
uvicorn server.main:app --reload

# O usando el manager
python -m manager.manager run-server

# O con Docker
docker compose up --build
```

El servidor arranca en `http://localhost:8000`.

### 5. Crear usuario admin

```bash
python -m manager.manager create-admin-user admin
```

---

## Configuración

La configuración se maneja con `pydantic-settings` a través de dos clases:

1. **`CoreSettings`** (`core/config.py`): base de datos, Redis, JWT, seguridad, Sentry, timezone.
2. **`Settings`** (`server/config.py`): extiende `CoreSettings` con configuración del servidor: CORS, rate limiting, paginación, rutas de documentación.

Todas las variables se leen desde `.env` automáticamente.

Ver `.env.example` para la lista completa.

---

## CLI Manager

```bash
python -m manager.manager [comando]
```

| Comando | Descripción |
|---------|-------------|
| `info` | Muestra el árbol de estructura del proyecto |
| `create-admin-user <name>` | Crea un usuario admin (solicita email y password) |
| `create-model` | Abre TUI interactiva para generar modelos SQLModel |
| `run-server` | Levanta Docker + Celery + Uvicorn |

### TUI `create-model`

Una aplicación Textual interactiva para generar modelos sin escribir código manualmente:

- **Sidebar** con exploración de modelos existentes por carpeta.
- **Formulario dinámico**: agregar/quitar campos con nombre, tipo, nullable, primary key, unique, index, default, max_length.
- **Selector de carpeta** destino dentro de `core/models/`.
- **Creación de carpetas** nuevas inline.
- **Generación** con template Mako que produce el archivo .py listo para usar.

---

## Documentación de la API

Una vez corriendo el servidor:

| Herramienta | URL |
|-------------|-----|
| Swagger UI | `http://localhost:8000/docs` |
| Redoc | `http://localhost:8000/redoc` |
| Scalar | `http://localhost:8000/scalar` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Health Check | `http://localhost:8000/scalar/health` |

### Endpoints principales

| Ruta | Métodos | Auth | Descripción |
|------|---------|------|-------------|
| `/auth/register` | POST | No | Registrar usuario |
| `/auth/login` | POST | No | Iniciar sesión (JWT) |
| `/auth/me` | GET | Sí | Perfil del usuario actual |
| `/user/me` | GET, PUT, DELETE | Sí | CRUD del perfil propio |
| `/user/change-password` | POST | Sí | Cambiar contraseña |
| `/user/{id}` | GET, PUT, DELETE | Sí | CRUD de usuarios (vía crud router) |
| `/admin/` | GET | Sí | Modelos registrados |
| `/admin/users` | GET | Sí | Listar usuarios |
| `/admin/users/{id}` | GET, PATCH, DELETE | Sí | Gestionar usuarios |
| `/admin/logs` | POST | Sí | Consultar logs |
| `/scalar/health` | GET | No | Health check |

---

## Docker

### docker-compose.yaml

```yaml
services:
  server:       # FastAPI + Uvicorn (puerto 8000 → 8080)
  celery_worker:# Celery worker
  redis:        # Redis con persistencia + auth
  postgres:     # PostgreSQL 18 Alpine
```

```bash
docker compose up --build
```

### Dockerfile

- **Base**: `python:3.14-alpine3.23`
- Puerto expuesto: `8000`
- Comando: `uvicorn server.main:app`

---

## Tests

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=server --cov=core --cov-report=term-missing

# Tests específicos
pytest tests/server/test_main.py -v
pytest tests/core/test_logic.py -v
```

Configuración en `pytest.ini`:
- `asyncio_mode = auto` — los tests asíncronos funcionan sin decoradores extra.
- `--tb=short` — tracebacks compactos.
- Warnings de deprecación ignorados.

---

## Migraciones (Alembic)

```bash
# Crear migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## ¿Por qué existe este proyecto?

Porque la mayoría de los templates de FastAPI que existen:

- Mezclan lógica de negocio con rutas HTTP.
- No tienen una capa de persistencia desacoplada (SPI).
- Usan bcrypt como si fuera 2010 (Argon2 es el estándar actual).
- No tienen logging que sirva para producción (con redacción de datos sensibles).
- No incluyen task queue ni caché.
- El "CRUD automático" que traen es una broma.

Este proyecto no es un boilerplate para copiar y pegar. Es una **base sólida** para construir sobre ella, con decisiones técnicas justificadas y una arquitectura que escala.

---

## Licencia

MIT
