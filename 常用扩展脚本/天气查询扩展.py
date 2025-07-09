"""
天气查询扩展
功能: 通过OpenWeatherMap API查询城市天气信息
作者: System
版本: 1.0.0
依赖: requests
"""

import requests
import json
from datetime import datetime

def get_default_config():
    """返回默认配置"""
    return {
        "api_key": "",
        "base_url": "https://api.openweathermap.org/data/2.5",
        "units": "metric",
        "lang": "zh_cn"
    }

def get_config_form():
    """返回配置表单"""
    return """
    <div class="mb-3">
        <label for="config.api_key" class="form-label">OpenWeather API密钥</label>
        <input type="password" class="form-control" id="config.api_key" 
               name="config.api_key" value="{{ config.api_key }}" required>
        <div class="form-text">请在 <a href="https://openweathermap.org/api" target="_blank">OpenWeatherMap</a> 申请免费API密钥</div>
    </div>
    
    <div class="mb-3">
        <label for="config.units" class="form-label">温度单位</label>
        <select class="form-select" id="config.units" name="config.units">
            <option value="metric" {{ 'selected' if config.units == 'metric' else '' }}>摄氏度 (°C)</option>
            <option value="imperial" {{ 'selected' if config.units == 'imperial' else '' }}>华氏度 (°F)</option>
            <option value="kelvin" {{ 'selected' if config.units == 'kelvin' else '' }}>开尔文 (K)</option>
        </select>
    </div>
    
    <div class="mb-3">
        <label for="config.lang" class="form-label">语言</label>
        <select class="form-select" id="config.lang" name="config.lang">
            <option value="zh_cn" {{ 'selected' if config.lang == 'zh_cn' else '' }}>中文</option>
            <option value="en" {{ 'selected' if config.lang == 'en' else '' }}>English</option>
        </select>
    </div>
    """

def get_query_form():
    """返回查询表单"""
    return """
    <div class="mb-3">
        <label for="city" class="form-label">城市名称</label>
        <input type="text" class="form-control" id="city" name="city" 
               placeholder="例如: 北京, Beijing, New York" required>
        <div class="form-text">支持中英文城市名称</div>
    </div>
    
    <div class="mb-3">
        <label for="country" class="form-label">国家代码 (可选)</label>
        <input type="text" class="form-control" id="country" name="country" 
               placeholder="例如: CN, US" maxlength="2">
        <div class="form-text">ISO 3166国家代码，提高查询准确性</div>
    </div>
    
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" id="forecast" name="forecast">
        <label class="form-check-label" for="forecast">
            获取5天天气预报
        </label>
    </div>
    """

def validate_config(config):
    """验证配置"""
    if not config.get("api_key"):
        return False, "API密钥不能为空"
    
    if len(config.get("api_key", "")) < 10:
        return False, "API密钥格式不正确"
    
    return True, ""

def execute_query(params, config=None):
    """执行天气查询"""
    try:
        city = params.get("city", "").strip()
        country = params.get("country", "").strip()
        forecast = params.get("forecast", False)
        
        if not city:
            return {"error": "城市名称不能为空"}
        
        # 构建查询字符串
        query = city
        if country:
            query = f"{city},{country}"
        
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "")
        units = config.get("units", "metric")
        lang = config.get("lang", "zh_cn")
        
        # 当前天气查询
        current_url = f"{base_url}/weather"
        current_params = {
            "q": query,
            "appid": api_key,
            "units": units,
            "lang": lang
        }
        
        current_response = requests.get(current_url, params=current_params, timeout=10)
        
        if current_response.status_code != 200:
            error_data = current_response.json()
            return {"error": f"查询失败: {error_data.get('message', '未知错误')}"}
        
        current_data = current_response.json()
        
        # 格式化当前天气数据
        result = {
            "current_weather": {
                "city": current_data["name"],
                "country": current_data["sys"]["country"],
                "temperature": current_data["main"]["temp"],
                "feels_like": current_data["main"]["feels_like"],
                "humidity": current_data["main"]["humidity"],
                "pressure": current_data["main"]["pressure"],
                "description": current_data["weather"][0]["description"],
                "wind_speed": current_data["wind"]["speed"],
                "wind_direction": current_data["wind"].get("deg", 0),
                "visibility": current_data.get("visibility", 0) / 1000,  # 转换为公里
                "sunrise": datetime.fromtimestamp(current_data["sys"]["sunrise"]).strftime("%H:%M"),
                "sunset": datetime.fromtimestamp(current_data["sys"]["sunset"]).strftime("%H:%M"),
                "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # 如果需要预报数据
        if forecast:
            forecast_url = f"{base_url}/forecast"
            forecast_response = requests.get(forecast_url, params=current_params, timeout=10)
            
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                
                # 处理预报数据
                forecasts = []
                for item in forecast_data["list"][:40]:  # 5天，每3小时一次
                    forecasts.append({
                        "datetime": item["dt_txt"],
                        "temperature": item["main"]["temp"],
                        "description": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"]
                    })
                
                result["forecast"] = forecasts
        
        return {
            "success": True,
            "data": result,
            "query_info": {
                "city": query,
                "units": units,
                "language": lang,
                "include_forecast": forecast
            }
        }
        
    except requests.RequestException as e:
        return {"error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}
