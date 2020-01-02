import json
from app.models import *
from django.utils.deprecation import MiddlewareMixin


class EventTrigger(MiddlewareMixin):

    def process_response(self, request, response):
        if request.method == 'GET':
            pass
        if request.method == 'POST':
            pass
        if request.method == 'PUT':
            pass
        if request.method == 'DELETE':
            pass
        return response
