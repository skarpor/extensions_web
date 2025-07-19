from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Request, Depends, Form, Body
from fastapi.staticfiles import StaticFiles
from typing import List
import asyncio
import json
import uuid
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
# 存放所有活跃的WebSocket连接
from core.logger import get_logger
from core.auth import get_current_user
router=APIRouter()
templates = Jinja2Templates(directory="static")
logger = get_logger("danmu")
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Connection removed. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                logger.info("Client disconnected during broadcast")
                self.disconnect(connection)
            except RuntimeError as e:
                logger.error(f"Runtime error: {e}")
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# WebSocket端点
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # 可以处理客户端发来的消息
            except asyncio.TimeoutError:
                # 心跳检测
                await websocket.send_text("ping")
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        manager.disconnect(websocket)

# 发送弹幕的API接口
@router.post("/send_danmu")
async def send_danmu(
    data: dict = Body(...)  # 改为接收JSON
):
    # danmu_data = {
    #     "id": str(uuid.uuid4()),
    #     "text": data.get("text", ""),
    #     "color": data.get("color", "#ffffff"),
    #     "timestamp": int(asyncio.get_event_loop().time() * 1000)
    # }
    # await manager.broadcast(json.dumps(danmu_data))
    await send_data(data)
    return {"status": "success"}

async def send_data(data):
    danmu_data = {
        "id": str(uuid.uuid4()),
        "text": data.get("text", ""),
        "color": data.get("color", "#ffffff"),
        "timestamp": int(asyncio.get_event_loop().time() * 1000)
    }
    await manager.broadcast(json.dumps(danmu_data))

@router.get("/",response_class=HTMLResponse)
def index(
        request:Request,
        # user=Depends(get_current_user)
):
    return templates.TemplateResponse(
        "danmu.html",
        {
            "request": request,
            "host": settings.HOST,
            "port": settings.PORT,
        }
    )