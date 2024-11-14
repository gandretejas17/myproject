from django.db import models

class Roles(models.Model):

    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    STATUS_CHOICES = ((1, 'Active'),(2, 'Inactive'),(3,'Deleted'))
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=1)
    
    class Meta:
        db_table = "roles"

    def __str__(self):
        return str(self.pk)

    @staticmethod    
    def to_dict(instance):
        resp_dict = {}
        resp_dict['id'] = instance.id
        resp_dict['name'] = instance.name
        resp_dict['status'] = instance.status
        resp_dict['status_name'] = instance.get_status_display()
              
        return resp_dict
