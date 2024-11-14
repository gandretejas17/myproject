from django.urls import re_path as url
from .views.student import StudentView

""" Students """
urlpatterns = [
    url(r'^students/$', StudentView.as_view({'get': 'list', 'post': 'create', 'delete': 'bulk_delete'})),
    url(r'^students/(?P<id>.+)/$', StudentView.as_view({'get': 'retrieve' , 'put': 'partial_update', 'delete': 'delete'})),
]