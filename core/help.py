import os
from config import settings

def get_file_list(dir: str):
    files = []
    for filename in os.listdir(dir):
        filepath = os.path.join(dir, filename)
        if os.path.isfile(filepath):
            # 获取文件大小
            size = os.path.getsize(filepath)
            # 格式化文件大小
            if size < 1024:
                size_formatted = f"{size} B"
            elif size < 1024 * 1024:
                size_formatted = f"{size / 1024:.1f} KB"
            else:
                size_formatted = f"{size / (1024 * 1024):.1f} MB"

            # 获取修改时间
            modified_time = os.path.getmtime(filepath)
            from datetime import datetime
            modified_time_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")

            # 确定文件类型和图标
            file_type = "其他"
            icon_class = "fa-file"

            if filename.endswith('.md'):
                file_type = "文档"
                icon_class = "fa-file-alt"
            elif filename.endswith('.py'):
                file_type = "示例扩展"
                icon_class = "fa-file-code"
            elif filename.endswith('.html'):
                file_type = "示例页面"
                icon_class = "fa-file-code"

            files.append({
                "filename": filename,
                # "filepath": filepath,
                # "size": size,
                "size_formatted": size_formatted,
                "modified_time": modified_time_str,
                "type": file_type,
                "icon_class": icon_class,
            })

        # 按修改时间排序
        files.sort(key=lambda x: x["modified_time"], reverse=True)

    return files
