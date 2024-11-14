from drf_yasg.openapi import Parameter, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
import json

response_list = {
    "message": [
        "Ok"
    ],
    "code": 200,
    "success": True,
    "data": [],
    "paginator": {
        "total_count": 1,
        "total_pages": 1,
        "current_page": 1,
        "limit": 10
    }
}

response_get = {
    "message": [
        "Ok"
    ],
    "code": 200,
    "success": True,
    "data": {}
}

response_post = {
    "message": [
        "Student created successfully."
    ],
    "code": 201,
    "success": True,
    "data": {}
}

response_update = {
    "message": [
        "Student updated successfully."
    ],
    "code": 200,
    "success": True,
    "data": {}
}

response_delete = {
    'message': [
        'Student deleted.'
    ],
    'code': 200,
    'success': True,
    'data': {}
}

response_unauthenticate = {
    'message': [
        "Authentication credentials were not provided."
    ],
    'code': 401,
    'data': {}
}

response_unauthorized = {
    'message': [
        "You do not have permission to perform this action."
    ],
    'code': 403,
    'data': {}
}

response_bad_request = {
    'message': [
        'Student already exists.'
    ],
    'code': 400,
    'success': False,
    'data': {}
}

response_not_found = {
    'message': [
        'Student not found.'
    ],
    'code': 404,
    'success': False,
    'data': {}
}

swagger_auto_schema_list = swagger_auto_schema(
    manual_parameters=[
        Parameter('sort_by', IN_QUERY, description='sort by id', type='char'),
        Parameter('sort_direction', IN_QUERY, description='sort_direction in ascending,descending', type='char'),
        Parameter('id', IN_QUERY, description='id parameter', type='int'),
        Parameter('keyword', IN_QUERY, description='keyword paramater', type='char'),
        Parameter('page', IN_QUERY, description='page no. paramater', type='int'),
        Parameter('limit', IN_QUERY, description='limit paramater', type='int'),
        Parameter('type', IN_QUERY, description='All result set type=all', type='char'),
        Parameter('start_date', IN_QUERY, description='start_date paramater', type='char'),
        Parameter('end_date', IN_QUERY, description='end_date paramater', type='char'),         
        Parameter('status', IN_QUERY, description='status paramater', type='int'),
    ],
    responses={
        '200': json.dumps(response_list),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
    },

    operation_id='list students',
    operation_description='API to list students data',
)

swagger_auto_schema_post = swagger_auto_schema(
    responses={
        '201': json.dumps(response_post),
        '400': json.dumps(response_bad_request),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
    },

    operation_id='Create students',
    operation_description='API to add students \n \n request :: {}',
)

swagger_auto_schema_update = swagger_auto_schema(
    responses={
        '200': json.dumps(response_update),
        '400': json.dumps(response_bad_request),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
        '404': json.dumps(response_not_found),
    },

    operation_id='update students',
    operation_description='API to update students \n \n request :: {}',
)

swagger_auto_schema_delete = swagger_auto_schema(
    responses={
        '200': json.dumps(response_delete),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
        '404': json.dumps(response_not_found),
    },

    operation_id='delete students',
    operation_description='API to delete students',
)

swagger_auto_schema_bulk_delete = swagger_auto_schema(
    responses={
        '200': json.dumps(response_delete),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
        '404': json.dumps(response_not_found),
    },

    operation_id='delete students',
    operation_description='API to bulk delete students',
)

swagger_auto_schema = swagger_auto_schema(     
    responses={
        '200': json.dumps(response_get),
        '401': json.dumps(response_unauthenticate),
        '403': json.dumps(response_unauthorized),
        '404': json.dumps(response_not_found),
    },

    operation_id='Fetch students',
    operation_description='API to fetch students',
)