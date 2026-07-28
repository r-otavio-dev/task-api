import sqlite3

import pytest

from database import (
    INITIAL_TASKS,
    create_task,
    delete_task,
    get_db_connection,
    get_task,
    initialize_database,
    list_tasks,
    update_task,
)


def test_initialize_database_creates_expected_table(tmp_path):
    database_path = tmp_path / "tasks.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(tasks)").fetchall()

    assert [(column[1], column[2], column[3], column[5]) for column in columns] == [
        ("id", "INTEGER", 0, 1),
        ("title", "TEXT", 1, 0),
        ("done", "BOOLEAN", 1, 0),
    ]


def test_initialize_database_seeds_three_initial_tasks(tmp_path):
    database_path = tmp_path / "tasks.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()

    assert rows == [
        (task["id"], task["title"], int(task["done"]))
        for task in INITIAL_TASKS
    ]


def test_initialize_database_does_not_duplicate_seed_data(tmp_path):
    database_path = tmp_path / "tasks.db"

    initialize_database(database_path)
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

    assert task_count == 3


def test_initialize_database_does_not_seed_when_table_is_not_empty(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute("DELETE FROM tasks")
        connection.execute(
            "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
            (10, "Tarefa personalizada", 0),
        )
        connection.commit()

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks"
        ).fetchall()

    assert rows == [(10, "Tarefa personalizada", 0)]


def test_get_db_connection_closes_connection_after_context(tmp_path):
    database_path = tmp_path / "tasks.db"

    with get_db_connection(database_path) as connection:
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_list_tasks_reads_rows_and_converts_booleans(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    tasks = list_tasks(database_path)

    assert tasks == INITIAL_TASKS
    assert tasks[0]["done"] is False
    assert tasks[2]["done"] is True


def test_get_task_reads_one_row_by_id(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    task = get_task(2, database_path)

    assert task == INITIAL_TASKS[1]


def test_get_task_returns_none_for_unknown_id(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    task = get_task(999, database_path)

    assert task is None


def test_create_task_inserts_and_returns_generated_id(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    created_task = create_task("Aprender SQLite", database_path)

    assert created_task == {
        "id": 4,
        "title": "Aprender SQLite",
        "done": False,
    }
    assert get_task(4, database_path) == created_task


def test_create_task_uses_parameters_for_untrusted_title(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)
    suspicious_title = "'); DROP TABLE tasks; --"

    created_task = create_task(suspicious_title, database_path)

    assert created_task["title"] == suspicious_title
    assert len(list_tasks(database_path)) == 4


def test_update_task_persists_title_and_done(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    updated_task = update_task(
        1,
        "Estudar SQLite",
        True,
        database_path,
    )

    assert updated_task == {
        "id": 1,
        "title": "Estudar SQLite",
        "done": True,
    }
    assert get_task(1, database_path) == updated_task


def test_update_task_returns_none_for_unknown_id(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    updated_task = update_task(
        999,
        "Tarefa inexistente",
        False,
        database_path,
    )

    assert updated_task is None


def test_delete_task_removes_row_and_reports_result(tmp_path):
    database_path = tmp_path / "tasks.db"
    initialize_database(database_path)

    assert delete_task(2, database_path) is True
    assert get_task(2, database_path) is None
    assert delete_task(2, database_path) is False
