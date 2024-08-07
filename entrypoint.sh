#!/usr/bin/env bash

# Initialize the metastore
airflow db init

# Disable example DAGs
sed -i 's/load_examples = True/load_examples = False/' ${AIRFLOW_HOME}/airflow.cfg

# Run the scheduler in the background
airflow scheduler &> /dev/null &

# Create user (if not already created)
airflow users create -u olympics -p admin -r Admin -e admin@admin.com -f admin -l admin || true

# Run the web server in foreground (for Docker logs)
exec airflow webserver