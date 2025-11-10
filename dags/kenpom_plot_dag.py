"""
Airflow DAG for KenPom Team Ratings Visualization
Generates a Plotly visualization of team ratings from KenPom API
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# In Astro, the include folder is automatically added to PYTHONPATH
# So we can directly import from kenpom_plot
from kenpom_plot import main


# Default arguments for the DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# Define the DAG
dag = DAG(
    'kenpom_plot_generator',
    default_args=default_args,
    description='Generate KenPom team ratings visualization',
    schedule_interval='@daily',  # Run daily
    catchup=False,
    tags=['kenpom', 'visualization', 'basketball'],
)


def run_kenpom_plot(**context):
    """
    Task function to run the KenPom plot generation
    
    Args:
        context: Airflow context dictionary
    
    Returns:
        Path to generated plot file
    """
    # Get the execution date from context
    execution_date = context.get('execution_date') or context.get('data_interval_start')
    
    # Use current year or execution date year
    # You can also use a fixed year or get it from Airflow Variables
    from airflow.models import Variable
    try:
        # Try to get year from Airflow Variable, fallback to execution year or 2026
        year_var = Variable.get("KENPOM_YEAR", default_var=None)
        if year_var:
            year = int(year_var)
        else:
            year = execution_date.year if execution_date else 2026
    except Exception:
        # Fallback to execution year or default
        year = execution_date.year if execution_date else 2026
    
    # Output to dags/output folder (accessible from local machine since dags/ is mounted)
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the main function
    output_path = main(year=year, output_dir=output_dir)
    
    return output_path


# Define the task
kenpom_plot_task = PythonOperator(
    task_id='generate_kenpom_plot',
    python_callable=run_kenpom_plot,
    dag=dag,
)

kenpom_plot_task

