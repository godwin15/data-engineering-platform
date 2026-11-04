
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "data_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="wealth_management_silver_gold",
    description="Orchestrate all Silver and Gold transformations",
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["wealth-management", "medallion"],
) as dag:

    run_silver_sql = BashOperator(
        task_id="run_silver_sql_pipeline",
        bash_command=(
            "python /opt/airflow/scripts/"
            "run_silver_sql_pipeline.py"
        ),
    )

    run_silver_python = BashOperator(
        task_id="run_silver_python_pipeline",
        bash_command=(
            "python /opt/airflow/scripts/"
            "run_silver_pipeline.py"
        ),
    )

    run_gold = BashOperator(
        task_id="run_gold_pipeline",
        bash_command=(
            "python /opt/airflow/scripts/"
            "run_gold_pipeline.py"
        ),
    )

    validate_data_quality = BashOperator(
        task_id="validate_data_quality",
        bash_command=(
            "python /opt/airflow/scripts/"
            "validate_data_quality.py"
        ),
    )

    run_silver_sql >> run_silver_python >> run_gold >> validate_data_quality
