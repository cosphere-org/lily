
import os  # pragma: no cover

from django.core.wsgi import get_wsgi_application  # pragma: no cover

os.environ.setdefault(  # pragma: no cover
    "DJANGO_SETTINGS_MODULE", "conf.settings")

application = get_wsgi_application()  # pragma: no cover
