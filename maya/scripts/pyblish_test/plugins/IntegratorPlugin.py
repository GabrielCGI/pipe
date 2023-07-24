import pyblish.api


class IntegratorPlugin(pyblish.api.InstancePlugin):
    """Integrator

    Integrate the instance with the extracted data

    """
    order = pyblish.api.IntegratorOrder
    targets = ["test_target"]
    families = ["test_family1","test_family2"]

    def process(self, instance):
        """
        Integrate the instance with the extracted data
        :param instance
        :return:
        """

        self.log.debug("4 *** Integrator process ***")

        # TODO

        # Example :
        # Retrieve the path of the instance
        name = instance.data["name"]
        custom_param = instance.data["customParam"]
        path = instance.data["path"]
        self.log.debug("instance "+name+"("+custom_param+") integrated with path:"+path)



