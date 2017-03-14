import yaml
import os
import time

BASE_DIR = os.path.dirname(__file__)
config = yaml.load(open(os.path.join(BASE_DIR,"wdqs.yaml")))
user = config['jimu']['user']
password = config['jimu']['password']


# logging config
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s',
            'convert':time.localtime
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
			'filename': 'wdqs.log',
			'maxBytes': "20480",
			'backupCount': 3
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'wdqs': {
            'handlers': ['file','console'],
            'level': 'INFO',
        },

    },
}
