from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictStr,
    field_validator,
    model_validator,
)

import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="Task API",
    version="1.0",
    description="API CRUD para gerenciamento de tarefas com SQLite.",
    lifespan=lifespan,
)


class ApiInfo(BaseModel):
    name: str
    version: str
    endpoints: list[str]


class HealthStatus(BaseModel):
    status: str


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Title cannot be empty")
        return title


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr | None = None
    done: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @model_validator(mode="after")
    def validar_campos_enviados(self):
        if not self.model_fields_set:
            raise ValueError("Request body cannot be empty")
        if "done" in self.model_fields_set and self.done is None:
            raise ValueError("Done must be true or false")
        return self


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
):
    """Converte os erros automáticos de validação do FastAPI em HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"},
    )


def resposta_nao_encontrada(task_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.get(
    "/",
    response_model=ApiInfo,
    summary="Exibir informações da API",
)
def inicio():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    response_model=HealthStatus,
    summary="Verificar a saúde do servidor",
)
def verificar_saude():
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=list[Task],
    summary="Listar todas as tarefas",
)
def listar_tarefas():
    return database.list_tasks()


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Buscar uma tarefa pelo ID",
)
def buscar_tarefa(task_id: int):
    task = database.get_task(task_id)
    if task is None:
        return resposta_nao_encontrada(task_id)
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=201,
    summary="Criar uma tarefa",
)
def criar_tarefa(payload: TaskCreate):
    return database.create_task(payload.title)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Atualizar uma tarefa",
)
def atualizar_tarefa(task_id: int, payload: TaskUpdate):
    current_task = database.get_task(task_id)
    if current_task is None:
        return resposta_nao_encontrada(task_id)

    changes = payload.model_dump(exclude_unset=True)
    title = changes.get("title", current_task["title"])
    done = changes.get("done", current_task["done"])

    updated_task = database.update_task(task_id, title, done)
    if updated_task is None:
        return resposta_nao_encontrada(task_id)

    return updated_task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Excluir uma tarefa",
)
def excluir_tarefa(task_id: int):
    if not database.delete_task(task_id):
        return resposta_nao_encontrada(task_id)

    return Response(status_code=204)
