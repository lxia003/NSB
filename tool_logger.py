import datetime
import logging
import logging.config
import os


def init_log(log_instance):
    """
        This function is to dump trace into log file
    :return:
        log instance. Module can use this instance to dump trace
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = log_instance + "_" + datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
    logging_conf = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                'format': '%(asctime)s [%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s'
            },
            'standard': {
                'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s'
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },

            "default": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": os.path.join(log_dir, log_file),
                'mode': 'w+',
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 20,
                "encoding": "utf8"
            },
        },

        "root": {
            'handlers': ['default', 'console'],
            'level': "INFO",
            'propagate': False
        }
    }

    logging.config.dictConfig(logging_conf)

    # configure application log
    return logging.getLogger(log_instance)