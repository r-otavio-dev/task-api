# Task API com FastAPI e SQLite

API REST para criar, consultar, atualizar e excluir tarefas. O projeto usa
FastAPI para receber requisições HTTP, Pydantic para validar os dados e SQLite
para armazená-los de forma persistente.

Esta versão conclui a atividade **W3 · A1 — Connecting your CRUD to the
database** sem alterar o contrato público da API anterior.

## Objetivo

O projeto demonstra um CRUD completo:

- **Create:** cria uma tarefa com `POST`;
- **Read:** consulta tarefas com `GET`;
- **Update:** altera uma tarefa com `PUT`;
- **Delete:** remove uma tarefa com `DELETE`.

Cada tarefa possui três campos:

```json
{
  "id": 1,
  "title": "Estudar Python",
  "done": false
}
```

## Tecnologias

- Python;
- FastAPI;
- Pydantic;
- Uvicorn;
- SQLite por meio do módulo nativo `sqlite3`;
- Pytest e FastAPI TestClient.

O SQLite foi escolhido porque é simples, leve e adequado para aprendizado e
aplicações locais. Ele não exige instalar ou manter um servidor de banco de
dados separado: toda a base fica em um único arquivo.

## Como o banco funciona

Na primeira inicialização do servidor, a aplicação cria `tasks.db` na mesma
pasta de `main.py`. Em seguida, cria a tabela e insere três tarefas de exemplo
somente se ela estiver completamente vazia.

Reiniciar a aplicação não recria o banco nem duplica as tarefas. Os dados
criados, atualizados ou excluídos continuam no arquivo.

O schema utilizado é:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0
);
```

No SQLite, `done` é armazenado como `0` ou `1`. A API converte esses valores
para `false` ou `true` no JSON.

`tasks.db` e os arquivos de journal estão no `.gitignore`, pois são dados
locais gerados durante o uso e não código-fonte.

## Estrutura principal

```text
task-api/
├── database.py
├── docs/
│   └── README.md
├── main.py
├── queries.sql
├── requirements.txt
├── test_database.py
├── test_main.py
└── README.md
```

- `main.py`: modelos, validações e rotas FastAPI;
- `database.py`: conexão, inicialização e operações SQL;
- `queries.sql`: consultas manuais para explorar o banco;
- `test_database.py`: testes da camada SQLite;
- `test_main.py`: testes do contrato HTTP com bancos temporários;
- `docs/`: local reservado para a evidência visual do DB Browser.

## Instalação

Abra o PowerShell na pasta do projeto.

Crie o ambiente virtual:

```powershell
python -m venv .venv
```

Instale as dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não é necessário instalar um pacote Python para o SQLite, pois `sqlite3` faz
parte da biblioteca padrão do Python.

## Iniciando o servidor

Execute:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app
```

O terminal deve informar que o servidor está disponível em:

```text
http://127.0.0.1:8000
```

Abra a documentação interativa:

<http://localhost:8000/docs>

Use `Ctrl+C` no terminal para encerrar o servidor.

## Endpoints e códigos HTTP

| Método | Rota | Função | Sucesso |
|---|---|---|---:|
| `GET` | `/` | Informações da API | `200` |
| `GET` | `/health` | Estado do servidor | `200` |
| `GET` | `/tasks` | Lista todas as tarefas | `200` |
| `GET` | `/tasks/{id}` | Busca uma tarefa | `200` |
| `POST` | `/tasks` | Cria uma tarefa | `201` |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa | `200` |
| `DELETE` | `/tasks/{id}` | Exclui uma tarefa | `204` |

Outros códigos preservados:

- `400 Bad Request`: corpo JSON inválido;
- `404 Not Found`: o ID solicitado não existe;
- `204 No Content`: exclusão concluída, sem corpo de resposta.

## Exemplos de uso

Com o servidor em execução, os exemplos abaixo podem ser usados no PowerShell.

### Informações da API

```powershell
curl.exe http://localhost:8000/
```

