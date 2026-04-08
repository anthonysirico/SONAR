from fastapi import APIRouter
from app.services.graph_service import get_full_graph, get_node_by_id, get_top_prominence
from app.services.prominence import compute_all_prominence
from app.services.detection import run_all_detections

router = APIRouter()

@router.get("/")
async def full_graph():
    return get_full_graph()

@router.get("/top")
async def top_nodes(limit: int = 20):
    return get_top_prominence(limit)

@router.get("/{node_id}")
async def node_detail(node_id: str):
    return get_node_by_id(node_id)

@router.post("/prominence/compute")
async def run_prominence():
    return compute_all_prominence()

@router.post("/detect")
async def run_detection():
    return run_all_detections()