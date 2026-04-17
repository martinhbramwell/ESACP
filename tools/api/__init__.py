"""ESACP Control Plane API.

Thin FastAPI app wiring — app instance, middleware, exception handlers, and
route inclusion. All endpoint implementations live in ``tools/api/routes/``.
Shared helpers live in ``tools/api/helpers.py`` and ``tools/api/jobs.py``.

Start (from project root):
    uvicorn tools.api:app --port 8088 --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tools.api.routes import (
    destroy, health, hosts, jobs_api, power, promote, provision,
    template, wizard,
)
from tools.pipeline.orchestration.host_cleanup_check import (
    HostAlreadyProvisionedError,
)
from tools.pipeline.orchestration.host_registration import (
    HostConflictError, HostRegistrationError,
)

app = FastAPI(title="ESACP Control Plane API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HostRegistrationError)
async def _handle_host_registration_error(_: Request, exc: HostRegistrationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(HostConflictError)
async def _handle_host_conflict_error(_: Request, exc: HostConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(HostAlreadyProvisionedError)
async def _handle_host_provisioned_error(_: Request, exc: HostAlreadyProvisionedError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


for _mod in (hosts, provision, destroy, power, health, template,
             wizard, jobs_api, promote):
    app.include_router(_mod.router)
