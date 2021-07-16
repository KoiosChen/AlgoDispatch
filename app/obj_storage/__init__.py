from flask import Blueprint

obj_storage = Blueprint('obj_storage', __name__)

from . import file_operator
