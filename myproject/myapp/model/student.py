from django.db import models
from .base import Base

class Student(Base):
    name = models.CharField(null=True, blank=True, max_length=256)
    age = models.SmallIntegerField(null=True, blank=True, db_index=True)
    
    STATUS_BY = ((1, 'Active'),(2, 'Inactive'),(3, 'Deleted'),)
    status = models.PositiveSmallIntegerField(choices=STATUS_BY, default=1)
    
    class Meta:
        db_table = "students"
        
    def __str__(self):
        return str(self.pk)
    
    @staticmethod
    def to_dict(instance):
        resp_dict = {}
        resp_dict['id'] = instance.id
        resp_dict['name'] = instance.name
        resp_dict['age'] = instance.age
        resp_dict['status'] = instance.status
        resp_dict['status_name'] = instance.get_status_display()
        
        return resp_dict    