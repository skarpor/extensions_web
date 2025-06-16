"""
应用程序入口文件
"""

import uvicorn
from new_app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "new_app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        workers=1
    )