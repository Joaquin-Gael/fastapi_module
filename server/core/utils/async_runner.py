import asyncio
import threading
from datetime import timedelta


def run_async(coro: asyncio._CoroutineLike):
    _results = []
    _errors = []
    _finish = threading.Event()

    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _results.append(loop.run_until_complete(coro))
        except Exception as e:
            _errors.append(e)
        finally:
            try:
                if loop is not None:
                    loop.close()
            finally:
                _finish.set()

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    completed: bool = _finish.wait(timedelta(seconds=10).seconds)
    if not completed:
        raise TimeoutError("")

    t.join()

    if _errors:
        raise _errors[0]

    return _results[0]
