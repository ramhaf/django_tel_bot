from django.db import models

# Create your models here.

class Prayer(models.Model):
    date_time = models.DateTimeField()
    name = models.TextField()

    def __str__(self):
        return ['{}'.format(self.name), '{}'.format(self.date_time)]