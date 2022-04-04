
import pprint
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


import sys
import threading
import traceback


import threading
import odoo
from datetime import date, datetime
from xmlrpc.client import dumps, loads
import xmlrpc.client

from werkzeug.wrappers import Response

from odoo.http import Controller, dispatch_rpc, request, route
from odoo.service import wsgi_server
from odoo.fields import Date, Datetime
# from odoo.tools import lazy

import werkzeug.exceptions
import werkzeug.wrappers
import werkzeug.serving
import werkzeug.contrib.fixers


try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    # pylint: disable=bad-python3-import
    import xmlrpclib

LIMIT = 0

def wsgi_xmlrpc_ok(environ, start_response):
    """ Two routes are available for XML-RPC

    /xmlrpc/<service> route returns faultCode as strings. This is a historic
    violation of the protocol kept for compatibility.

    /xmlrpc/2/<service> is a new route that returns faultCode as int and is
    therefore fully compliant.
    """
    ## _logger.info ("\n------------XMLRP\n" + "AÑADIENDO CORS with" + "\n-------------------")
    ## _logger.info(environ)
    if environ["REQUEST_METHOD"] == "POST" and environ["PATH_INFO"].startswith(
        "/xmlrpc/"
    ):
        length = int(environ["CONTENT_LENGTH"])
        data = environ["wsgi.input"].read(length)

        # Distinguish betweed the 2 faultCode modes
        string_faultcode = True
        service = environ["PATH_INFO"][len("/xmlrpc/") :]
        if environ["PATH_INFO"].startswith("/xmlrpc/2/"):
            service = service[len("2/") :]
            string_faultcode = False
        params, method = xmlrpclib.loads(data)
        try:

            result = odoo.http.dispatch_rpc(service, method, params)
            response = xmlrpclib.dumps((result,), methodresponse=1, allow_none=False)

        except Exception as e:
            if string_faultcode:
                response =  wsgi_server.xmlrpc_handle_exception_string(e)
            else:
                response =  wsgi_server.xmlrpc_handle_exception_int(e)
        headers = [
                              ('Content-Type','text/xml'),('Content-Length', str(len(response))),
                              ('Access-Control-Allow-Origin','*'),
                              ('Access-Control-Allow-Methods','POST, GET, OPTIONS'),
                              ('Access-Control-Max-Age',1000),
                              ('Access-Control-Allow-Headers','origin, x-csrftoken, content-type, accept'),
                    ]
        ## _logger.info ("\n------------XMLRP\n" + "CORS AÑADIDAS" + "\n-------------------")
        return werkzeug.wrappers.Response(response=response, mimetype="text/xml", headers=headers)(
            environ, start_response)
    
class EnableCors(models.Model):
    _name ="enable.cors"

    
    @api.model_cr
    def _register_hook(self):
        ### 🐒-patch XML-RPC controller to know remote address.
        super()._register_hook()

        original_fn = wsgi_server.application_unproxied

        def _patch(environ, start_response):

            environ['HTTP_ORIGIN'] = environ['HTTP_REFERER'] = environ['HTTP_HOST']
            ## _logger.info ("\n------------XMLRPC\n" + environ['PATH_INFO'] + "\n-------------------")
            ## _logger.info(environ)
            if hasattr(threading.current_thread(), "uid"):
                del threading.current_thread().uid
            if hasattr(threading.current_thread(), "dbname"):
                del threading.current_thread().dbname
            if hasattr(threading.current_thread(), "url"):
                del threading.current_thread().url
            with odoo.api.Environment.manage():
                if environ["REQUEST_METHOD"] == "POST" and environ["PATH_INFO"].startswith("/xmlrpc/"):
                    ## _logger.info ("\n------------XMLRP\n" + environ['PATH_INFO'] + "\n-------------------")
                # Try all handlers until one returns some result (i.e. not None).
                    result = wsgi_xmlrpc_ok(environ, start_response)
                    if result:
                        return result
            return original_fn(environ, start_response)

        wsgi_server.application_unproxied = _patch
        