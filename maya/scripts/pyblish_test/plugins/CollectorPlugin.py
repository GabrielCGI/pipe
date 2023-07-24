import pyblish.api


class CollectorPlugin(pyblish.api.ContextPlugin):
    """Collector of data

    Collect in instances that will be processed individually

    """
    order = pyblish.api.CollectorOrder
    targets = ["test_target"]

    def process(self, context):
        """
        Collect data in instances that will be processed individually
        :param context
        :return:
        """

        self.log.debug("1 *** Collector process ***")

        # TODO

        # Example :
        # Creating instances
        name = "instance"
        custom_param = "test"
        context.create_instance(name+"1", family="test_family1", target="test_target", customParam=custom_param)
        context.create_instance(name+"2", family="test_family1", target="test_target", customParam=custom_param)
        context.create_instance(name+"3", family="test_family2", target="test_target", customParam=custom_param)
        context.create_instance(name+"4", family="test_family2", target="test_target", customParam=custom_param)
        context.create_instance(name+"5", family="test_family2", target="test_target", customParam=custom_param)
        self.log.debug("instance "+name+"(" +str(custom_param)+") collected")
