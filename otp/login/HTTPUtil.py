from panda3d.core import *

class HTTPUtilException(Exception):

    def __init__(self, what):
        Exception.__init__(self, what)


class ConnectionError(HTTPUtilException):

    def __init__(self, what, statusCode):
        HTTPUtilException.__init__(self, what)
        self.statusCode = statusCode


class UnexpectedResponse(HTTPUtilException):

    def __init__(self, what):
        HTTPUtilException.__init__(self, what)


def getHTTPResponse(url, http, body = None):
    if body:
        hd = http.postForm(url, body)
    else:
        hd = http.getDocument(url)
    if not http.isValid():
        raise ConnectionError('Unable to reach %s' % url.cStr(), http.getStatusCode())
    stream = http.openReadBody()
    sr = StreamReader(stream, 1)
    response = sr.readlines()

    return response
