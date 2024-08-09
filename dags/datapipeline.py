from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime
import os
import kaggle
import ast
import shutil
import pandas as pd
from airflow.utils.dates import days_ago
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

DATA_PATH = '/mnt/airflow/data'


def upload_files_to_s3():
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'paris-olympics-2024'  # Make sure this is a valid bucket name
    directory = '/mnt/airflow/processed_data'
    
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            s3_hook.load_file(
                filename=os.path.join(directory, filename),
                key=f"data/{filename}",  # Specify the path inside the bucket
                bucket_name=bucket_name,
                replace = True
            )


def authenticate_credentials()-> None:
    # Make sure kaggle.json is in the correct directory
    kaggle.api.authenticate()
    return 

def checkforfiles() -> None:
    if os.path.isdir(DATA_PATH) and len(os.listdir(DATA_PATH)) > 0:
        print(f"Directory {DATA_PATH} is not empty. Removing contents.")
        shutil.rmtree(DATA_PATH)
        os.mkdir(DATA_PATH)
        print(f"Contents of directory {DATA_PATH} removed successfully.")
    else:
        print(f"Directory {DATA_PATH} is empty or does not exist.")
    return 


def convert_to_csv(cell):
    try:
        lst = ast.literal_eval(cell)
        return ', '.join(lst)
    except:
        return cell


def remove_numbers(string):
    new_string = str()
    for x in string:
        if not x.isdigit():
            new_string += x.strip()
    return new_string

def create_bridge_table(df, team_col='code', athletes_col='athletes_codes'):
    # Initialize the DataFrame for the bridge table
    bridge_df = pd.DataFrame(columns=['team_code', 'athlete_code'])

    # Drop rows where athletes_col is NaN
    df = df.dropna(subset=[athletes_col])

    # Iterate over the rows of the DataFrame
    for _, row in df.iterrows():
        team_code = row[team_col]
        
        # Debug: Print the athlete codes to inspect the format
        # print(f"Raw athlete codes: {row[athletes_col]}")
        
        try:
            athletes_codes = ast.literal_eval(row[athletes_col])
        except ValueError as e:
            print(f"ValueError: {e}")
            continue

        # Create a new row for each athlete code
        for athlete_code in athletes_codes:
            new_row = {'team_code': team_code, 'athlete_code': athlete_code}
            bridge_df = pd.concat([bridge_df, pd.DataFrame([new_row])], ignore_index=True)

    return bridge_df


def process_data_venue()-> None:
    # Load the dataset
    df = pd.read_csv('/mnt/airflow/data/venues.csv')
    
    # Apply the conversion function to the 'sports' column
    df['sports'] = df['sports'].apply(convert_to_csv)
    
    # Drop the specified columns
    df = df.drop(columns=['date_start', 'date_end', 'url'])
    
    processed_file_path = '/mnt/airflow/processed_data/venues.csv'
    df.to_csv(processed_file_path, index=False)
    return


def process_data_athletes()->None:
    # Load the dataset
    df = pd.read_csv('/mnt/airflow/data/athletes.csv')
    
    # Specify the columns to keep
    columns = ['code', 'name', 'name_short', 'name_tv', 'gender', 'function',
               'country_code', 'country', 'country_full', 'nationality',
               'nationality_full', 'nationality_code', 'height', 'weight',
               'disciplines', 'events', 'birth_date']
    df = df[columns]
    
    # Apply the conversion function to the 'events' and 'disciplines' columns
    df['events'] = df['events'].apply(convert_to_csv)
    df['disciplines'] = df['disciplines'].apply(convert_to_csv)
    
    processed_file_path = '/mnt/airflow/processed_data/athletes.csv'
    df.to_csv(processed_file_path, index=False)
    return 


def process_data_teams()->None:

    # Read the CSV file
    df = pd.read_csv('/mnt/airflow/data/teams.csv')

    # Process the DataFrame
    bridge_table = create_bridge_table(df)
    bridge_file_path = '/mnt/airflow/processed_data/bridge_team_athlete.csv'
    bridge_table.to_csv(bridge_file_path, index=False)
    
    df['athletes_codes'] = df['athletes_codes'].apply(convert_to_csv)
    columns = ['code', 'team', 'team_gender', 'country','country_code', 'discipline', 'disciplines_code', 'events','num_athletes']
    df = df[columns]
    # Save the bridge table to a new CSV file
    processed_file_path = '/mnt/airflow/processed_data/teams.csv'
    df.to_csv(processed_file_path, index=False)
    
    return 


