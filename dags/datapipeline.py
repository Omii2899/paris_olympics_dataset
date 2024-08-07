from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import os
import kaggle
# from custom_operators.cleanup_operator import CleanupOperator  # Adjust the import path as necessary

AIRFLOW_HOME = '/mnt/airflow'


def authenticate_credentials()-> None:
    # Make sure kaggle.json is in the correct directory
    kaggle.api.authenticate()
    return 

def checkforfiles()->None:
    file_path = os.path.join(AIRFLOW_HOME, 'paris-2024-olympic-summer-games.zip')
    dir_path = os.path.join(AIRFLOW_HOME, 'paris-2024-olympic-summer-games')

    if os.path.isfile(file_path):
        os.remove(file_path)

    if os.path.isdir(dir_path):
        os.rmdir(dir_path)
        
    return 
        
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 1),
    'retries': 1,
}

dag = DAG(
    dag_id = 'Download_Data',
    default_args=default_args,
    schedule_interval='@daily',
)

authenticate_task = PythonOperator(
    task_id='authentication',
    python_callable=authenticate_credentials,
    dag=dag,
)
cleanup_task = PythonOperator(
        task_id='checkforfiles',
        python_callable = checkforfiles,
        dag = dag,
    )

authenticate_task >> cleanup_task