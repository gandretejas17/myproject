import os
from uuid import uuid4
from .base import Base
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from utility.constants import FILE_SIZE, BYTES_PER_MB

def file_size(value):
    limit = FILE_SIZE * BYTES_PER_MB
    if value.size > limit:
        raise ValidationError(f'File too large {round((value.size / BYTES_PER_MB), 2)} MB. Size should not exceed 5 MB.')

def path_and_rename(instance, filename):
    from datetime import datetime
    upload_to = "static"
    ext = filename.split(".")[-1]
    if instance.pk:
        filename = f"{uuid4().hex}{instance.pk}.{ext}"
    else:
        date_str = str(datetime.now()).replace(" ", "_").replace(":", "_").replace(".", "_").replace("-", "_")
        filename = f"{uuid4().hex}{date_str}.{ext}"
    return os.path.join(upload_to, filename)


class Assets(Base):
    # Fields
    file_name = models.FileField(upload_to=path_and_rename, null=True, validators=[file_size])
    file_type = models.CharField(max_length=155, null=True, blank=True)
    file_size = models.FloatField(unique=False, null=True, blank=True)
    actual_file_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "assets"
        indexes = (
            models.Index(fields=("file_type", "file_size", "actual_file_name"),),
            models.Index(fields=("file_size", "actual_file_name"),),
            models.Index(fields=("file_type", "file_size"),),
            models.Index(fields=("actual_file_name", "file_type"),),
        )

    @staticmethod
    def to_dict(instance):
        resp_data = {}
        resp_data['id'] = instance.id
        resp_data['file_name'] = f"{settings.DOMAIN_URL}media/{str(instance.file_name)}"
        resp_data['actual_file_name'] = instance.actual_file_name
        resp_data['file_type'] = instance.file_type
        resp_data['file_size'] = instance.file_size
        return resp_data
