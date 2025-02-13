import imp

def reloadAllModules(packages):
    """Quick routine to reload every modules
    in a packages.

    Args:
        packages (module): Packages containing modules
    """
    
    for module_name in dir(packages):
        if (not module_name.startswith("__")
            and not module_name.endswith("__")):
            module = getattr(packages, module_name)
            
            # Check if module is a module
            if isinstance(module, type(imp)):
                imp.reload(module)
