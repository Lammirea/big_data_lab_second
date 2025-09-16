from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn
import os
import configparser
import json
import redis
from train import MultiModel
from predict import Predictor
import logger

app = FastAPI()

# Инициализация Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

@app.post("/train/")
async def train_model(
    model_type: str = "d_tree",
    use_config: bool = True,
    save_model: bool = True,  # Добавлен параметр для управления сохранением
    # Параметры для Logistic Regression
    solver: str = "lbfgs",
    max_iter: int = 100,
    # Параметры для Random Forest
    n_estimators: int = 100,
    criterion: str = "entropy",
    # Параметры для Decision Tree
    max_depth: int = 10,
    min_samples_split: int = 2,
    predict_flag: bool = False
):
    try:
        # Используем MultiModel из train.py
        multi_model = MultiModel()
        
        # Выбор модели в зависимости от параметра
        if model_type == "log_reg":
            result = multi_model.log_reg(
                use_config=use_config, 
                solver=solver, 
                max_iter=max_iter, 
                predict=predict_flag,
                save=save_model  # Передаем параметр сохранения
            )
        elif model_type == "rand_forest":
            result = multi_model.rand_forest(
                use_config=use_config, 
                n_estimators=n_estimators, 
                criterion=criterion, 
                predict=predict_flag,
                save=save_model  # Передаем параметр сохранения
            )
        elif model_type == "d_tree":
            result = multi_model.d_tree(
                use_config=use_config, 
                max_depth=max_depth, 
                min_samples_split=min_samples_split, 
                predict=predict_flag,
                save=save_model  # Передаем параметр сохранения
            )
        elif model_type == "gnb":
            result = multi_model.gnb(predict=predict_flag, save=save_model)
        else:
            raise HTTPException(status_code=400, detail=f"Неизвестный тип модели: {model_type}")
        
        return {
            "model_trained": result, 
            "model_type": model_type,
            "model_saved": save_model
        }
    except HTTPException:
        # Повторно пробрасываем HTTPException чтобы сохранить его статус-код (400, 422 и т.д.)
        raise
    except Exception as e:
        # Для всех остальных исключений возвращаем 500
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/")
async def predict_model(mode: str = "smoke", file: UploadFile = None):
    cache_key = f"predict:{mode}"

    # Безопасная проверка кэша — при ошибке просто считаем cache miss
    try:
        try:
            if redis_client is not None and redis_client.exists(cache_key):
                raw = redis_client.get(cache_key)
                if raw:
                    # если в кэше лежит JSON-строка — распарсим и вернём ответ
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        # если парсинг не удался — просто пропускаем кэш
                        logger.warning("Не удалось распарсить данные из Redis, игнорируем кэш")
                        parsed = None
                    if parsed is not None:
                        return {"from_cache": True, **parsed}
        except redis.exceptions.RedisError as re:
            logger.warning(f"Redis error while checking cache (treat as cache miss): {re}")
    except Exception as e:
        # Очень внешняя защита — если что-то странное, логируем и продолжаем
        logger.warning(f"Unexpected error during Redis cache check: {e}")

    try:
        predictor = Predictor()

        if mode == "upload":
            if file is None:
                raise HTTPException(status_code=400, detail="Файл не предоставлен для режима 'upload'")
            file_contents = await file.read()
            result = predictor.predict_upload(file_contents)
        elif mode == "smoke":
            result = predictor.predict_smoke()
        else:
            raise HTTPException(status_code=400, detail="Неверный режим. Используйте 'smoke' или 'upload'")

        # (Опционально) попытка записать результат в кэш — снова в try/except,
        # чтобы проблемы с Redis не ломали ответ.
        try:
            try:
                if redis_client is not None:
                    redis_client.set(cache_key, json.dumps(result))
                    # при желании можно установить ttl: redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
            except redis.exceptions.RedisError as re:
                logger.warning(f"Redis error while storing cache (ignored): {re}")
        except Exception as e:
            logger.warning(f"Unexpected error while writing to Redis cache: {e}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_dir, '..', "config.ini")
    config.read(config_path, encoding="utf-8")
    try:
        host = config["FASTAPI"]["host"]
        port = config.getint("FASTAPI", "port")
    except KeyError:
        raise ValueError("В config.ini отсутствует секция [FASTAPI] или ключи host/port")
    uvicorn.run(app, host=host, port=port)