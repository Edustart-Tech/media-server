# media_library/management/commands/rundramatiq_v2.py
import os
import sys
import time
import logging
import subprocess
from django.core.management.base import BaseCommand
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('dramatiq_worker')

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.last_restart = time.time()
        self.cooldown = 2  # cooldown period in seconds to avoid multiple restarts

    def on_any_event(self, event):
        # Skip temporary files, __pycache__, and migrations
        if (event.src_path.endswith('.pyc') or
                '__pycache__' in event.src_path or
                'migrations' in event.src_path or
                '.git' in event.src_path):
            return

        # Only react to .py file changes
        if not event.src_path.endswith('.py'):
            return

        current_time = time.time()
        if current_time - self.last_restart >= self.cooldown:
            logger.info(f"Code change detected: {event.src_path}")
            self.last_restart = current_time
            self.callback()

class Command(BaseCommand):
    help = 'Runs Dramatiq workers with auto-reload on code changes'

    def add_arguments(self, parser):
        parser.add_argument('--processes', type=int, default=1,
                            help='Number of processes to run')
        parser.add_argument('--threads', type=int, default=8,
                            help='Number of threads per process')
        parser.add_argument('--no-reload', action='store_true',
                            help='Disable auto-reloading')
        parser.add_argument('--watch-dirs', nargs='+', default=['media_library'],
                            help='Directories to watch for code changes')

    def handle(self, *args, **options):
        self.processes = options['processes']
        self.threads = options['threads']
        self.no_reload = options['no_reload']
        self.watch_dirs = options['watch_dirs']
        self.process = None

        # Set environment variable for verbose logging
        os.environ['DRAMATIQ_VERBOSE'] = '1'

        try:
            if self.no_reload:
                self.start_worker()
                # This will block until the process exits
                self.process.wait()
            else:
                self.setup_auto_reload()

                # Start the worker initially
                self.restart_worker()

                # Keep the management command running
                while True:
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        self.stop_worker()
                        break

        except KeyboardInterrupt:
            self.stop_worker()
            self.stdout.write(self.style.SUCCESS('Dramatiq worker stopped'))

    def start_worker(self):
        """Start the Dramatiq worker process"""
        cmd = [
            sys.executable, "-m", "dramatiq",
            "--verbose",
            "--processes", str(self.processes),
            "--threads", str(self.threads),
            "media_library.tasks"
        ]

        self.stdout.write(self.style.SUCCESS(
            f'Starting Dramatiq with {self.processes} processes and {self.threads} threads per process'
        ))

        # Use Popen instead of run to get a reference to the process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Start a thread to continuously read and print the process output
        import threading
        def log_output():
            for line in self.process.stdout:
                self.stdout.write(line.strip())

        threading.Thread(target=log_output, daemon=True).start()

    def stop_worker(self):
        """Stop the Dramatiq worker process"""
        if self.process and self.process.poll() is None:  # Process is still running
            logger.info("Stopping Dramatiq worker...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Dramatiq worker did not terminate gracefully, forcing...")
                self.process.kill()

    def restart_worker(self):
        """Restart the Dramatiq worker process"""
        self.stop_worker()
        time.sleep(1)  # Give it a moment to fully stop
        self.start_worker()

    def setup_auto_reload(self):
        """Set up file system watchers for auto-reloading"""
        self.stdout.write(self.style.SUCCESS(f'Auto-reloading enabled. Watching directories: {", ".join(self.watch_dirs)}'))

        # Set up file watcher
        event_handler = CodeChangeHandler(self.restart_worker)
        self.observer = Observer()

        for watch_dir in self.watch_dirs:
            path = os.path.join(os.getcwd(), watch_dir)
            if os.path.exists(path):
                self.observer.schedule(event_handler, path=path, recursive=True)
            else:
                logger.warning(f"Watch directory does not exist: {path}")

        self.observer.start()
