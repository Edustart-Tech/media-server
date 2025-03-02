


# Basic usage with auto-reload on media_library code changes
python manage.py rundramatiq

# Specify custom directories to watch
python manage.py rundramatiq --watch-dirs media_library core utils

# Run with multiple processes and threads
python manage.py rundramatiq --processes 2 --threads 4

# Disable auto-reloading
python manage.py rundramatiq --no-reload
