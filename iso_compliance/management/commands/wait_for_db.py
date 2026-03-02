import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database to be available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        max_attempts = 30
        attempt = 0
        
        while not db_conn and attempt < max_attempts:
            try:
                db_conn = connections['default']
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS('Database available!'))
            except OperationalError:
                attempt += 1
                self.stdout.write(f'Database unavailable, waiting... (attempt {attempt}/{max_attempts})')
                time.sleep(2)
        
        if not db_conn:
            self.stdout.write(self.style.ERROR('Database connection failed after 30 attempts'))
            raise Exception('Could not connect to database')