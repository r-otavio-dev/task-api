import sqlite3

from database import INITIAL_TASKS, initialize_database


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
