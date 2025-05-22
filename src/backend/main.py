from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import rag_routes, gen_routes, file_routes, web_routes, api_key_routes, conversation_routes


app = FastAPI(title="Agent System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_routes.router, prefix="/rag", tags=["RAG"])
app.include_router(file_routes.router, prefix="/files", tags=["Files"])
app.include_router(web_routes.router, prefix="/web", tags=["WebSearch"])
app.include_router(gen_routes.router, prefix="/generate", tags=["Generative Content"])
app.include_router(api_key_routes.router, prefix="/api-key", tags=["API Key"])
app.include_router(conversation_routes.router, prefix="/conversations", tags=["Conversations"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Agent System"}