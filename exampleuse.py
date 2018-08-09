#!/usr/bin/env python3
from flask import Flask
from wsdldecorator import service_method, wrap_in_envelope
from uuid import uuid4


app = Flask(__name__)

wsdl = "Exemplification.wsdl"

@app.route('/get_example', methods=['POST'])
@service_method(wsdl)
def ExampleGetOp():
    example = uuid4().hex
    response = wrap_in_envelope(opresponse, example)
    return response


@app.route('/store_example', methods=['POST'])
@service_method(wsdl)
def ExampleStoreOp():
    message = "the example was stored"
    response = wrap_in_envelope(opresponse, message)
    return response


app.run(debug=True, host="0.0.0.0", port=9999)