from flask import Blueprint

roles = Blueprint('roles', __name__)

from . import roles_api
