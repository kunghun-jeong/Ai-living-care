"""
api_server.py  —  Manager API 게이트웨이 (실험 · 미승인)

역할:
    frontend/(React)가 POST하는 자연어를 받아 pipeline.run()(Neo4j 추론
    파이프라인)으로 처리하고, 결과를 frontend로 돌려주는 동시에 Worker로도
    전달한다. 이 저장소의 정본 원칙("HTTP API 없음", root CLAUDE.md·
    docs/api-spec.md)과 충돌하는 실험 코드 — 자세한 내용은 이 폴더의
    CLAUDE.md 「Neo4j 추론 파이프라인」과 ../../frontend/CLAUDE.md 참조.

실행:
    cd manager_ai_agent/manager_ai_core
    uvicorn api_server:app --reload --port 8000
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "kg_mapping"))
sys.path.append(os.path.join(os.path.dirname(__file__), "policy_generation"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "a2a_client"))

import pipeline
from graph_retrieval import GraphRetriever
from a2a_client import send_to_worker

# 로컬 개발 전용 — React 개발 서버(Vite 기본 포트) origin만 허용한다.
# 프로덕션 배포용 설정이 아니다 (이 파일 전체가 실험·미승인).
_ALLOWED_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

_retriever: GraphRetriever | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _retriever
    _retriever = GraphRetriever()
    try:
        yield
    finally:
        _retriever.close()
        _retriever = None


app = FastAPI(title="AI-Care Manager API (실험·미승인)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    text: str
    hour: int | None = None


@app.get("/api/health")
def health():
    try:
        _retriever.list_axes()
        return {"neo4j": "ok"}
    except Exception as e:
        return {"neo4j": "unreachable", "detail": str(e)}


@app.post("/api/query")
def query(req: QueryRequest):
    hour = req.hour if req.hour is not None else datetime.now().hour
    result = pipeline.run(req.text, hour, retriever=_retriever)

    for axis_result in result["results"]:
        axis_result["worker_delivery"] = send_to_worker(
            {
                "axis": axis_result["axis"],
                "evaluation": axis_result["evaluation"],
                "sequence": axis_result["sequence"],
            }
        )

    return result
