import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
from database import INITIAL_TASKS
from main import app


@pytest.fixture
def database_path(tmp_path, monkeypatch):
    path = tmp_path / "tasks.db"
    monkeypatch.setattr(database, "DATABASE_PATH", path)
    return path


@pytest.fixture
def client(database_path):
    """Inicia a API com um banco temporário novo para cada teste."""
    with TestClient(app) as test_client:
        yield test_client


def test_inicio_retorna_informacoes_da_api(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_health_retorna_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_listar_tarefas_retorna_200(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == INITIAL_TASKS


def test_buscar_tarefa_existente_retorna_200(client):
    response = client.get("/tasks/1")

    assert response.status_code == 200
    assert response.json() == INITIAL_TASKS[0]


def test_buscar_id_inexistente_retorna_404(client):
    response = client.get("/tasks/99")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_criar_tarefa_valida_retorna_201(client):
    response = client.post("/tasks", json={"title": "  Buy milk  "})

    assert response.status_code == 201
    assert response.json() == {
        "id": 4,
        "title": "Buy milk",
        "done": False,
    }


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
def test_criar_tarefa_invalida_retorna_400(client, payload):
    response = client.post("/tasks", json=payload)

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid request body"}


def test_tarefa_criada_persiste_em_nova_conexao(client, database_path):
    created_task = client.post(
        "/tasks",
        json={"title": "Aprender persistência"},
    ).json()

    with sqlite3.connect(database_path) as connection:
        persisted_row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (created_task["id"],),
        ).fetchone()

    assert persisted_row == (
        created_task["id"],
        "Aprender persistência",
        0,
    )


def test_atualizar_titulo_e_done_retorna_200(client):
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


def test_atualizar_somente_titulo_preserva_done(client):
    response = client.put(
        "/tasks/3",
        json={"title": "  Publicar projeto  "},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 3,
        "title": "Publicar projeto",
        "done": True,
    }


def test_atualizar_somente_done_retorna_200(client):
    response = client.put("/tasks/2", json={"done": True})

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "title": "Fazer atividade",
        "done": True,
    }


def test_atualizar_id_inexistente_retorna_404(client):
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
def test_atualizacao_invalida_retorna_400(client, payload):
    response = client.put("/tasks/1", json=payload)

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid request body"}


def test_atualizacao_invalida_nao_altera_parte_da_tarefa(client):
    response = client.put(
        "/tasks/1",
        json={"title": "Título que não deve ficar", "done": None},
    )

    assert response.status_code == 400
    assert client.get("/tasks/1").json() == INITIAL_TASKS[0]


def test_excluir_tarefa_valida_retorna_204_e_corpo_vazio(client):
    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks/1").status_code == 404


def test_excluir_id_inexistente_retorna_404(client):
    response = client.delete("/tasks/99")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_done_converte_entre_json_booleano_e_sqlite_inteiro(
    client,
    database_path,
):
    response = client.put("/tasks/1", json={"done": True})

    with sqlite3.connect(database_path) as connection:
        stored_done = connection.execute(
            "SELECT done FROM tasks WHERE id = ?",
            (1,),
        ).fetchone()[0]

    assert response.json()["done"] is True
    assert stored_done == 1
    assert isinstance(stored_done, int)


def test_dados_persistem_e_seed_nao_duplica_apos_reiniciar(
    database_path,
):
    with TestClient(app) as first_client:
        created_task = first_client.post(
            "/tasks",
            json={"title": "Sobreviver ao reinício"},
        ).json()

    with TestClient(app) as restarted_client:
        response = restarted_client.get(
            f"/tasks/{created_task['id']}"
        )
        all_tasks = restarted_client.get("/tasks").json()

    assert response.status_code == 200
    assert response.json() == created_task
    assert len(all_tasks) == 4
