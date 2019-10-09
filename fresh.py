import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Drops all tables, then remakes and migrates migrations'

    def add_arguments(self, parser):
        parser.add_argument('basepath', type=str)

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        -- if the schema you operate on is not "current",
                        -- you will want to replace current_schema() in
                        -- query with 'schematodeletetablesfrom'
                        -- *and* update the generate 'DROP...' accordingly.
                        FOR r IN (
                            SELECT tablename
                            FROM pg_tables
                            WHERE schemaname = current_schema()
                        ) LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' ||
                            quote_ident(r.tablename) ||
                            ' CASCADE';
                        END LOOP;
                    END $$;
                """, [])

            for root, dirs, files in os.walk(options['basepath']):
                for name in files:
                    if 'migrations' in root and \
                        'apps' in root and \
                            name != '__init__.py':
                        os.remove(os.path.join(root, name))

            call_command('makemigrations')
            call_command('migrate')
        except Exception as e:
            raise CommandError(
                f'An error has ocurred while dropping tables. \n{e}'
            )

        self.stdout.write(self.style.SUCCESS('Database has been refreshed'))
