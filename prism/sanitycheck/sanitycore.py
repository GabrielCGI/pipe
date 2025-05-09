import os
from pathlib import Path
import importlib
import time

import logging
from .logs import loggingsetup

LOG_DIRECTORY = 'R:/logs/sanity_check_logs'
LOG_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    'configs', 'logconfig.json')

loggingsetup.setup_log('sanity_check', LOG_CONFIG_PATH, LOG_DIRECTORY)

# TODO Find a way to specify the package __name__ instead of root
logger = logging.getLogger()
logger.info('Init logger')

YAML_FILE = os.path.join(os.path.dirname(__file__),'configs' ,'check_hierarchy.yaml')

def getProductionPath(core):
    
    filepath = core.getCurrentFileName()
    entity = core.getScenefileData(filepath)
    
    if not entity:
        return ''
    
    entity_type = entity.get('type')
    department = entity.get('department')
    task = entity.get('task')
    
    path = []
    if entity_type == 'asset':
        path.append('Assets')
    elif entity_type == 'shot':
        path.append('Shots')
    else:
        return ''
    
    path.append(str(department))
    path.append(str(task))
    
    return str(Path(*path))


def parseChecks(checkPath: str, checksDatas: dict):
    
    checks = []
    checksDatas = checksDatas['Production']
    if checksDatas['rules']:
        checks += checksDatas['rules']
    for depth in Path(checkPath).parts:
        checksDatas = checksDatas.get(depth, None)
        if not checksDatas:
            return checks
        current_checks = checksDatas.get('rules', [])
        if current_checks:
            checks += current_checks
            
    return list(set(checks))


def getCheck(checks):
    
    module = f'{__package__}.checks.check'
    check_module = importlib.import_module(module)
    
    checklist = []
    for check in checks:
        try:
            module = f'{__package__}.checks.{check.lower()}'
            check_module = importlib.import_module(module)
            importlib.reload(check_module)
            try:
                check = getattr(check_module, check)()
                checklist.append(check)
            except Exception as e:
                logger.warning(e)
                logger.warning(f'Did not find {check} in {check_module.__name__}')
                continue
        except Exception as e:
            logger.warning(e)
            logger.warning(f'Did not find {check.lower()}.py in checks')
            continue
        
    return checklist


def execChecks(stateManager, checklist):
      
    for check in checklist:
        try:
            check.run(stateManager)
        except Exception as e:
            logger.error(e)
        

def main(*args):
    state_manager = args[0]
    yaml_config = args[1]
    
    core = state_manager.core

    if not os.path.exists(yaml_config):
        core.popup("Yaml config has not been found", severity='error')
        return True

    data = core.readYaml(yaml_config)
    logger.info(f'Successfully read data from {yaml_config}')

    path = getProductionPath(core)
    checks = parseChecks(path, data)
    logger.info(f'Parsed checks for {path}')
        
    checklist = getCheck(checks)
    logger.info(f'Get {len(checklist)} checks.')
    
    sanityui = importlib.import_module(f'{__package__}.ui.sanityui')
    importlib.reload(sanityui)
    
    logger.info(f'Open sanity UI.')
    dialog = sanityui.MainDialog(
        checkList=checklist,
        stateManager=state_manager,
        path=str(Path(path).as_posix()))

    if dialog.has_no_error:
        logger.info('Sanity check sucessfully passed.')
        return True
    
    res = dialog.exec()
    
    if res:
        
        msg = ('<h3>Sanity check sucessfully passed.<br>'
               f'{len(checklist)}/{len(checklist)} check passed.</h3>')
        popup = state_manager.core.waitPopup(state_manager.core, msg)
        with popup:
            time.sleep(1)
    return bool(res)
    