# Admin Panel — Vue 3 SPA + Dynamic API + Extension System

## Stack

| Capa | Tecnología |
|------|------------|
| Frontend | Vue 3 + TypeScript + Vue Router + Pinia |
| UI | DaisyUI + TailwindCSS |
| Backend | FastAPI + SQLModel + SQLAlchemy introspection |
| Build | Vite → `server/templates/admin/` |
| Auth | Server-side login → HttpOnly cookie (JWT) |
| Extensions | Proyectos Vue independientes, bundle estático |

---

## Estructura de archivos

```
fastapi_module/
├── server/
│   ├── routes/
│   │   ├── admin.py              # Router principal: incluye api + spa + login
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── api.py            # CRUD dinámico + schema de modelos
│   │       ├── spa.py            # Catch-all que sirve index.html
│   │       └── login.py          # Login server-side + cookie
│   └── templates/
│       └── admin/                # BUILD OUTPUT de Vite (se genera solo)
│           ├── index.html
│           ├── login.html         # Jinja2 minimal, existe antes del build
│           └── assets/
│               ├── index-*.js
│               └── index-*.css
│
├── admin-panel/                  # Proyecto Vue 3 (source)
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── api/
│   │   │   └── client.ts         # fetch wrapper con cookie automática
│   │   ├── composables/
│   │   │   ├── useRegistry.ts    # Model registry desde /admin/api/registry
│   │   │   ├── useCrud.ts        # CRUD genérico para cualquier modelo
│   │   │   └── useExtension.ts   # Extension registry
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AdminLayout.vue
│   │   │   │   ├── AdminSidebar.vue
│   │   │   │   └── AdminNavbar.vue
│   │   │   ├── auto/
│   │   │   │   ├── AutoTable.vue        # Tabla genérica sort/filter/page
│   │   │   │   ├── AutoForm.vue         # Formulario dinámico por tipo
│   │   │   │   ├── AutoDetail.vue       # Detalle con relaciones
│   │   │   │   └── FieldRenderer.vue    # Router de fields según tipo
│   │   │   └── fields/
│   │   │       ├── StringField.vue
│   │   │       ├── NumberField.vue
│   │   │       ├── BooleanField.vue
│   │   │       ├── DateTimeField.vue
│   │   │       ├── EnumField.vue
│   │   │       ├── RelationField.vue
│   │   │       ├── JsonField.vue
│   │   │       └── PasswordField.vue
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── ModelList.vue
│   │   │   ├── ModelForm.vue      # Create + Edit según params
│   │   │   └── ModelDetail.vue
│   │   └── extensions.registry.ts # GENERADO: registro de extensiones
│   │
│   ├── extensions/                # Extensiones instaladas (cada una es un proyecto)
│   │   └── mi-extension/
│   │       ├── extension.json
│   │       └── src/
│   │           └── index.ts
│   │
│   ├── scripts/
│   │   └── build-extensions.ts    # Pre-build: escanea extensions/* y genera registry
│   ├── vite.config.ts             # outDir: ../server/templates/admin
│   ├── tailwind.config.ts
│   ├── package.json
│   └── tsconfig.json
│
└── ADMIN_PANEL_PLAN.md           # Este archivo
```

---

## Backend — Dynamic Admin API

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/admin/api/registry` | Lista todos los modelos registrados con metadata |
| `GET` | `/admin/api/{model}/schema` | Schema del modelo: campos, tipos, relaciones, validaciones |
| `GET` | `/admin/api/{model}/` | Listado paginado + filtros + ordenamiento |
| `GET` | `/admin/api/{model}/{id}` | Detalle de un registro |
| `POST` | `/admin/api/{model}/` | Crear registro (validación dinámica) |
| `PATCH` | `/admin/api/{model}/{id}` | Actualizar registro |
| `DELETE` | `/admin/api/{model}/{id}` | Eliminar registro |

### Dynamic Model Introspection (api.py)

Se usa `SQLAlchemy inspect()` + `SQLModel.model_fields` para generar schemas Pydantic en runtime:

```python
from sqlalchemy import inspect as sa_inspect

