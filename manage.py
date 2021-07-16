#!/usr/bin/env python
import os
import multiprocessing
from app import create_app, db
from flask_script import Manager
from flask_migrate import Migrate

__author__ = 'Koios'

app = create_app(os.getenv('FLASK_CONFIG') or 'production')
manager = Manager(app)
migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2222, debug=False)
