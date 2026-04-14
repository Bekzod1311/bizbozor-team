import csv
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from listings.models import Listing, Category, Region, District


class Command(BaseCommand):
    help = "CSV fayldan listinglarni import qiladi"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV fayl yo‘li')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        try:
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                created_count = 0
                skipped_count = 0

                for row in reader:
                    try:
                        category = Category.objects.get(slug=row['category_slug'])
                        region = Region.objects.get(id=row['region_id'])
                        district = District.objects.get(id=row['district_id'])
                        owner = User.objects.get(username=row['owner_username'])

                        title = row['title'].strip()

                        if Listing.objects.filter(title=title, owner=owner).exists():
                            self.stdout.write(
                                self.style.WARNING(f"Skipped (already exists): {title}")
                            )
                            skipped_count += 1
                            continue

                        listing = Listing.objects.create(
                            owner=owner,
                            category=category,
                            region=region,
                            district=district,
                            title=title,
                            price=Decimal(row['price']),
                            short_description=row['short_description'].strip(),
                            description=row['description'].strip(),
                            phone=row['phone'].strip(),
                            telegram_username=row['telegram_username'].strip(),
                            google_maps_link=row['google_maps_link'].strip(),
                            status=row['status'].strip(),
                        )

                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Created: {listing.title}")
                        )

                    except Exception as e:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"Skipped row بسبب xato: {row} | Error: {e}")
                        )

                self.stdout.write(self.style.SUCCESS(
                    f"Import tugadi. Created: {created_count}, Skipped: {skipped_count}"
                ))

        except FileNotFoundError:
            raise CommandError(f"Fayl topilmadi: {csv_file}")