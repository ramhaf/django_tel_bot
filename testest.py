from django.core.management.base import BaseCommand

import csv
from prayers.models import Prayer

class Command(BaseCommand):
    def pars_csv(self):
        with open('bot_init/services/namaztime.csv', newline='') as fp:
            reader = csv.reader(fp)
            for row in reader:
                # p = Prayer.objects.create(datetime=row[0].split(';')[0])
                print(row[0].split(';')[0])

    # pars_csv()
