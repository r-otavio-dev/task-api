# Guia de estudo: Task API do zero ao SQLite e GitHub

Este guia explica, em linguagem de primeira aula, como a Task API foi
inspecionada, conectada ao banco, testada e versionada.

## 1. O que foi construído

O projeto é uma API de tarefas. Uma API recebe requisições e devolve respostas.
Cada tarefa possui esta estrutura:

```json
{
  "id": 1,
  "title": "Estudar Python",
  "done": false
}
```

As quatro operações principais formam o CRUD:

- **Create:** criar dados com `POST`.
- **Read:** consultar dados com `GET`.
- **Update:** atualizar dados com `PUT`.
- **Delete:** excluir dados com `DELETE`.

Os dados deste projeto ficam no arquivo SQLite `tasks.db`. Por isso, as tarefas
continuam existindo depois que o servidor é encerrado e iniciado novamente.
O GitHub armazena o código; o arquivo local do banco é ignorado pelo Git.

## 2. Entrando no projeto pelo terminal

Abra o PowerShell na pasta em que você clonou ou salvou o projeto. Um caminho
genérico seria:

```text
caminho\para\task-api
```

No PowerShell, use `cd` para entrar nela:

```powershell
cd caminho\para\task-api
```

`cd` significa *change directory*, ou mudar de diretório.

Os principais itens encontrados inicialmente foram:

```text
.git/
.venv/
__pycache__/
database.py
main.py
queries.sql
test_database.py
test_main.py
```

- `.git` guarda o histórico e as branches do Git.
- `.venv` é o ambiente virtual do Python.
- `__pycache__` contém arquivos compilados automaticamente.
- `main.py` contém as rotas e validações HTTP.
- `database.py` contém a conexão e as operações SQLite.
- `queries.sql` reúne consultas manuais para estudo.
- os arquivos `test_*.py` contêm os testes automatizados.

## 3. Inspecionando o Git antes de alterar arquivos

O histórico resumido foi consultado com:

```powershell
git log --oneline
```

O projeto já possuía este commit:

```text
f2a02be Stage 1: root and health endpoints
```

O estado foi consultado com:

```powershell
git status --short --branch
```

Inicialmente, `main.py` e um arquivo `.pyc` estavam modificados. Essa inspeção
foi importante para preservar o trabalho existente.

## 4. O que é uma branch

Foi criada uma linha separada de desenvolvimento:

```powershell
git switch -c agent/task-api-crud
```

Uma branch permite desenvolver sem apagar o estado da branch anterior. A
`master` permaneceu no Stage 1, enquanto o CRUD foi desenvolvido em
`agent/task-api-crud`.

## 5. Ambiente virtual do Python

O projeto usa o Python localizado em:

```text
.\.venv\Scripts\python.exe
```

Um ambiente virtual mantém as bibliotecas deste projeto separadas das
bibliotecas de outros projetos.

Para conferir a versão:

```powershell
.\.venv\Scripts\python.exe --version
```

Versão usada durante o desenvolvimento:

```text
Python 3.14.4
```

## 6. O erro de importação original

O arquivo tentava executar:

```python
from typing import StrictBool, StrictStr
```

Esses tipos não pertencem a `typing`. Eles pertencem ao Pydantic. A importação
correta é:

```python
from pydantic import StrictBool, StrictStr
```

Antes da correção, importar a aplicação causava:

```text
ImportError: cannot import name 'StrictBool' from 'typing'
```

## 7. Configuração do FastAPI

O objeto principal da aplicação é criado assim:

```python
app = FastAPI(
    title="Task API",
    version="1.0",
    description="API CRUD para gerenciamento de tarefas com SQLite.",
    lifespan=lifespan,
)
```

O FastAPI utiliza essas informações para gerar automaticamente a documentação
Swagger. O `lifespan` executa a inicialização do banco quando a aplicação
começa.

## 8. Modelos com Pydantic

O modelo de saída de uma tarefa é:

```python
class Task(BaseModel):
    id: int
    title: str
    done: bool
```

Isso estabelece que `id` é inteiro, `title` é texto e `done` é booleano.

### Modelo de criação

```python
class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr
```

`StrictStr` aceita somente texto verdadeiro. Um número como `123` não é
convertido silenciosamente em texto.

`extra="forbid"` rejeita campos que não fazem parte do modelo.

O título é limpo e validado:

```python
@field_validator("title")
@classmethod
def validar_titulo(cls, value: str) -> str:
    title = value.strip()
    if not title:
        raise ValueError("Title cannot be empty")
    return title
```

`strip()` remove espaços do começo e do final. Um título contendo somente
espaços torna-se vazio e é recusado.

### Modelo de atualização

```python
class TaskUpdate(BaseModel):
    title: StrictStr | None = None
    done: StrictBool | None = None
```

O caractere `|` pode ser lido como “ou”. `StrictBool` aceita somente os valores
JSON `true` e `false`; textos como `"true"`, números e `null` são recusados.

O modelo também verifica se pelo menos um campo foi enviado.

## 9. Armazenamento com SQLite

SQLite é um banco relacional salvo em um arquivo. Ele não precisa de outro
servidor: o próprio Python abre `tasks.db`, executa SQL e fecha a conexão.

O caminho é calculado a partir do arquivo do projeto:

```python
PROJECT_DIRECTORY = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIRECTORY / "tasks.db"
```

Isso funciona mesmo se o comando Uvicorn for iniciado por outra pasta.

A tabela é criada com:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0
);
```

- `INTEGER PRIMARY KEY AUTOINCREMENT` gera um ID novo;
- `TEXT NOT NULL` exige um título;
- `BOOLEAN NOT NULL DEFAULT 0` começa como não concluída;
- `IF NOT EXISTS` evita recriar uma tabela já existente.

Depois de criar a tabela, a inicialização executa `SELECT COUNT(*)`. As três
tarefas de exemplo são inseridas somente quando o resultado é zero. Executar a
inicialização outra vez não duplica dados.

Cada operação usa este formato:

```python
with get_db_connection() as connection:
    row = connection.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
```

O `?` é um parâmetro. O valor não é colado dentro da instrução SQL, o que evita
injeção SQL. O bloco `with` garante o fechamento da conexão.

Nas operações de escrita, `commit()` confirma a mudança no arquivo. Sem ele, um
`INSERT`, `UPDATE` ou `DELETE` poderia ser perdido ao fechar a conexão.

SQLite representa booleanos como `0` e `1`. `row_to_task()` converte esses
valores em `False` e `True`, que aparecem como `false` e `true` no JSON.

## 10. Convertendo validações para HTTP 400

O FastAPI normalmente responde com `422` para dados inválidos. O projeto exige
`400`, então foi registrado este manipulador:

```python
@app.exception_handler(RequestValidationError)
def validation_exception_handler(_request, _exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"},
    )
```

HTTP `400` informa que a requisição enviada pelo cliente é inválida.

## 11. Endpoints implementados

### `GET /`

Retorna nome, versão e rota principal da API.

### `GET /health`

Retorna:

```json
{"status": "ok"}
```

Essa rota confirma que o servidor está respondendo.

### `GET /tasks`

Executa um `SELECT` e retorna todas as tarefas armazenadas no banco.

### `GET /tasks/{task_id}`

O valor entre chaves é um parâmetro da URL. Em `/tasks/2`, o `task_id` vale 2.
Se a tarefa não existe, a API devolve `404` e uma mensagem no campo `error`.

### `POST /tasks`

Recebe:

```json
{"title": "Buy milk"}
```

O SQLite gera o ID automaticamente. `lastrowid` informa o ID criado, `done`
começa como `false`, `commit()` persiste a linha e a resposta usa HTTP `201`.

### `PUT /tasks/{task_id}`

Pode atualizar somente um campo:

```json
{"done": true}
```

ou os dois:

```json
{
  "title": "Estudar FastAPI",
  "done": true
}
```

O código usa `model_dump(exclude_unset=True)` para incluir somente os campos
realmente enviados. Toda a validação ocorre antes da alteração, evitando uma
atualização parcial causada por um corpo inválido. Depois, o código executa um
`UPDATE` parametrizado e confirma a operação com `commit()`.

### `DELETE /tasks/{task_id}`

Executa um `DELETE` parametrizado e retorna HTTP `204`, que significa sucesso
sem corpo de resposta.

## 12. Swagger

Com o servidor em execução, a documentação interativa fica em:

<http://localhost:8000/docs>

Para experimentar uma rota:

1. abra o endpoint;
2. clique em **Try it out**;
3. preencha os dados;
4. clique em **Execute**;
5. observe o status e o JSON de resposta.

## 13. Dependências

O arquivo `requirements.txt` registra as versões usadas:

```text
fastapi==0.139.2
httpx2==2.7.0
pydantic==2.13.4
pytest==9.1.1
uvicorn==0.51.0
```

Para instalar essas dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`-m pip` executa o instalador `pip` usando o Python da `.venv`. `-r` pede que o
pip leia a lista de um arquivo.

## 14. Testes automatizados

Os testes HTTP usam:

```python
with TestClient(app) as client:
    response = client.get("/health")
```

O `TestClient` simula requisições HTTP sem precisar abrir uma porta de rede.

Um teste básico é:

```python
def test_health_retorna_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

`assert` declara uma condição que precisa ser verdadeira.

Antes de cada teste, uma fixture aponta `DATABASE_PATH` para um arquivo
temporário. Assim, um teste que exclui uma tarefa não interfere no próximo
teste e nunca altera o `tasks.db` real do usuário.

Os testes também fecham e abrem novas conexões e reiniciam o `TestClient` para
comprovar a persistência e a ausência de seed duplicado.

Para executar a suíte:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

`-q` produz uma saída compacta. A validação desta versão cobre inicialização,
CRUD, erros, conversão booleana, SQL parametrizado e persistência.

## 15. `.gitignore` e arquivos gerados

O `.gitignore` contém:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
tasks.db
*.db-journal
venv/
```

Esses arquivos não devem ser versionados porque são ambientes locais, caches,
arquivos compilados, dados gerados ou possíveis configurações sensíveis.

Como um `.pyc` já estava rastreado, ele foi removido somente do índice:

```powershell
git rm --cached __pycache__/main.cpython-314.pyc
```

`--cached` preserva o arquivo no computador e interrompe apenas o rastreamento
do Git.

## 16. Iniciando e consultando o servidor

Para iniciar:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app
```

`main:app` significa “abra `main.py` e encontre o objeto `app`”. O servidor fica
em `http://localhost:8000`. Use `Ctrl+C` para encerrá-lo quando ele estiver
rodando diretamente no terminal.

Para consultar a saúde da aplicação:

```powershell
curl.exe -i http://localhost:8000/health
```

`curl` realiza requisições HTTP e `-i` mostra também os cabeçalhos da resposta.

## 17. README e documentação

O `README.md` é a página principal exibida pelo GitHub. Ele registra descrição,
instalação, rotas, exemplos JSON, comando do servidor, Swagger, schema SQLite,
persistência, DB Browser e execução dos testes.

## 18. Commits

Antes de cada commit foram executados os testes, revisado o `git diff` e
conferidos os arquivos preparados.

Comandos importantes:

```powershell
git diff
git add nome-do-arquivo
git commit -m "Mensagem do commit"
```

`git add` coloca um arquivo na área de preparação. `git commit` cria uma
fotografia permanente desse estágio.

Os seis commits originais do exercício são:

```text
609f26b Stage 6: document setup and API
8130757 Stage 5: add automated API tests
ed05ad9 Stage 4: pin compatible dependencies
2b27235 Stage 3: ignore generated Python files
7a20f45 Stage 2: full CRUD with strict validation
f2a02be Stage 1: root and health endpoints
```

Os seis commits da conexão com SQLite são:

```text
Stage 0: create SQLite database
Stage 1: database read endpoints
Stage 2: insert into database
Stage 3: update and delete with SQL
Stage 4: explored SQLite
Stage 5: database documentation
```

## 19. GitHub

O repositório público está em:

<https://github.com/r-otavio-dev/task-api>

O remote chamado `origin` aponta para esse endereço. Um remote é um apelido para
outro repositório.

O comando `git push` envia commits locais para o GitHub. Publicar no GitHub não
hospeda a API: o GitHub guarda o código, enquanto `localhost:8000` só funciona
quando o servidor está rodando no computador.

## 20. Roteiro seguro para praticar

Entre no projeto:

```powershell
cd caminho\para\task-api
```

Crie uma branch de estudo:

```powershell
git switch -c estudo/minha-pratica
```

Veja o estado e o histórico:

```powershell
git status
git log --oneline
```

Execute os testes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

O ciclo profissional básico aplicado neste projeto foi:

```text
entender → alterar → testar → revisar → commitar
```
