from __future__ import unicode_literals

from django.db import models
import uuid, json
from datetime import datetime, timedelta
import time, json

# Create your models here.


class PTT(models.Model):
    article_id = models.CharField(db_column = 'article_id', unique = True, max_length = 64)
    author = models.CharField(db_column = 'author', unique = False, max_length = 128, null = True)
    title = models.CharField(db_column = 'title', unique = False, max_length = 256, null = True)
    content = models.CharField(db_column = 'content', unique = False, max_length = 4096, null = True)
    date = models.DateTimeField(db_column = 'date', null = True)
    ip = models.CharField(db_column = 'ip', unique = False, max_length = 64, null = True)

    class Meta:
        db_table = 'PTT'

class Config(models.Model):
    name = models.CharField(db_column = 'name', unique = True, max_length = 16)
    value = models.CharField(db_column = 'value', unique = True, max_length = 10)

    class Meta:
        db_table = 'config'

class Keywords(models.Model):
    group = models.IntegerField(db_column = 'group',unique = False, default = 0)
    text = models.CharField(db_column = 'text',unique = False, max_length = 32)
    size = models.IntegerField(db_column = 'size',unique = False, default = 0)

    class Meta:
        db_table = 'Keywords'