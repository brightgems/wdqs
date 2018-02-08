# -*- coding: utf-8 -*-
import yaml
import os
import time

BASE_DIR = os.path.dirname(__file__)
config = yaml.load(open(os.path.join(BASE_DIR,"wdqs.yaml")))
user = config['jimu']['user']
password = config['jimu']['password']
user_center_url = "https://www.jimu.com/User/AssetOverview"
login_sign = u'上次登录'
JIMU_LOGIN_URL = "https://www.jimu.com/User/Login"
browser_driver = "Chrome"

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
            'maxBytes': 2048,
            'backupCount': 3
        }
    },
    'loggers': {

        'wdqs': {
            'handlers': ['file','console'],
            'level': 'DEBUG',
        },

    },
}
