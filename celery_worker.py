# Entrypoint for running celery worker: celery -A celery_worker.celery worker --loglevel=info
from tasks import celery