def get_model_schema(model_class: type[SQLModel]) -> dict:
    mapper = sa_inspect(model_class)
    fields = {}

    for col in mapper.columns:
        fields[col.name] = {
            "type": _resolve_python_type(col.type),
            "required": not col.nullable,
            "default": _serialize_default(col.default),
            "unique": col.unique,
            "primary_key": col.primary_key,
            "max_length": getattr(col.type, "length", None),
        }

    for rel in mapper.relationships:
        fields[rel.key] = {
            "type": "relationship",
            "direction": rel.direction.name,  # MANYTOONE | ONETOMANY | MANYTOMANY
            "related_model": rel.mapper.class_.__name__,
        }

    return fields
```

**Reglas de negocio:**
- Relaciones MANYTOMANY se excluyen del CRUD directo (se manejan como chips/tags)
- Passwords se hashean automáticamente vía el setter del modelo (`User.set_password`)
- El `id` (UUID) se genera automáticamente y es read-only en forms
- `created_at` / `updated_at` son auto-manejados y read-only

### Re-uso del mecanismo existente

El decorador `@register()` ya existe en `core/models/base/decorators/register.py` y almacena metadata en Redis (`admin:registry`). El nuevo `admin/api.py`:

1. Lee `admin:registry` de Redis (igual que el actual `GET /admin/`)
2. Importa dinámicamente la clase del modelo desde `model_module`
3. Genera schema + endpoints CRUD en base a la introspección

---

## Frontend — Vue 3 SPA

### Rutas

```typescript
const routes = [
  { path: "/admin", redirect: "/admin/dashboard" },
  { path: "/admin/dashboard", component: Dashboard },
  { path: "/admin/login", component: LoginView },  // solo si no hay cookie
  { path: "/admin/:model", component: ModelList },
  { path: "/admin/:model/new", component: ModelForm },
  { path: "/admin/:model/:id", component: ModelDetail },
  { path: "/admin/:model/:id/edit", component: ModelForm },
]
```

### AutoTable.vue — Tabla genérica

Props:
- `modelName: string`
- `fields: FieldDefinition[]` (desde schema)
- `data: Record[]`
- `loading: boolean`

Features:
- Sort por columna (click en header)
- Filtro por texto global
- Paginación server-side
- Checkbox para bulk actions
- Acciones por fila: edit, delete, custom (de extensions)

### AutoForm.vue — Formulario dinámico

Props:
- `modelName: string`
- `fields: FieldDefinition[]`
- `record?: Record` (si es edit)
- `overrides?: Record<string, Component>` (de extensiones)

Renderiza cada campo según su tipo usando `FieldRenderer.vue`:
```vue
<FieldRenderer
  :field="field"
  :value="formValues[field.name]"
  @update="(val) => formValues[field.name] = val"
