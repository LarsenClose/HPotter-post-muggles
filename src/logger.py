''' Simple setup for HPotter's logging. '''
import logging
import logging.config

logging.config.fileConfig('src/logging.conf')
logger = logging.getLogger('hpotter')
