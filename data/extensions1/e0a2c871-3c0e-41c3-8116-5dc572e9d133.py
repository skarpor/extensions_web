"""
CSV数据分析扩展
功能: 上传CSV文件并进行数据分析
作者: System
版本: 1.0.0
依赖: 无 (使用Python标准库)
"""

import csv
import io
import json
from collections import Counter
from datetime import datetime

def get_query_form():
    """返回查询表单"""
    return """
    <div class="mb-3">
        <label for="csv_file" class="form-label">CSV文件</label>
        <input type="file" class="form-control" id="csv_file" name="csv_file" 
               accept=".csv" required>
        <div class="form-text">请上传CSV格式的数据文件</div>
    </div>
    
    <div class="mb-3">
        <label for="encoding" class="form-label">文件编码</label>
        <select class="form-select" id="encoding" name="encoding">
            <option value="utf-8">UTF-8</option>
            <option value="gbk">GBK</option>
            <option value="gb2312">GB2312</option>
            <option value="utf-8-sig">UTF-8 with BOM</option>
        </select>
    </div>
    
    <div class="mb-3">
        <label for="delimiter" class="form-label">分隔符</label>
        <select class="form-select" id="delimiter" name="delimiter">
            <option value=",">逗号 (,)</option>
            <option value=";">分号 (;)</option>
            <option value="\t">制表符 (Tab)</option>
            <option value="|">竖线 (|)</option>
        </select>
    </div>
    
    <div class="mb-3">
        <label for="analysis_type" class="form-label">分析类型</label>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="basic_stats" name="analysis_type" value="basic" checked>
            <label class="form-check-label" for="basic_stats">基础统计</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="column_analysis" name="analysis_type" value="columns">
            <label class="form-check-label" for="column_analysis">列分析</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="data_quality" name="analysis_type" value="quality">
            <label class="form-check-label" for="data_quality">数据质量检查</label>
        </div>
    </div>
    
    <div class="mb-3">
        <label for="target_column" class="form-label">目标分析列 (可选)</label>
        <input type="text" class="form-control" id="target_column" name="target_column" 
               placeholder="指定要详细分析的列名">
    </div>
    """

def analyze_column_type(values):
    """分析列的数据类型"""
    non_empty_values = [v for v in values if v and str(v).strip()]
    if not non_empty_values:
        return "empty"
    
    # 检查是否为数字
    numeric_count = 0
    date_count = 0
    
    for value in non_empty_values[:100]:  # 只检查前100个值
        str_value = str(value).strip()
        
        # 检查数字
        try:
            float(str_value)
            numeric_count += 1
            continue
        except ValueError:
            pass
        
        # 检查日期
        for date_format in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                datetime.strptime(str_value, date_format)
                date_count += 1
                break
            except ValueError:
                continue
    
    total_checked = min(100, len(non_empty_values))
    
    if numeric_count / total_checked > 0.8:
        return "numeric"
    elif date_count / total_checked > 0.8:
        return "date"
    else:
        return "text"

