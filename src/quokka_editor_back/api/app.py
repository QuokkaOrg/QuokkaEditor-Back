from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Sit to mój fan"}
