from flask import Blueprint

orders = Blueprint('orders', __name__)

from . import orders_api
