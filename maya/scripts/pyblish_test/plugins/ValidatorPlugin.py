import pyblish.api


class ValidatorPlugin(pyblish.api.InstancePlugin):
    """Validator of data

    Validate the instance to carry on the process

    """
    order = pyblish.api.ValidatorOrder
    targets = ["test_target"]
    families = ["test_family1","test_family2"]

    def process(self, instance):
        """
        Validate the instance to carry on the process
        :param instance
        :return:
        """

        self.log.debug("2 *** Validator process ***")

        # TODO

        # Example :
        # Check if custom parameter is a string
        name = instance.data["name"]
        custom_param = instance.data["customParam"]
        if not isinstance(custom_param, str):
            raise Exception("""Custom param not a string\n
            The custom param should be a string""")
        # if not name[-1] != "5":
        #     raise Exception("""Bad number instance""")
        self.log.debug("instance "+name+"(" +custom_param+") validated")
