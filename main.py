import io
from sensor.configuration.mongo_db_connection import MongoDBClient
from sensor.exception import SensorException
import os , sys
from sensor.logger import logging


from sensor.pipeline.training_pipeline import TrainPipeline
from sensor.utils.main_utils import load_object
from sensor.ml.model.estimator import ModelResolver,TargetValueMapping
from sensor.configuration.mongo_db_connection import MongoDBClient
from sensor.exception import SensorException
import os,sys
from sensor.logger import logging
from sensor.pipeline import training_pipeline
from sensor.pipeline.training_pipeline import TrainPipeline
import os
from sensor.utils.main_utils import read_yaml_file
from sensor.constant.training_pipeline import SAVED_MODEL_DIR


from  fastapi import FastAPI
from sensor.constant.application import APP_HOST, APP_PORT
from starlette.responses import RedirectResponse
from uvicorn import run as app_run
from fastapi.responses import Response
from sensor.ml.model.estimator import ModelResolver,TargetValueMapping
from sensor.utils.main_utils import load_object
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi import FastAPI, File, UploadFile, Response
import pandas as pd


app = FastAPI()



origins = ["*"]
#Cross-Origin Resource Sharing (CORS) 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/",tags=["authentication"])
async def  index():
    return RedirectResponse(url="/docs")





@app.get("/train")
async def train():
    try:

        training_pipeline = TrainPipeline()

        if training_pipeline.is_pipeline_running:
            return Response("Training pipeline is already running.")
        
        training_pipeline.run_pipeline()
        return Response("Training successfully completed!")
    except Exception as e:
        return Response(f"Error Occurred! {e}")
        




# @app.get("/predict")
# async def predict():
#     try:

#     # get data and from the csv file 
#     # covert it into dataframe 
        

#         df =None

#         Model_resolver = ModelResolver(model_dir=SAVED_MODEL_DIR)
#         if not Model_resolver.is_model_exists():
#             return Response("Model is not available")
        
#         best_model_path = Model_resolver.get_best_model_path()
#         model= load_object(file_path=best_model_path)
#         y_pred=model.predict(df)
#         df['predicted_column'] = y_pred
#         df['predicted_column'].replace(TargetValueMapping().reverse_mapping,inplace=True)


#         # get the prediction output as you wnat 


    # except  Exception as e:
    #     raise  SensorException(e,sys)

import io
import traceback
from fastapi import FastAPI, File, UploadFile, Response
import pandas as pd
@app.post("/predict")  # Changed to POST for file upload
async def predict(file: UploadFile = File(...)):
    try:
        logging.info(f"Received file: {file.filename}")
        
        # 1. Validate file type
        if not file.filename.endswith('.csv'):
            logging.error(f"Invalid file type: {file.filename}")
            return Response("Please upload a CSV file only.", status_code=400)
        
        # 2. Read and validate CSV file
        try:
            contents = await file.read()
            logging.info(f"File size: {len(contents)} bytes")
            
            # Convert to dataframe
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            logging.info(f"DataFrame shape: {df.shape}")
            logging.info(f"DataFrame columns: {df.columns.tolist()}")
            
        except Exception as e:
            logging.error(f"Error reading CSV: {str(e)}")
            return Response(f"Error reading CSV file: {str(e)}", status_code=400)
        
        # 3. Validate dataframe
        if df.empty:
            logging.error("DataFrame is empty")
            return Response("Uploaded CSV file is empty.", status_code=400)
        
        # 4. Check for missing values
        missing_values = df.isnull().sum().sum()
        if missing_values > 0:
            logging.warning(f"Found {missing_values} missing values")
            # Fill missing values or handle as needed
            df = df.fillna(df.mean())  # Simple fill with mean for numeric columns
        
        # 5. Check if model exists
        try:
            model_resolver = ModelResolver(model_dir=SAVED_MODEL_DIR)
            if not model_resolver.is_model_exists():
                logging.error("Model not found")
                return Response("Model is not available", status_code=404)
            
            # Load the best model
            best_model_path = model_resolver.get_best_model_path()
            logging.info(f"Loading model from: {best_model_path}")
            model = load_object(file_path=best_model_path)
            
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            return Response(f"Error loading model: {str(e)}", status_code=500)
        
        # 6. Make predictions
        try:
            logging.info("Making predictions...")
            
            # Create a copy for predictions
            prediction_df = df.copy()
            
            # Make predictions
            y_pred = model.predict(prediction_df)
            logging.info(f"Predictions shape: {y_pred.shape if hasattr(y_pred, 'shape') else len(y_pred)}")
            
            # Add predictions to dataframe
            prediction_df['predicted_column'] = y_pred
            
            # Apply reverse mapping if available
            try:
                target_mapping = TargetValueMapping()
                if hasattr(target_mapping, 'reverse_mapping'):
                    prediction_df['predicted_column'] = prediction_df['predicted_column'].replace(
                        target_mapping.reverse_mapping
                    )
                    logging.info("Applied reverse mapping")
            except Exception as mapping_error:
                logging.warning(f"Could not apply reverse mapping: {mapping_error}")
                # Continue without reverse mapping
            
        except Exception as e:
            logging.error(f"Error making predictions: {str(e)}")
            return Response(f"Error making predictions: {str(e)}", status_code=500)
        
        # 7. Prepare response
        try:
            predictions_response = {
                "status": "success",
                "filename": file.filename,
                "total_records": len(prediction_df),
                "original_columns": df.columns.tolist(),
                "predictions_sample": prediction_df['predicted_column'].head(10).tolist(),
                "prediction_counts": prediction_df['predicted_column'].value_counts().to_dict(),
                "full_data": prediction_df.to_dict('records')  # Remove this if response is too large
            }
            
            logging.info("Prediction completed successfully")
            return predictions_response
            
        except Exception as e:
            logging.error(f"Error preparing response: {str(e)}")
            return Response(f"Error preparing response: {str(e)}", status_code=500)
        
    except Exception as e:
        logging.error(f"Unexpected error in predict endpoint: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return Response(f"Internal server error: {str(e)}", status_code=500)


def main():
    try:
            
        training_pipeline = TrainPipeline()
        training_pipeline.run_pipeline()
    except Exception as e:
        print(e)
        logging.exception(e)



if __name__ == "__main__":

    
    # database_name="ineuron"
    # collection_name ="sensor"
    # dump_csv_file_to_mongodb_collection(file_path,database_name,collection_name)
    app_run(app ,host=APP_HOST,port=APP_PORT)
