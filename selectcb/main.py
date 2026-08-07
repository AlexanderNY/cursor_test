from fastapi import FastAPI

app = FastAPI(
    title="SelectCB Service",
    description="Микросервис SelectCB",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "SelectCB Service API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "service": "selectcb",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
    )
