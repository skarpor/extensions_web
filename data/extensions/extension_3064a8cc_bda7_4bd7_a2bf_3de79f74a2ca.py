from typing import Dict

def execute_query(params: Dict[str, Dict], config: Dict[str, Dict]) -> Dict[str, Dict]:
    # file_manager = params.get("file_manager")
    filetext=""
    if params.get("files"):
        files = params["files"]
        content: bytes = files["file"]["content"]
        filetext = content.decode("utf-8")

        # for file in files.keys():
            # print(file, files[file]["content"])
            # 获取当前python文件的名称
            #with open(file, "r", encoding="utf-8") as f:
            # file_manager.save_file(filename=files[file]["filename"], file_content=files[file]["content"])


    return {"data":filetext}

def get_query_form() -> str:
    return """
<div class="mb-3">
                <label for="analysis_type" class="form-label">分析类型</label>
                <select class="form-select" id="analysis_type" name="analysis_type">
                    <option value="basic">基本信息分析</option>
                    <option value="content">内容分析</option>
                    <option value="security">安全检查</option>
                    <option value="full">完整分析</option>
                </select>
            </div>
             <div class="mb-3">
                <label for="file" class="form-label">选择文件</label>
                <input type="file" class="form-control"  name="file" required id="file">
                <div class="form-text">选择要上传和分析的文件</div>
            </div>
    """

