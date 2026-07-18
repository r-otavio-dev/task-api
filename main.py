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


app = FastAPI(
    title="Task API",
    version="1.0",
    description="API CRUD para gerenciamento de tarefas em memória.",
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


INITIAL_TASKS = [
    {"id": 1, "title": "Estudar Python", "done": False},
    {"id": 2, "title": "Fazer atividade", "done": False},
    {"id": 3, "title": "Enviar projeto para o GitHub", "done": True},
]

# Esta lista é a única forma de armazenamento da aplicação.
tasks = [task.copy() for task in INITIAL_TASKS]


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


def procurar_indice(task_id: int) -> int | None:
    for indice, task in enumerate(tasks):
        if task["id"] == task_id:
            return indice
    return None


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
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Buscar uma tarefa pelo ID",
)
def buscar_tarefa(task_id: int):
    indice = procurar_indice(task_id)
    if indice is None:
        return resposta_nao_encontrada(task_id)
    return tasks[indice]


@app.post(
    "/tasks",
    response_model=Task,
    status_code=201,
    summary="Criar uma tarefa",
)
def criar_tarefa(payload: TaskCreate):
    proximo_id = max((task["id"] for task in tasks), default=0) + 1
    nova_tarefa = {
        "id": proximo_id,
        "title": payload.title,
        "done": False,
    }
    tasks.append(nova_tarefa)
    return nova_tarefa


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Atualizar uma tarefa",
)
def atualizar_tarefa(task_id: int, payload: TaskUpdate):
    indice = procurar_indice(task_id)
    if indice is None:
        return resposta_nao_encontrada(task_id)

    alteracoes = payload.model_dump(exclude_unset=True)
    tasks[indice].update(alteracoes)
    return tasks[indice]


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Excluir uma tarefa",
)
def excluir_tarefa(task_id: int):
    indice = procurar_indice(task_id)
    if indice is None:
        return resposta_nao_encontrada(task_id)

    tasks.pop(indice)
    return Response(status_code=204)
