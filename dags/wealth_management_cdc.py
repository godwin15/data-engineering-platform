from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from pipeline_monitoring import on_pipeline_success, on_pipeline_failure

default_args = {
    "owner": "data_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="wealth_management_client_cdc",
    description="Process incremental client CDC events",
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule_interval=None,
    catchup=False,
    on_success_callback=on_pipeline_success,
    on_failure_callback=on_pipeline_failure,
    max_active_runs=1,
    tags=["wealth-management", "cdc", "incremental"],
) as dag:

    process_client_changes = BashOperator(
        task_id="process_client_changes",
        bash_command="python /opt/airflow/scripts/process_client_cdc.py",
    )

    validate_client_changes = BashOperator(
        task_id="validate_client_changes",
        bash_command="python /opt/airflow/scripts/validate_client_cdc.py",
    )

    process_client_changes >> validate_client_changes
