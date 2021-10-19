from django.db import models
from django.contrib.auth.models import User

class account_manager(models.Manager):
    def test(self):
        pass

class account(models.Model):
    name                    = models.CharField(max_length=100)
    email                   = models.EmailField(max_length=100)
    user                    = models.ForeignKey(User, 
                                                related_name="account", 
                                                on_delete=models.CASCADE, 
                                                null=True
                                                )

    objects = account_manager()

    class Meta:
        pass
