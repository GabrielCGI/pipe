import os
import re
import sys
import json
import logging
import logging.config

def sanitize_filename(name: str, replacement: str = "_") -> str:
    """
    Replaces invalid filename characters with the given replacement.
    """
    
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)

def setup_log(
        logName: str,
        logConfigPath: str,
        logDirectory: str,
        with_time: bool=True) -> bool:
    """Set logging settings from a config and specify an output log dir.
    
    Note: Failed silently if he can't parse logConfigPath.
    LogConfigPath should be a json respecting Configuration dictionary schema
    https://docs.python.org/3/library/logging.config.html
    
    Args:
        logName (str): Log identifier.
        logConfigPath (str): Config path.
        logDirectory (str): Output Log directory.
    Returns:
        bool: return false if log could not be setup
    """
    try:
    
        log_config = None
        with open(logConfigPath, 'r') as log_file:
            log_config = json.load(log_file)
        if not log_config:
            print('No config', file=sys.stderr)
            return False
        
        
        sanitized_name = sanitize_filename(logName)
        if with_time:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_name = f"log_{sanitized_name}_{timestamp}.log"
        else:
            log_name = f"log_{sanitized_name}.log"

        log_file = os.path.join(logDirectory, log_name)
        
        os.makedirs(logDirectory, exist_ok=True)
        
        log_config['handlers']['file']['filename'] = log_file
        
        logging.config.dictConfig(log_config)
        return True

    except:
        return False