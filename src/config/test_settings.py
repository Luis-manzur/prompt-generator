from config.settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

OLLAMA_MODEL = 'test-model'
OLLAMA_HOST = 'http://localhost:11434'
SECRET_KEY = 'test-secret-key-not-for-prod'
