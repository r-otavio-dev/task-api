# Task API

API para criar, consultar, atualizar e excluir tarefas. O projeto foi feito em
Python com FastAPI e usa uma lista em memória como armazenamento.

## O que é CRUD?

CRUD reúne as quatro operações básicas feitas com dados:

- **Create (criar):** cadastrar uma tarefa com `POST`.
- **Read (ler):** listar ou buscar tarefas com `GET`.
- **Update (atualizar):** alterar uma tarefa com `PUT`.
- **Delete (excluir):** remover uma tarefa com `DELETE`.

## Tecnologias utilizadas

- Python 3.14.4
- FastAPI 0.139.2
- Pydantic 2.13.4
- Uvicorn 0.51.0
- Pytest 9.1.1
- FastAPI TestClient com HTTPX2 2.7.0

## Instalação

Abra o PowerShell na pasta do projeto e crie o ambiente virtual:

```powershell
py -m venv .venv
```

Instale as dependências registradas no projeto:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Iniciar o servidor

Use este único comando na pasta do projeto:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app
```

A API ficará disponível em `http://localhost:8000`.

## Swagger

Com o servidor em execução, abra a documentação interativa em:

<http://localhost:8000/docs>

O Swagger permite visualizar e experimentar os endpoints pelo navegador.

## Endpoints

| Método | Rota | Descrição | Códigos HTTP |
| --- | --- | --- | --- |
| `GET` | `/` | Mostra nome, versão e rota principal da API. | `200` |
| `GET` | `/health` | Confirma que o servidor está respondendo. | `200` |
| `GET` | `/tasks` | Lista todas as tarefas. | `200` |
| `GET` | `/tasks/{task_id}` | Busca uma tarefa pelo ID. | `200`, `404` |
| `POST` | `/tasks` | Cria uma tarefa e gera seu ID. | `201`, `400` |
| `PUT` | `/tasks/{task_id}` | Atualiza `title`, `done` ou ambos. | `200`, `400`, `404` |
| `DELETE` | `/tasks/{task_id}` | Exclui uma tarefa. | `204`, `404` |

Erros de corpo ou tipo no `POST` e no `PUT` retornam código `400` e um objeto
JSON com o campo `error`. IDs inexistentes retornam código `404`.

## Exemplos de JSON

Corpo para criar uma tarefa com `POST /tasks`:

```json
{
  "title": "Buy milk"
}
```

Corpo para atualizar os dois campos permitidos com `PUT /tasks/1`:

```json
{
  "title": "Buy milk and bread",
  "done": true
}
```

Também é possível enviar somente `title` ou somente `done` no `PUT`.

## Exemplo real com curl

Com o servidor em execução, o comando abaixo foi testado no PowerShell:

```powershell
curl.exe -i http://localhost:8000/health
```

Saída real obtida em 18 de julho de 2026:

```http
HTTP/1.1 200 OK
date: Sat, 18 Jul 2026 16:31:49 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

## Armazenamento em memória

As tarefas ficam somente na lista `tasks` enquanto o programa está em execução.
O projeto não usa banco de dados e não grava tarefas em arquivos. Ao reiniciar o
servidor, alterações feitas pela API desaparecem e as três tarefas de exemplo
voltam a ser carregadas.

## Executar os testes

Na pasta do projeto, execute:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

A suíte verifica as respostas de leitura, criação, atualização e exclusão, além
dos códigos `400`, `404`, `201` e `204` exigidos pela API. Na validação desta
versão, os 27 casos passaram.
