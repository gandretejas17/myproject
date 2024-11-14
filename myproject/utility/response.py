from rest_framework.response import Response


class ApiResponse(object):
    def __init__(self, message="Okay", code=200, success=True, data={}, paginator={}):
        if data is None:
            data = dict()
        self.message = message
        self.code = code
        self.success = success
        self.data = data
        self.paginator = paginator

    def message_format(self, message):
        if type(message) == str:
            return [message]
        else:
            return message

    def response_created(self, message="Resource created", code=201, success=True, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_ok(self, message="Ok", code=200, success=True, data={}, paginator={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        if paginator:
            data['paginator'] = paginator
        return Response(data=data, status=code)

    def response_internal_server_error(self, message="Internal server error", code=500, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_bad_request(self, message="Bad Request", code=400, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_unauthenticate(self, message="Unauthenticate", code=401, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_unauthorized(self, message="Unauthorized", code=403, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_not_found(self, message="Not Found", code=404, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)

    def response_not_acceptable(self, message="Not acceptable", code=406, success=False, data={}):
        message = self.message_format(message)
        data = {"message": message, "code": code, "success": success, "data": data}
        return Response(data=data, status=code)
