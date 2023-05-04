try:
    import sys
    import json
    import pymel.core as pm
    msg_result = sys.argv[1]
    input_data = json.loads(sys.argv[2])
    for name,path in input_data:
        pm.openFile(path, force=True)
        unknown_plugins = pm.unknownPlugin(query=True, list=True)
        if unknown_plugins is None : unknown_plugins = []
        data = {
            "name": name,
            "filepath": path,
            "unknown_plugin_names": [str(node) for node in unknown_plugins],
        }
        print(msg_result+" "+json.dumps(data))
except Exception as e:
    print(str(e))