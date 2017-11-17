"""\
This module is used by WSGI server (whichever you choose).
Basically, ``app`` is provided as the WSGI enabled
application. For example::

    gunicorn -b 0.0.0.0:6543 wsgi:app

"""
from press.main import make_wsgi_app


app = make_wsgi_app()
