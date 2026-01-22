from django.core.management.base import BaseCommand, CommandError
from api.scrapers.item_catalogue import RedCrossItemScraper


class Command(BaseCommand):
    help = "Scrape Red Cross item catalogue and store code-to-URL mappings in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            dest="clear_existing",
            default=True,
            help="Clear existing mappings before inserting new ones (default: True)",
        )
        parser.add_argument(
            "--no-clear",
            action="store_false",
            dest="clear_existing",
            help="Do not clear existing mappings, append to the database",
        )
        parser.add_argument(
            "--save-json",
            action="store_true",
            dest="save_json",
            default=False,
            help="Also save mappings to JSON files (code_to_url.json, missing_code_urls.json)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting item catalogue scraper..."))

        try:
            scraper = RedCrossItemScraper()

            self.stdout.write(self.style.HTTP_INFO("\n[1/2] Collecting product URLs from categories..."))
            homepage_url = "https://itemscatalogue.redcross.int/index.aspx"
            result = scraper.collect_products_from_top_level_categories(homepage_url)

            if not result or not result.get("all_urls"):
                raise CommandError("No product URLs found during collection phase")

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Found {len(result['all_urls'])} unique product URLs across {result['total_categories']} categories"
                )
            )

            self.stdout.write(self.style.HTTP_INFO("\n[2/2] Extracting codes and building mappings..."))
            code_results = scraper.build_code_to_url_mapping(result["all_urls"])

            if not code_results or not code_results.get("code_to_url"):
                raise CommandError("No codes found during extraction phase")

            self.stdout.write(
                self.style.SUCCESS(f"✓ Found {len(code_results['code_to_url'])} unique item codes")
            )
            self.stdout.write(
                self.style.WARNING(f"  ({len(code_results['missing_code_urls'])} URLs had no codes)")
            )

            self.stdout.write(self.style.HTTP_INFO("\nSaving to database..."))
            scraper.save_to_database(
                code_results["code_to_url"],
                clear_existing=options["clear_existing"],
            )

            if options["save_json"]:
                self.stdout.write(self.style.HTTP_INFO("Saving JSON files..."))
                scraper.save_to_json(code_results["code_to_url"], "code_to_url.json")
                scraper.save_to_json(code_results["missing_code_urls"], "missing_code_urls.json")
                self.stdout.write(self.style.SUCCESS("✓ JSON files saved"))

            self.stdout.write(
                self.style.SUCCESS(
                    "\n✓ Scraping completed successfully! "
                    "Item code mappings are now available in the database."
                )
            )

        except Exception as e:
            raise CommandError(f"Scraping failed: {str(e)}")