/>
```

`FieldRenderer.vue` switchea entre los componentes de `fields/` según el tipo:
- `string` → `StringField.vue` (o `PasswordField.vue` si el campo se llama "password")
- `integer` / `float` → `NumberField.vue`
- `boolean` → `BooleanField.vue`
- `datetime` → `DateTimeField.vue`
- `enum` → `EnumField.vue` (select)
- `relationship` (MANYTOONE) → `RelationField.vue` (select con search)
- `relationship` (MANYTOMANY) → multi-select con chips
- `json` → `JsonField.vue` (textarea + formato)

---

## Login Flow (Server-side + Cookie)

```
┌─────────────┐    GET /admin/login     ┌──────────────┐
│   Browser   │ ──────────────────────► │  FastAPI      │
│             │ ◄────────────────────── │  (Jinja2)     │
│             │    login.html (form)     │              │
│             │                         │              │
│             │    POST /admin/login     │              │
│             │ ──────────────────────► │  Valida       │
│             │    (email + password)    │  credenciales │
│             │                         │              │
│             │ ◄────────────────────── │              │
│             │    302 + Set-Cookie      │  JWT en      │
│             │    → /admin/dashboard    │  HttpOnly     │
│             │                         │  cookie       │
│             │    GET /admin/dashboard  │              │
│             │ ──────────────────────► │  Sirve SPA    │
│             │ ◄────────────────────── │  index.html   │
│             │    index.html (Vue SPA)  │              │
│             │                         │              │
│             │    GET /admin/api/...    │  API normal   │
│             │    (cookie automática)   │  con JWT      │
```

La cookie HttpOnly:
- `SameSite=Lax` (default en navegadores modernos)
- `Secure` en producción
- Path `/admin/`
- Expira cuando expira el JWT

---

## Sistema de Extensiones

### Estructura de una extensión

```
admin-panel/extensions/mi-extension/
├── extension.json
├── src/
│   ├── index.ts
│   └── components/
│       ├── CustomUserList.vue
│       ├── CustomUserForm.vue
│       └── AnalyticsPage.vue
├── package.json       # Dependencias específicas de la extensión
├── tsconfig.json
└── vite.config.ts     # Quién sabe, capaz la extensión tiene su propio build
```

### extension.json

```json
{
  "$schema": "../../extensions.schema.json",
  "name": "mi-extension",
  "version": "1.0.0",
  "description": "Personalización del panel de Users + página de analytics",
  "overrides": [
    {
      "model": "User",
      "view": "list",
      "component": "CustomUserList"
    },
    {
      "model": "User",
      "view": "form",
      "component": "CustomUserForm"
    }
  ],
  "pages": [
    {
      "path": "/analytics",
      "label": "Analytics",
      "icon": "ChartBarIcon",
      "component": "AnalyticsPage"
    }
  ],
  "actions": [
    {
      "model": "User",
      "label": "Export CSV",
      "icon": "ArrowDownTrayIcon",
      "action": "exportCsv"
    }
  ]
}
```

### Build de extensiones

El script `scripts/build-extensions.ts` ejecuta antes del build de Vite:

1. Escanea `extensions/*/extension.json`
2. Valida contra `extensions.schema.json`
3. Genera `src/extensions.registry.ts`:

```typescript
// GENERATED — do not edit manually
import { defineAsyncComponent } from "vue"
import type { ExtensionManifest } from "./types/extension"

export const extensionOverrides: ExtensionManifest["overrides"] = [
  {
    model: "User",
    view: "list",
    component: defineAsyncComponent(() =>
      import("./extensions/mi-extension/src/components/CustomUserList.vue")
    ),
  },
  {
    model: "User",
    view: "form",
    component: defineAsyncComponent(() =>
      import("./extensions/mi-extension/src/components/CustomUserForm.vue")
    ),
  },
]

export const extensionPages: ExtensionManifest["pages"] = []

export const extensionActions: ExtensionManifest["actions"] = []
```

### Runtime: cómo se aplican

En `ModelList.vue`:
```typescript
const override = findOverride(currentModel.value, "list")
const ListComponent = override ? override.component : AutoTable
```

En `AdminSidebar.vue`:
```typescript
const dynamicPages = computed(() => [
  ...defaultPages,
  ...extensionPages.value,
])
```

---

## Build & Dev

### Desarrollo

```bash
# Terminal 1 — FastAPI
cd fastapi_module
uvicorn server.main:app --reload

# Terminal 2 — Vue dev server (con proxy a FastAPI)
cd admin-panel
npm run dev
# → http://localhost:5173/admin/ (proxy API a :8000)
```

`vite.config.ts`:
```typescript
export default defineConfig({
  base: "/admin/",
  server: {
    port: 5173,
    proxy: { "/admin/api": "http://localhost:8000" },
  },
  build: {
    outDir: "../server/templates/admin",
    emptyOutDir: true,
  },
})
```

### Producción

```bash
cd admin-panel
npm run build
# → compila a server/templates/admin/
```

FastAPI sirve todo via `StaticFiles` + catch-all en `/admin/{path:path}`.

---

## Convenios

- **Las extensiones NO tocan el core de `admin-panel`**. Solo declaran overrides.
- **El login es responsabilidad exclusiva del backend**. La SPA solo consume la cookie.
- **Los modelos se registran con `@register()`**, no hay configuración extra.
- **Password fields**: solo se muestran en create/edit, nunca en list/detail. El campo se renderiza como `PasswordField.vue`.
- **No se exponen datos sensibles** en el schema. El `fields` del decorador filtra qué se muestra.
