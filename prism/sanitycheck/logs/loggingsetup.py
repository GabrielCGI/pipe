import os
import re
import sys
import json
import datetime
import logging
import logging.config

def sanitize_filename(name: str, replacement: str = "_") -> str:
    """
    Replaces invalid filename characters with the given replacement.
    """
    
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)

def setup_log(logName: str, logConfigPath: str, logDirectory: str):
    """Set logging settings from a config and specify an output log dir.
    
    Note: Failed silently if he can't parse logConfigPath.
    LogConfigPath should be a json respecting Configuration dictionary schema
    https://docs.python.org/3/library/logging.config.html
    
    Args:
        logName (str): Log identifier.
        logConfigPath (str): Config path.
        logDirectory (str): Output Log directory.
    """    
    
    log_config = None
    with open(logConfigPath, 'r') as log_file:
        log_config = json.load(log_file)
    if not log_config:
        print('No config', file=sys.stderr)
        return
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    sanitized_name = sanitize_filename(logName)
    log_name = f"log_{sanitized_name}_{timestamp}.log"
    log_file = os.path.join(logDirectory, log_name)
    
    os.makedirs(logDirectory, exist_ok=True)
    
    log_config['handlers']['file']['filename'] = log_file
    
    logging.config.dictConfig(log_config)
