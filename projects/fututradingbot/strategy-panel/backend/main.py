from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import uvicorn

from models import (
    StrategyConfig, ConfigResponse, StrategyType,
    TQQQStrategy, TrendStrategy, ZScoreStrategy,
    BreakoutStrategy, MomentumStrategy, FlexibleArbitrageStrategy,
    MTFSettings, RiskControl
)
from config import config_manager

app = FastAPI(
    title="FutuTradingBot Strategy Config API",
    description="策略參數調整面板API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FutuTradingBot Strategy Config API", "version": "1.0.0"}

@app.get("/api/config")
async def get_config():
    """獲取當前配置"""
    return config_manager.get_config()

@app.post("/api/config", response_model=ConfigResponse)
async def update_config(config: StrategyConfig):
    """更新配置"""
    try:
        config_dict = config.model_dump()
        
        # 驗證權重
        mtf = config_dict.get("mtf", {})
        total_weight = mtf.get("monthly_weight", 0) + mtf.get("weekly_weight", 0) + mtf.get("daily_weight", 0)
        if total_weight != 100:
            return ConfigResponse(
                success=False,
                message="配置更新失敗",
                errors=[f"時間框架權重總和必須為100，當前為{total_weight}"]
            )
        
        config_manager.update_config(config_dict)
        return ConfigResponse(
            success=True,
            message="配置更新成功",
            config=config
        )
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return ConfigResponse(
            success=False,
            message="配置驗證失敗",
            errors=errors
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            message=f"配置更新失敗: {str(e)}"
        )

@app.post("/api/config/reset")
async def reset_config():
    """重置為默認配置"""
    config = config_manager.reset_config()
    return ConfigResponse(
        success=True,
        message="配置已重置為默認值",
        config=StrategyConfig(**config)
    )

@app.post("/api/config/save/{filename}")
async def save_config(filename: str):
    """保存配置到文件"""
    success = config_manager.save_to_file(filename)
    if success:
        return {"success": True, "message": f"配置已保存為 {filename}"}
    raise HTTPException(status_code=500, detail="保存配置失敗")

@app.post("/api/config/load/{filename}")
async def load_config(filename: str):
    """從文件加載配置"""
    config = config_manager.load_from_file(filename)
    if config:
        return ConfigResponse(
            success=True,
            message=f"配置 {filename} 已加載",
            config=StrategyConfig(**config)
        )
    raise HTTPException(status_code=404, detail="配置文件不存在")

@app.get("/api/config/list")
async def list_configs():
    """列出所有保存的配置"""
    configs = config_manager.list_saved_configs()
    return {"configs": configs}

@app.post("/api/config/export")
async def export_config():
    """導出配置為JSON字符串"""
    json_str = config_manager.export_config()
    return {"success": True, "config_json": json_str}

@app.post("/api/config/import")
async def import_config(config_json: str):
    """從JSON字符串導入配置"""
    success = config_manager.import_config(config_json)
    if success:
        return ConfigResponse(
            success=True,
            message="配置導入成功",
            config=StrategyConfig(**config_manager.get_config())
        )
    raise HTTPException(status_code=400, detail="導入配置失敗，請檢查JSON格式")

@app.post("/api/config/apply")
async def apply_config():
    """應用當前配置到交易系統"""
    # 這裡可以添加與實際交易系統的集成
    config = config_manager.get_config()
    return {
        "success": True,
        "message": "配置已應用到交易系統",
        "applied_config": config
    }

@app.get("/api/strategies")
async def get_strategies():
    """獲取所有可用的策略類型"""
    return {
        "strategies": [
            {"id": "tqqq", "name": "TQQQ策略", "description": "基於Z-Score和RSI的均值回歸策略"},
            {"id": "trend", "name": "Trend策略", "description": "基於EMA和指標共振的趨勢跟踪策略"},
            {"id": "zscore", "name": "ZScore策略", "description": "純Z-Score均值回歸策略"},
            {"id": "breakout", "name": "Breakout策略", "description": "突破交易策略"},
            {"id": "momentum", "name": "Momentum策略", "description": "動量交易策略"},
            {"id": "flexible_arbitrage", "name": "FlexibleArbitrage策略", "description": "靈活套利策略"}
        ]
    }

@app.get("/api/validate")
async def validate_config():
    """驗證當前配置"""
    valid, message = config_manager.validate_weights()
    return {"valid": valid, "message": message}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
