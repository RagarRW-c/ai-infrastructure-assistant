from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.ai import generate_infra

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    type: str
    cloud: str


@app.post("/generate")
def generate(req: PromptRequest):

    try:

        result = generate_infra(req.prompt, req.type, req.cloud)

        return {
            "result": result
        }

    except Exception as e:

        return {
            "result": f"ERROR: {str(e)}"
        }