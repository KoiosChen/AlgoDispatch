from flask import Blueprint

algocap = Blueprint('algocap', __name__)

from . import algocap_api
