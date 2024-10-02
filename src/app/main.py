import mlflow
import logging
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import boto3 
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class WineFeatures(BaseModel):
    alcohol: float
    malic_acid: float
    ash: float
    alcalinity_of_ash: float
    magnesium: float
    total_phenols: float
    flavanoids: float
    nonflavanoid_phenols: float
    proanthocyanins: float
    hue: float
    od280_od315_of_diluted_wines: float
    proline: float

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('MLFLOW_S3_ENDPOINT_URL'),  
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def upload_to_minio(bucket_name, object_name, data):
    try:
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name_with_timestamp = f"{object_name}_{current_time}"
        
        s3_client.put_object(Bucket=bucket_name, Key=object_name_with_timestamp, Body=data)
        logger.info(f"Dados enviados ao MinIO: {object_name_with_timestamp}")
    except Exception as e:
        logger.error(f"Erro ao enviar dados ao MinIO: {str(e)}")
        raise

@app.get("/api/validate_model")
async def validate_model():
    run_id = 's3://mlflow/3/68485ba5b3d54280868ca5ebf740a219/artifacts/extra_trees_model'
    try:
        model = mlflow.sklearn.load_model(run_id)
        logger.info("Modelo validado: %s", run_id)
        return {"status": "Modelo existe", "model_name": run_id}
    except Exception as e:
        logger.error("Erro ao validar o modelo: %s", str(e))
        raise HTTPException(status_code=404, detail="Modelo não encontrado")

@app.get("/api/health")
async def health_check():
    logger.info("Verificação de saúde realizada.")
    return {"status": "Estou saudável"}

@app.post("/api/predict")
async def predict(features: WineFeatures):
    
    run_id = 's3://mlflow/3/68485ba5b3d54280868ca5ebf740a219/artifacts/extra_trees_model'

    try:
        model = mlflow.sklearn.load_model(run_id)
        logger.info("Modelo carregado: %s ", run_id)
        
        data = {
            "alcohol": [features.alcohol],
            "malic_acid": [features.malic_acid],
            "ash": [features.ash],
            "alcalinity_of_ash": [features.alcalinity_of_ash],
            "magnesium": [features.magnesium],
            "total_phenols": [features.total_phenols],
            "flavanoids": [features.flavanoids],
            "nonflavanoid_phenols": [features.nonflavanoid_phenols],
            "proanthocyanins": [features.proanthocyanins],
            "hue": [features.hue],
            "od280_od315_of_diluted_wines": [features.od280_od315_of_diluted_wines],
            "proline": [features.proline]
        }

        input_df = pd.DataFrame(data)
        input_df.rename(columns={"od280_od315_of_diluted_wines":"od280/od315_of_diluted_wines"},inplace=True)
        logger.info("DataFrame criado: %s", input_df)

        prediction = model.predict(input_df)
        logger.info("Previsão realizada: %s", prediction)
        
        prediction_list = prediction.tolist()
        
        input_data = json.dumps(data)
        output_data = json.dumps({"prediction": prediction_list})
        
        upload_to_minio("trackerapi", "input_data.json", input_data)
        upload_to_minio("trackerapi", "output_data.json", output_data)

        return {"prediction": prediction_list, "model": run_id}
    except Exception as e:
        logger.error("Erro ao realizar a previsão: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
