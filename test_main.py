import pytest
from fastapi.testclient import TestClient

from main import INITIAL_TASKS, app, tasks


client = TestClient(app)


@pytest.fixture(autouse=True)
def restaurar_tarefas():
    """Garante que cada teste comece com as três tarefas de exemplo."""
    tasks[:] = [task.copy() for task in INITIAL_TASKS]


def test_inicio_retorna_informacoes_da_api():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_health_retorna_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_listar_tarefas_retorna_200():
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == INITIAL_TASKS


def test_buscar_tarefa_existente_retorna_200():
    response = client.get("/tasks/1")

    assert response.status_code == 200
    assert response.json() == INITIAL_TASKS[0]


def test_buscar_id_inexistente_retorna_404():
    response = client.get("/tasks/99")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_criar_tarefa_valida_retorna_201():
    response = client.post("/tasks", json={"title": "  Buy milk  "})

    assert response.status_code == 201
    assert response.json() == {"id": 4, "title": "Buy milk", "done": False}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": 123},
        {"title": None},
        {"title": "Válido", "done": False},
    ],
)
def test_criar_tarefa_invalida_retorna_400(payload):
    response = client.post("/tasks", json=payload)

    assert response.status_code == 400
    assert "error" in response.json()


def test_atualizar_titulo_e_done_retorna_200():
    response = client.put(
        "/tasks/1",
        json={"title": "  Estudar FastAPI  ", "done": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Estudar FastAPI",
        "done": True,
    }


def test_atualizar_somente_done_retorna_200():
    response = client.put("/tasks/2", json={"done": True})

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "title": "Fazer atividade",
        "done": True,
    }


def test_atualizar_id_inexistente_retorna_404():
    response = client.put("/tasks/99", json={"done": True})

    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": 123},
        {"title": None},
        {"done": "true"},
        {"done": 1},
        {"done": None},
        {"unknown": "field"},
    ],
)
def test_atualizacao_invalida_retorna_400(payload):
    response = client.put("/tasks/1", json=payload)

    assert response.status_code == 400
    assert "error" in response.json()


def test_atualizacao_invalida_nao_altera_parte_da_tarefa():
    response = client.put(
        "/tasks/1",
        json={"title": "Título que não deve ficar", "done": None},
    )

    assert response.status_code == 400
    assert client.get("/tasks/1").json() == INITIAL_TASKS[0]


def test_excluir_tarefa_valida_retorna_204_e_corpo_vazio():
    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks/1").status_code == 404


def test_excluir_id_inexistente_retorna_404():
    response = client.delete("/tasks/99")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}
