import time

from fastapi import Request, Response


async def request_timing_middleware(request: Request, call_next) -> Response:
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{elapsed_time:.6f}"
    return response