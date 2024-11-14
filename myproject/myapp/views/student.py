import operator
from functools import reduce
from django.db.models import Q
from django.db import transaction
from simple_search import search_filter
from django.db.models.functions import Lower

""" utility """
from utility.constants import MESSAGES, STATUS_ACTIVE, STATUS_DELETED, STATUS_INACTIVE
from utility.response import ApiResponse
from utility.utils import (
    MultipleFieldPKModelMixin,
    CreateRetrieveUpdateViewSet,
    create_or_update_serializer,
    filter_array_list,
    filter_queryset,
    filter_status,
    get_field_type,
    get_pagination_resp,
    get_required_fields,
    transform_list,
    validate_empty_strings,
)

""" model imports """
from ..models import Student

""" serializers """
from ..serializers.student_serializer import StudentSerializer

""" swagger """
from ..swagger.student_swagger import (
    swagger_auto_schema,
    swagger_auto_schema_post,
    swagger_auto_schema_update,
    swagger_auto_schema_list,
    swagger_auto_schema_delete,
    swagger_auto_schema_bulk_delete
)


class StudentView(MultipleFieldPKModelMixin, CreateRetrieveUpdateViewSet, ApiResponse):
    serializer_class = StudentSerializer
    singular_name = "Student"
    model_class = Student.objects.filter(status__in=[STATUS_ACTIVE, STATUS_INACTIVE])

    search_fields = ["name"]

    def get_object(self, pk):
        try:
            return self.model_class.get(pk=pk)
        except Exception:
            return None

    @swagger_auto_schema        
    def retrieve(self, request, *args, **kwargs):
        """
        :To get the single record
        """
        """ capture data """
        get_id = self.kwargs.get("id")

        """ process/format on data """
        instance = self.get_object(get_id)
        if instance:
            resp_dict = self.transform_single(instance)

            return ApiResponse.response_ok(self, data=resp_dict)

        return ApiResponse.response_not_found(self, message=self.singular_name + MESSAGES['not_found'])
    
    @swagger_auto_schema_post
    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        :To create the new record
        """
        sp1 = transaction.savepoint()

        """ capture data """
        req_data = request.data.copy()
        if not req_data:
            return ApiResponse.response_bad_request(self, message=MESSAGES['all_fields_should_not_empty'])

        name = req_data.get("name")
        age = req_data.get("age")
        
        required_field = ["name", "age"]
        if required_field := get_required_fields(required_field, req_data):
            return ApiResponse.response_bad_request(self, message=required_field)        
    
        if error_message := validate_empty_strings({"name":name}, req_data):
            return ApiResponse.response_bad_request(self, message=error_message)
               
        if age not in range(0, 41):
            return ApiResponse.response_bad_request(self, message="Enter the valid age.")    
               
        if self.model_class.filter(name__iexact=name.strip(), age=age, status=STATUS_ACTIVE).exists():
            return ApiResponse.response_bad_request(self, message= f"{self.singular_name}" + " already exists.")

        req_data["status"] = STATUS_ACTIVE
        req_data["name"] = name.strip()

        """ validate serializer """
        _, error = create_or_update_serializer(self.serializer_class, req_data, sp1)
        if error:
            return ApiResponse.response_bad_request(self, message=error)

        """ success response """
        transaction.savepoint_commit(sp1)
        return ApiResponse.response_created(self, data=req_data, message=f"{self.singular_name}" + MESSAGES["created"])

    @swagger_auto_schema_update
    @transaction.atomic()
    def partial_update(self, request, *args, **kwargs):
        """
        :To update the existing record
        """
        sp1 = transaction.savepoint()

        """ capture data """
        req_data = request.data
        if not req_data:
            return ApiResponse.response_bad_request(self, message=MESSAGES['all_fields_should_not_empty'])
        
        get_id = self.kwargs.get("id")
        instance = self.get_object(get_id)
        if not instance:
            return ApiResponse.response_not_found(self, message=self.singular_name + MESSAGES['not_found'])
        
        name = req_data.get("name")
        age = req_data.get("age")
        status = req_data.get("status")

        if name:
            if error_message := validate_empty_strings({"name":name}, req_data):
                return ApiResponse.response_bad_request(self, message=error_message)

        if age and age not in range(0, 41):
            return ApiResponse.response_bad_request(self, message="Enter the valid age.") 

        if status and status not in [STATUS_ACTIVE, STATUS_INACTIVE]:
            return ApiResponse.response_bad_request(self, message="Invalid status.")
                              
        if name and age:
            if self.model_class.filter(name__iexact=name.strip(), age=age, status=STATUS_ACTIVE).exclude(id=instance.id).exists():
                return ApiResponse.response_bad_request(self, message=f"{self.singular_name}" + " already exists.")
        
            req_data["name"] = name.strip()
        
        """ validate serializer """
        _, error = create_or_update_serializer(self.serializer_class, req_data, sp1, instance)
        if error:
            return ApiResponse.response_bad_request(self, message=error)

        """ success response """
        transaction.savepoint_commit(sp1)
        return ApiResponse.response_ok(self, data=req_data, message=f"{self.singular_name}" + MESSAGES["updated"])

    @swagger_auto_schema_list
    def list(self, request, *args, **kwargs):
        """
        :To get the all records
        """
        where_array = request.query_params
        
        # capture data
        obj_list = []

        filter_array = {"id": "id", "name": "name", "age": "age"}
        obj_list = filter_array_list(filter_array, where_array, obj_list)
        
        default_obj_list, sort_by, error_response = filter_queryset(request, where_array)
        if error_response:
            return ApiResponse.response_bad_request(self, message=[str(error_response.args[0])])
        if default_obj_list:
            obj_list = default_obj_list 

        status_obj_list, error_response = filter_status(where_array)
        if error_response:
            return ApiResponse.response_bad_request(self, message=error_response)
        if status_obj_list:
            obj_list.extend(status_obj_list)

        q_list = [Q(x) for x in obj_list]
        if q_list:
            queryset = self.model_class.filter(reduce(operator.and_, q_list)).order_by((sort_by))
        else:
            queryset = self.model_class.order_by((sort_by))

        """Search for keyword"""
        if where_array.get("keyword"):
            queryset = queryset.filter(search_filter(self.search_fields, where_array.get("keyword")))

        if field_type := get_field_type(Student, sort_by):
            if field_type == 'CharField':
                queryset = queryset.order_by(Lower(sort_by))

        resp_data = get_pagination_resp(queryset, request)

        response_data = transform_list(self, resp_data.get("data"))

        return ApiResponse.response_ok(self, data=response_data, paginator=resp_data.get("paginator"))

    @swagger_auto_schema_delete
    def delete(self, request, *args, **kwargs):
        """
        :To delete the single record.
        """
        get_id = self.kwargs.get("id")

        """ get instance """
        instance = self.get_object(get_id)
        if not instance:
            return ApiResponse.response_not_found(self, message=self.singular_name + MESSAGES['not_found'])

        instance.status=STATUS_DELETED
        instance.save()

        return ApiResponse.response_ok(self, message=self.singular_name + " deleted.")

    @swagger_auto_schema_bulk_delete
    def bulk_delete(self, request, *args, **kwargs):
        """
        :To delete the multiple record.
        """
        """ capture data """
        req_data = request.data
        ids = req_data.get("ids")

        if not ids or not isinstance(ids, list):
            return ApiResponse.response_bad_request(self, message="Please select " + self.singular_name.lower())

        """ get instance """
        queryset = self.model_class.filter(id__in=ids)
        if not queryset:
            return ApiResponse.response_not_found(self, message=self.singular_name + MESSAGES['not_found'])

        queryset.update(status=STATUS_DELETED)

        return ApiResponse.response_ok(self, message=self.singular_name + " deleted.")
    
    ##Generate the response
    def transform_single(self, instance):
        resp_dict = {}
        resp_dict = Student.to_dict(instance)

        return resp_dict   