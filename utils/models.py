from django.db import models


class BaseModel(models.Model):
    '''模型类父类'''
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建实间' )
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改实间')

    class Meta(object):
        abstract = True