def execute_query(params, config=None):
    """执行CSV分析"""
    try:
        files = params.get("files", {})
        if "csv_file" not in files:
            return {"error": "请上传CSV文件"}
        
        file_info = files["csv_file"]
        file_content = file_info["content"]
        filename = file_info["filename"]
        
        # 获取参数
        encoding = params.get("encoding", "utf-8")
        delimiter = params.get("delimiter", ",")
        analysis_types = params.getlist("analysis_type") if hasattr(params, 'getlist') else [params.get("analysis_type", "basic")]
        target_column = params.get("target_column", "").strip()
        
        # 处理制表符
        if delimiter == "\\t":
            delimiter = "\t"
        
        # 解码文件内容
        try:
            text_content = file_content.decode(encoding)
        except UnicodeDecodeError:
            # 尝试其他编码
            for fallback_encoding in ['utf-8', 'gbk', 'latin-1']:
                try:
                    text_content = file_content.decode(fallback_encoding)
                    encoding = fallback_encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return {"error": "无法解码文件，请检查文件编码"}
        
        # 解析CSV
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        
        try:
            data = list(csv_reader)
        except csv.Error as e:
            return {"error": f"CSV解析失败: {str(e)}"}
        
        if not data:
            return {"error": "CSV文件为空或格式错误"}
        
        result = {
            "file_info": {
                "filename": filename,
                "encoding": encoding,
                "delimiter": delimiter,
                "total_rows": len(data),
                "total_columns": len(data[0].keys()) if data else 0
            },
            "columns": list(data[0].keys()) if data else []
        }
        
        # 基础统计
        if "basic" in analysis_types:
            result["basic_statistics"] = {
                "row_count": len(data),
                "column_count": len(data[0].keys()) if data else 0,
                "file_size_bytes": len(file_content),
                "sample_data": data[:5]  # 前5行数据
            }
        
        # 列分析
        if "columns" in analysis_types:
            column_analysis = {}
            
            for column in data[0].keys():
                values = [row[column] for row in data]
                non_empty_values = [v for v in values if v and str(v).strip()]
                
                column_stats = {
                    "total_count": len(values),
                    "non_empty_count": len(non_empty_values),
                    "empty_count": len(values) - len(non_empty_values),
                    "unique_count": len(set(non_empty_values)),
                    "data_type": analyze_column_type(values)
                }
                
                # 最常见的值
                if non_empty_values:
                    value_counts = Counter(non_empty_values)
                    column_stats["most_common"] = value_counts.most_common(10)
                    
                    # 如果是数字类型，计算统计值
                    if column_stats["data_type"] == "numeric":
                        try:
                            numeric_values = [float(v) for v in non_empty_values if v]
                            if numeric_values:
                                column_stats["numeric_stats"] = {
                                    "min": min(numeric_values),
                                    "max": max(numeric_values),
                                    "mean": sum(numeric_values) / len(numeric_values),
                                    "median": sorted(numeric_values)[len(numeric_values) // 2]
                                }
                        except (ValueError, TypeError):
                            pass
                
                column_analysis[column] = column_stats
            
            result["column_analysis"] = column_analysis
        
        # 数据质量检查
        if "quality" in analysis_types:
            quality_issues = []
            
            for column in data[0].keys():
                values = [row[column] for row in data]
                empty_count = sum(1 for v in values if not v or not str(v).strip())
                empty_rate = empty_count / len(values)
                
                if empty_rate > 0.5:
                    quality_issues.append({
                        "type": "high_missing_rate",
                        "column": column,
                        "missing_rate": empty_rate,
                        "description": f"列 '{column}' 缺失率过高 ({empty_rate:.1%})"
                    })
                
                # 检查重复值
                non_empty_values = [v for v in values if v and str(v).strip()]
                if len(non_empty_values) > 0:
                    unique_rate = len(set(non_empty_values)) / len(non_empty_values)
                    if unique_rate < 0.1:
                        quality_issues.append({
                            "type": "low_diversity",
                            "column": column,
                            "unique_rate": unique_rate,
                            "description": f"列 '{column}' 数据多样性较低 ({unique_rate:.1%})"
                        })
            
            result["quality_check"] = {
                "issues": quality_issues,
                "overall_quality": "good" if len(quality_issues) == 0 else "needs_attention"
            }
        
        # 目标列详细分析
        if target_column and target_column in data[0].keys():
            target_values = [row[target_column] for row in data]
            target_analysis = {
                "column_name": target_column,
                "value_distribution": dict(Counter(target_values).most_common(20)),
                "data_type": analyze_column_type(target_values)
            }
            
            # 如果是数字类型，生成分布统计
            if target_analysis["data_type"] == "numeric":
                try:
                    numeric_values = [float(v) for v in target_values if v and str(v).strip()]
                    if numeric_values:
                        # 创建直方图数据
                        min_val, max_val = min(numeric_values), max(numeric_values)
                        bin_count = min(20, len(set(numeric_values)))
                        bin_width = (max_val - min_val) / bin_count if bin_count > 1 else 1
                        
                        histogram = {}
                        for value in numeric_values:
                            bin_index = int((value - min_val) / bin_width) if bin_width > 0 else 0
                            bin_index = min(bin_index, bin_count - 1)
                            bin_range = f"{min_val + bin_index * bin_width:.2f}-{min_val + (bin_index + 1) * bin_width:.2f}"
                            histogram[bin_range] = histogram.get(bin_range, 0) + 1
                        
                        target_analysis["histogram"] = histogram
                except (ValueError, TypeError):
                    pass
            
            result["target_analysis"] = target_analysis
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {"error": f"CSV分析失败: {str(e)}"}
