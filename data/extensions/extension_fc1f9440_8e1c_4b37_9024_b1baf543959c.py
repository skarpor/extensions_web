from typing import Dict
def execute_query(params: Dict[str, Dict], config: Dict[str, Dict]) -> Dict[str, Dict]:
    return {"data":params.get("query", {}).get("analysis_type")}

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
    """