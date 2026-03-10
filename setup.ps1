uvicorn server.main:app --host $env:SERVER_HOST --port $env:SERVER_PORT --loop $env.LOOP_MASTER
