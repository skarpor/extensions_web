import asyncio
import base64
import json
import os
import uuid
import zlib
import re
from io import BytesIO
from typing import AsyncGenerator, Dict, Tuple

from fastapi.templating import Jinja2Templates
import qrcode
from fastapi import UploadFile, Request, APIRouter, File
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, FileResponse

from app.core.logger import get_logger

router = APIRouter(prefix="/trans")
templates = Jinja2Templates(directory="templates")  

# 允许跨域
# 配置日志

# 二维码生成配置
QR_CHUNK_SIZE = 200  # 降低每个二维码的数据量
QR_VERSION = 10      # 降低版本，使二维码更容易识别
QR_BOX_SIZE = 4      # 降低像素大小
QR_BORDER = 4        # 保持标准边框

# 存储目录
UPLOAD_DIR = "uploads"
COMPRESSED_DIR = "compressed"
for dir_path in [UPLOAD_DIR, COMPRESSED_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# 存储会话信息
sessions: Dict[str, dict] = {}

logger = get_logger("trans_files")

def optimize_binary_data(data: bytes) -> str:
    """优化二进制数据的存储方式"""
    # 将二进制转换为hex字符串
    hex_str = data.hex()
    
    # 查找重复模式
    result = []
    i = 0
    while i < len(hex_str):
        # 查找连续重复的单字符
        if i + 1 < len(hex_str):
            char = hex_str[i]
            count = 1
            while i + count < len(hex_str) and hex_str[i + count] == char:
                count += 1
            if count > 3:  # 如果重复次数大于3，使用压缩格式
                result.append(f"{char}*{count}")
                i += count
                continue
        
        # 查找重复的双字符模式
        if i + 3 < len(hex_str):
            pattern = hex_str[i:i+2]
            count = 1
            while i + (count+1)*2 <= len(hex_str) and hex_str[i+count*2:i+(count+1)*2] == pattern:
                count += 1
            if count > 2:  # 如果重复次数大于2，使用压缩格式
                result.append(f"({pattern})*{count}")
                i += count * 2
                continue
        
        # 如果没有找到重复模式，直接添加字符
        result.append(hex_str[i])
        i += 1
    
    return ",".join(result)

def compress_file(content: bytes) -> Tuple[bytes, dict]:
    """压缩文件内容，返回压缩后的数据和元信息"""
    # 尝试不同的压缩级别，选择最佳压缩比
    best_compressed = content
    best_ratio = 1
    best_level = 0
    
    for level in range(-1, 10):  # zlib压缩级别从-1到9
        try:
            compressed = zlib.compress(content, level)
            ratio = len(compressed) / len(content)
            if ratio < best_ratio:
                best_compressed = compressed
                best_ratio = ratio
                best_level = level
        except Exception as e:
            logger.error(f"Compression error at level {level}: {e}")
    
    metadata = {
        "original_size": len(content),
        "compressed_size": len(best_compressed),
        "compression_ratio": best_ratio,
        "compression_level": best_level
    }
    
    return best_compressed, metadata

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页，提供上传文件的表单"""
    return templates.TemplateResponse("trans/index.html", {"request": request})

@router.post("/upload")
async def upload_file(file: UploadFile):
    """处理文件上传"""
    try:
        session_id = str(uuid.uuid4())
        
        # 读取并压缩文件
        content = await file.read()
        compressed_data, metadata = compress_file(content)
        
        # 保存压缩后的文件
        compressed_path = os.path.join(COMPRESSED_DIR, f"{session_id}_{file.filename}.gz")
        with open(compressed_path, "wb") as f:
            f.write(compressed_data)
        
        # 存储会话信息
        sessions[session_id] = {
            "file_path": compressed_path,
            "original_name": file.filename,
            "metadata": metadata
        }
        
        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "metadata": metadata,
            "message": "File uploaded and compressed successfully"
        })
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

async def generate_qr_chunks(file_path: str, metadata: dict) -> AsyncGenerator[tuple[bytes, int, dict], None]:
    """生成文件内容的二维码分块"""
    with open(file_path, "rb") as f:
        compressed_data = f.read()
    
    # 第一个二维码包含文件信息
    file_info = {
        "type": "file_info",
        "original_name": os.path.basename(file_path).split('_', 1)[1].replace('.gz', ''),
        "total_size": len(compressed_data),
        "metadata": metadata
    }
    
    # 生成文件信息二维码
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(json.dumps(file_info))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    total_chunks = (len(compressed_data) + QR_CHUNK_SIZE - 1) // QR_CHUNK_SIZE + 1  # +1 for file info
    yield img_byte_arr.getvalue(), total_chunks, file_info

    # 生成数据块二维码
    chunk_index = 0
    for i in range(0, len(compressed_data), QR_CHUNK_SIZE):
        chunk = compressed_data[i:i+QR_CHUNK_SIZE]
        optimized_data = optimize_binary_data(chunk)
        
        qr = qrcode.QRCode(
            version=QR_VERSION,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=QR_BOX_SIZE,
            border=QR_BORDER,
        )
        
        # 添加数据到二维码 (包含索引和优化后的数据)
        data = f"{chunk_index}:{optimized_data}"
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        yield img_byte_arr.getvalue(), total_chunks, {"type": "data", "index": chunk_index}
        chunk_index += 1
        
        await asyncio.sleep(0.1)  # 控制生成速度

async def qr_stream_generator(request: Request, session_info: dict):
    """生成二维码的SSE流"""
    try:
        async for qr_bytes, total_chunks, chunk_info in generate_qr_chunks(
            session_info["file_path"], 
            session_info["metadata"]
        ):
            if await request.is_disconnected():
                logger.info("Client disconnected")
                break

            qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
            message = {
                "type": "qr",
                "image": qr_base64,
                "total_chunks": total_chunks,
                "chunk_info": chunk_info
            }
            yield f"data: {json.dumps(message)}\n\n"

        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    except Exception as e:
        logger.error(f"Error generating QR codes: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@router.get("/stream-qr/{session_id}")
async def stream_qr(request: Request, session_id: str):
    """处理SSE流请求"""
    if session_id not in sessions:
        return JSONResponse({
            "status": "error",
            "message": "Invalid session ID"
        }, status_code=404)

    session_info = sessions[session_id]
    if not os.path.exists(session_info["file_path"]):
        return JSONResponse({
            "status": "error",
            "message": "File not found"
        }, status_code=404)

    return StreamingResponse(
        qr_stream_generator(request, session_info),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# 新增解析相关的路由
@router.post("/parse-video")
async def parse_video(file: UploadFile = File(...)):
    """解析视频中的二维码"""
    # TODO: 实现视频解析功能
    pass

@router.post("/parse-text")
async def parse_text(text: str):
    """解析文本内容还原为文件"""
    try:
        # 解析文本内容
        lines = text.strip().split('\n')
        if not lines:
            raise ValueError("Empty text content")

        # 解析文件信息（第一行）
        file_info = json.loads(lines[0])
        if file_info["type"] != "file_info":
            raise ValueError("Invalid file info")

        # 初始化解压缩数据
        compressed_data = bytearray()

        # 解析数据块
        for line in lines[1:]:
            if not line.strip():
                continue
            index, data = line.split(':', 1)
            # 解析优化的数据格式
            decoded_data = decode_optimized_data(data)
            compressed_data.extend(decoded_data)

        # 解压数据
        original_data = zlib.decompress(compressed_data)

        # 保存并返回文件
        output_path = os.path.join(UPLOAD_DIR, file_info["original_name"])
        with open(output_path, "wb") as f:
            f.write(original_data)

        return FileResponse(
            output_path,
            filename=file_info["original_name"],
            media_type="application/octet-stream"
        )

    except Exception as e:
        logger.error(f"Parse error: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

def decode_optimized_data(data: str) -> bytes:
    """解码优化后的数据格式"""
    result = []
    parts = data.split(',')
    
    for part in parts:
        if '*' in part:
            if part.startswith('('):
                # 处理(ab)*n格式
                pattern = part[1:].split(')*')
                hex_str = pattern[0]
                count = int(pattern[1])
                result.extend([hex_str] * count)
            else:
                # 处理a*n格式
                char, count = part.split('*')
                result.extend([char] * int(count))
        else:
            result.append(part)
    
    return bytes.fromhex(''.join(result))

@router.on_event("shutdown")
async def cleanup():
    """清理上传的文件"""
    for session_info in sessions.values():
        try:
            file_path = session_info["file_path"]
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

