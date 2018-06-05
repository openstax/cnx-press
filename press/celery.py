from .config import configure


app = configure().make_celery_app()
