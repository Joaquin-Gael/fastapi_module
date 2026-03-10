# Project Structure

```
fastapi_module/
├─ server/
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ utils/
│  │  └─ cache/
│  ├─ routes/
│  ├─ schemas/
│  ├─ templates/
│  ├─ forms/
│  ├─ middlewares/
│  ├─ data/
│  └─ test/
├─ DockerFile
├─ docker-compose.yaml
├─ pyproject.toml
├─ poetry.lock
├─ .env.example
└─ README.md
```

---

## Folder Descriptions (to be completed)

- **server/**: 
  - *Description*: Es la base del proyecto y donde esta toda la logica desde el wraper de la api hasta la logica central del core

- **server/core/**: 
  - *Description*: Es donde esta la logica real de el sistema, todas las funciones bases estan en esta carpeta organizadas por sub-carpetas

- **server/core/utils/**: 
  - *Description*: En esta carpeta se generan los scripts/herramientas/extras que se pueden invocar a lo largo de todo el proyecto

- **server/core/cache/**: 
  - *Description*: En esta carpeta se manega la configuracion de los clientes de redis

- **server/routes/**: 
  - *Description*: En esta carpeta se maneja la router madre/main que es el embudo donde convergen todos los routers

- **server/schemas/**: 
  - *Description*: En esta carpeta se manejan los esquemas de respuestas de las rutas que estan finamente relacionados con los modelos

- **server/templates/**: 
  - *Description*: En esta carpeta solamente se almacenan los archivos html y algunas utils para este fin

- **server/forms/**: 
  - *Description*: 

- **server/middlewares/**: 
  - *Description*: 

- **server/data/**: 
  - *Description*: 

- **server/test/**: 
  - *Description*: 

- **DockerFile**: 
  - *Description*: 

- **docker-compose.yaml**: 
  - *Description*: 

- **pyproject.toml**: 
  - *Description*: 

- **poetry.lock**: 
  - *Description*: 

- **.env.example**: 
  - *Description*: 

- **README.md**: 
  - *Description*:
