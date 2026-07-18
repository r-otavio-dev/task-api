from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def inicio():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def verificar_saude():
    return {"status": "ok"}