Resposta:

```json
{
  "name": "Task API",
  "version": "1.0",
  "endpoints": ["/tasks"]
}
```

### Verificar a saúde

```powershell
curl.exe http://localhost:8000/health
```

Resposta:

```json
{"status": "ok"}
```

### Listar tarefas

```powershell
curl.exe http://localhost:8000/tasks
```

### Buscar uma tarefa

```powershell
curl.exe http://localhost:8000/tasks/1
```

Quando o ID não existe, a resposta mantém o formato original:

```json
{"error": "Task 99 not found"}
```

### Criar uma tarefa

```powershell
curl.exe -X POST http://localhost:8000/tasks `
  -H "Content-Type: application/json" `
  -d '{"title":"Aprender SQLite"}'
```

Resposta com status `201`:

```json
{
  "id": 4,
  "title": "Aprender SQLite",
  "done": false
}
```

### Atualizar uma tarefa

O `PUT` é parcial: envie `title`, `done` ou ambos.

```powershell
curl.exe -X PUT http://localhost:8000/tasks/4 `
  -H "Content-Type: application/json" `
  -d '{"done":true}'
```

Resposta:

```json
{
  "id": 4,
  "title": "Aprender SQLite",
  "done": true
}
```

### Excluir uma tarefa

```powershell
curl.exe -i -X DELETE http://localhost:8000/tasks/4
```

O status é `204` e a resposta não possui corpo.

Corpos inválidos em `POST` ou `PUT` retornam status `400`:

```json
{"error": "Invalid request body"}
```

## Comprovando a persistência

1. Inicie o servidor.
2. Crie uma tarefa com `POST /tasks`.
3. Confirme com `GET /tasks`.
4. Encerre o servidor com `Ctrl+C`.
5. Inicie o mesmo comando Uvicorn novamente.
6. Repita `GET /tasks`.

Se a tarefa criada ainda aparecer e os três exemplos não estiverem duplicados,
a persistência foi comprovada.

## Abrindo `tasks.db` no DB Browser for SQLite

1. Baixe e instale o **DB Browser for SQLite** pelo site oficial
   <https://sqlitebrowser.org/>.
2. Inicie a API pelo menos uma vez para gerar `tasks.db`.
3. Abra o DB Browser e clique em **Open Database**.
4. Selecione `tasks.db` na pasta do projeto.
5. Abra a aba **Browse Data**.
6. Escolha a tabela `tasks`.
7. Confirme as colunas `id`, `title` e `done`.
8. Na aba **Execute SQL**, experimente uma consulta somente de leitura:

```sql
SELECT * FROM tasks;
```

O arquivo `queries.sql` também contém consultas de estudo. As instruções
`UPDATE` e `DELETE` presentes nele alteram dados e devem ser executadas
manualmente apenas quando essa mudança for desejada. Elas não são executadas na
inicialização da API.

## Evidência visual

Depois de abrir o banco e mostrar a tabela `tasks`, faça uma captura real da
tela e salve-a como `docs/database-screenshot.png`.

![SQLite database opened in DB Browser](docs/database-screenshot.png)

A imagem não está incluída automaticamente porque deve comprovar o banco real
aberto no seu computador.

## Testes automatizados

Execute:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes verificam inicialização, seed sem duplicação, CRUD, validações,
respostas HTTP, conversão booleana, segurança das consultas e persistência.
Cada teste usa um banco temporário, portanto a suíte não altera `tasks.db`.

## Segurança e decisões de implementação

- todos os valores variáveis são enviados ao SQLite por parâmetros `?`;
- nenhum valor do usuário é concatenado em uma string SQL;
- toda escrita chama `commit()`;
- cada operação abre e fecha sua própria conexão;
- o caminho do banco é calculado a partir de `database.py`, não da pasta atual
  do terminal;
- não há credenciais ou caminhos absolutos de uma máquina no código;
- nenhuma rota consulta a antiga lista em memória.
