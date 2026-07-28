from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3


PROJECT_DIRECTORY = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIRECTORY / "tasks.db"

INITIAL_TASKS = [
    {"id": 1, "title": "Estudar Python", "done": False},
    {"id": 2, "title": "Fazer atividade", "done": False},
    {"id": 3, "title": "Enviar projeto para o GitHub", "done": True},
]

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0
)
"""


@contextmanager
def get_db_connection(
    database_path: str | Path | None = None,
) -> Iterator[sqlite3.Connection]:
    path = Path(database_path) if database_path is not None else DATABASE_PATH
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


def initialize_database(database_path: str | Path | None = None) -> None:
    with get_db_connection(database_path) as connection:
        connection.execute(CREATE_TASKS_TABLE)

        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        if task_count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    (task["title"], int(task["done"]))
                    for task in INITIAL_TASKS
                ],
            )

        connection.commit()
