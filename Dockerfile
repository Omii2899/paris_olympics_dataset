FROM python:3.9.14
LABEL maintainer="Aadarsh"

ARG AIRFLOW_VERSION=2.2.5
ARG AIRFLOW_HOME=/mnt/airflow

WORKDIR ${AIRFLOW_HOME}
ENV AIRFLOW_HOME=${AIRFLOW_HOME}

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /requirements.txt

# COPY ./.env /.env
# Upgrade pip separately to catch any issues
RUN pip install --upgrade pip && \
    useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow && \
    pip install apache-airflow==${AIRFLOW_VERSION} && \
    pip install -r /requirements.txt

# Copy the Airflow scripts
COPY ./dags ${AIRFLOW_HOME}/dags/
COPY ./kaggle.json ${AIRFLOW_HOME}/.config/kaggle/
COPY ./entrypoint.sh ${AIRFLOW_HOME}/entrypoint.sh
# Ensure the entrypoint script is executable
RUN chmod +x ${AIRFLOW_HOME}/entrypoint.sh

# Set ownership and permissions
RUN chown -R airflow:airflow ${AIRFLOW_HOME}

USER airflow

EXPOSE 8080

ENTRYPOINT [ "/mnt/airflow/entrypoint.sh" ]