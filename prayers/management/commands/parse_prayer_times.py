from django.core.management.base import BaseCommand
from bot_init.service import download_namaztimecsv

import csv
from prayers.models import Prayer


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        download_namaztimecsv()
        # with open('bot_init/services/namaztime.csv', newline='') as fp:
        #     reader = csv.reader(fp)
        #     for row in reader:
        #         # p = Prayer.objects.create(datetime=row[0].split(';')[0])
        #         print(row[0].split(';')[0])

    # pars_csv()
