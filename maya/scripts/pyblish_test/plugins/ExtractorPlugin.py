import pyblish.api


class ExtractorPlugin(pyblish.api.InstancePlugin):
    """Extractor of data

    Extract the data of the instance in order to integrate it

    """
    order = pyblish.api.ExtractorOrder
    targets = ["test_target"]
    families = ["test_family1","test_family2"]

    def process(self, instance):
        """
        Extract the data of the instance in order to integrate it
        :param instance
        :return:
        """

        self.log.debug("3 *** Extractor process ***")

        # TODO

        # Example :
        # Retrieving the datas of the instance and store a path for the integrator
        name = instance.data["name"]
        custom_param = instance.data["customParam"]
        instance.data["path"] = "example/of/path/"+name+"/"+custom_param
        self.log.debug("instance "+name+"(" +custom_param+") extracted")

