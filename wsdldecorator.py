from functools import wraps
from lxml.objectify import fromstring, ObjectPath
from lxml.etree import QName, tostring
from lxml.builder import ElementMaker
from flask import request, make_response

class service_method(object):
    wsdl = None
    nsmap = None
    operations = None
    messages = None

    def __init__(self, wsdl_file):
        self.wsdl = self.import_wsdl(wsdl_file)
        self.operations = self.get_operations(self.wsdl)
        self.messages = self.get_messages(self.wsdl)


    def __call__(self, fn, *args, **kwargs):

        #this copies magic methods and attributes from the original function to the decorator
        @wraps(fn)
        def decorator(*args, **kwargs):

            if fn.__name__ not in self.operations:
                raise Exception("not a service method")

            #thid should have an apropiate action not an exception
            if not self.valid_input(fn.__name__, request.data):
                raise Exception("invalid input")

            fn.__globals__['opresponse'] = self.messages[fn.__name__]['output'] 
            return fn(*args, **kwargs)

        return decorator

    def valid_input(self, func, message):
        Envelope = fromstring(message)
        body = Envelope.Body.getchildren()
        rname = ""
        for element in body:
            rname = QName(element.tag).localname

        return rname == self.messages[func]['input']

    @staticmethod
    def get_operations(service):

        nsmap = service.nsmap
        elements = []

        for ops in service.binding.find(
            QName(nsmap['wsdl'], "operation")):
            elements.append(ops.get("name"))

        return elements

    @staticmethod
    def get_messages(service):

        nsmap = service.nsmap
        ops = {}

        for ptop in service.portType.find(
            QName(nsmap['wsdl'], "operation")):
            ops[ptop.get("name")] = {}

            #input/output
            for io in ptop.find(QName(nsmap['wsdl'], "input")):
                message = io.get("message").split("tns:")[1]
                ops[ptop.get("name")]['input'] = message 

            for io in ptop.find(QName(nsmap['wsdl'], "output")):
                message = io.get("message").split("tns:")[1]
                ops[ptop.get("name")]['output'] = message 

        return ops



    @staticmethod
    def import_wsdl(file):
        xml = None  
        with open(file, "rb") as f:
            xml = f.read()

        return fromstring(xml)


# the envelope is built manually here but it can be contructed automatically from the wsdl
def wrap_in_envelope(opresponse, data):
    nsmap = {"soapenv" : "http://schemas.xmlsoap.org/soap/envelope/", 
             "v3": "http://www.example.com/Exemplification/v3"}

    E = ElementMaker(namespace="http://schemas.xmlsoap.org/soap/envelope/",
                     nsmap=nsmap)

    v3 = ElementMaker(namespace="http://www.example.com/Exemplification/v3",
                     nsmap=nsmap)


    Envelope = E.Envelope
    Header = E.Header
    Body = E.Body
    HeaderResponse = v3.HeaderResponse
    Response = getattr(v3, opresponse)

    StatusCode = v3.StatusCode
    ErrorCode = v3.ErrorCode
    Message = v3.Message
    Data = v3.Data(data)
    envelope  = Envelope(Header(
                                HeaderResponse()), 
                           Body(
                                Response(
                                #getattr(Response, opresponse)(
                                         StatusCode(), ErrorCode(),
                                         Message(),
                                         Data)))

    httpheaders = {'content_type': 'application/soap+xml; charset=utf-8'}
    response = make_response(tostring(envelope),'200', httpheaders)

    return response