def process_data_totalmedals()->None:
    # Path to the events CSV file
    file_path = '/mnt/airflow/data/medals_total.csv'
    # Read the events CSV file into a DataFrame
    df = pd.read_csv(file_path)
    processed_file_path = '/mnt/airflow/processed_data/total_medals.csv'
    df.to_csv(processed_file_path, index=False)
    
    return



def process_data_schedules()->None:
    # Read the schedules CSV file
    file_path = '/mnt/airflow/data/schedules.csv'
    df = pd.read_csv(file_path)
    
    # Apply the remove_numbers function to 'venue_code' and 'venue' columns
    df['venue_code'] = df['venue_code'].apply(lambda x: remove_numbers(x) if isinstance(x, str) else x)
    df['venue'] = df['venue'].apply(lambda x: remove_numbers(x) if isinstance(x, str) else x)
    
    # Save the processed DataFrame back to CSV
    processed_file_path = '/mnt/airflow/processed_data/schedules.csv'
    df.to_csv(processed_file_path, index=False)
    
    return

def process_data_events()->None:
    # Path to the events CSV file
    file_path = '/mnt/airflow/data/events.csv'
    # Read the events CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Columns to retain
    columns = ['event', 'tag', 'sport', 'sport_code']
    
    # Select only the desired columns
    df = df[columns]
    
    processed_file_path = '/mnt/airflow/processed_data/events.csv'
    df.to_csv(processed_file_path, index=False)
    return


def process_data_medalists()->None:
    # Path to the events CSV file
    file_path = '/mnt/airflow/data/medallists.csv'
    # Read the events CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Columns to retain
    columns = ['medal_date', 'medal_type', 'medal_code', 'name', 'gender', 'country','country_code', 'nationality', 'team_gender', 'discipline','event', 'event_type', 'birth_date', 'code']
    
    # Select only the desired columns
    df = df[columns]
    
    processed_file_path = '/mnt/airflow/processed_data/medalists.csv'
    df.to_csv(processed_file_path, index=False)
    
    return

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 1),
    'retries': 0,
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
create_dir_task = BashOperator(
    task_id='create_dir',
    bash_command="mkdir -p /mnt/airflow/processed_data",
    dag=dag,
)
download_data = BashOperator(
    task_id='download_data',
    bash_command="mkdir -p /mnt/airflow/data && kaggle datasets download -d piterfm/paris-2024-olympic-summer-games -p /mnt/airflow/data/",
    dag=dag,
)
unzip_data = BashOperator(
    task_id='unzip_data',
    bash_command="unzip -o /mnt/airflow/data/paris-2024-olympic-summer-games.zip -d /mnt/airflow/data/",
    dag=dag,
)
process_venue_data_task = PythonOperator(
    task_id='process_venue',
    python_callable=process_data_venue,
    dag=dag,
)
process_athletes_data_task = PythonOperator(
    task_id='process_athletes',
    python_callable=process_data_athletes,
    dag=dag,
)
process_teams_data_task = PythonOperator(
    task_id='process_teams',
    python_callable=process_data_teams,
    dag=dag,
)
process_totalmedals_data_task = PythonOperator(
    task_id='process_medalstotal',
    python_callable=process_data_totalmedals,
    dag=dag,
)
process_schedules_data_task = PythonOperator(
    task_id='process_schedules',
    python_callable=process_data_schedules,
    dag=dag,
)
process_events_data_task = PythonOperator(
    task_id='process_events',
    python_callable=process_data_events,
    dag=dag,
)
process_medallists_data_task = PythonOperator(
    task_id='process_medallists',
    python_callable=process_data_medalists,
    dag=dag,
)
upload_to_s3_task = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_files_to_s3,
    dag=dag,
)


authenticate_task >> cleanup_task  >> download_data >> unzip_data >> create_dir_task >> [process_teams_data_task, process_venue_data_task, process_athletes_data_task,process_totalmedals_data_task,process_schedules_data_task,process_events_data_task,process_medallists_data_task] >> upload_to_s3_task
