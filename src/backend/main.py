from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from routes import rag_routes, gen_routes, file_routes, web_routes, api_route


app = FastAPI(title="Agent System")

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from the frontend (default Vite port)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(rag_routes.router, prefix="/rag", tags=["RAG"])
app.include_router(file_routes.router, prefix="/files", tags=["Files"])
app.include_router(web_routes.router, prefix="/web", tags=["WebSearch"])
app.include_router(gen_routes.router, prefix="/generate", tags=["Generative Content"])
app.include_router(api_route.router, prefix="/api", tags=["API"])
@app.get("/")
def read_root():
    return {"message": "Welcome to Agent System"}