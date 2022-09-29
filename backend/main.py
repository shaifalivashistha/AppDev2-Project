import logging

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_security import Security

from application.api import *
from application import workers
from application.models import *
from application.security import *
from application.database import db
from application.validation import *

from application.config import LocalDevelopmentConfig

logging.basicConfig(
    filename="./debug.log",
    level=logging.DEBUG,
    format=f"%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
)


app = None
api = None
celery = None


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config["CORS_HEADERS"] = "Content-Type"
    app.config.from_object(LocalDevelopmentConfig)

    db.init_app(app)
    app.app_context().push()
    app.logger.info("App setup complete")

    api = Api(app)
    app.app_context().push()

    _ = Security(app, user_datastore)

    celery = workers.celery
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        enable_utc=app.config["ENABLE_UTC"],
    )
    celery.Task = workers.ContextTask
    app.app_context().push()

    return app, api, celery


app, api, celery = create_app()

from application.controllers import *

from application.api import *


# # -------------------------API_ROUTES-------------------------#
# api.add_resource(UserAPI, "/api/users/", "/api/users/<int:id>")
# api.add_resource(TrackerAPI, "/api/trackers/", "/api/trackers/<int:id>/")
# api.add_resource(LogAPI, "/api/trackers/<int:id>/")
# api.add_resource(ExportTrackerAPI, "/<email>/tracker/export")
# api.add_resource(ExportLogAPI, "/<email>/tracker/<int:id/logs/export")

if __name__ == "__main__":
    app.run(debug=True)
