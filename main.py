from fastapi import FastAPI

app = FastAPI()
__VERSION__ = "0.1.0"

@app.get("/")
async def root():
    return {"status": "ok", "server": "AmiaBlog", "version": __VERSION__}
