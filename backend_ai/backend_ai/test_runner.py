from django.test.runner import DiscoverRunner


class ShadowModelTestRunner(DiscoverRunner):
    """
    Test runner that temporarily makes 'managed=False' models 'managed=True'
    so that the test database creates the tables for shadow models.
    """

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps

        all_models = apps.get_models()

        self.unmanaged_models = [m for m in all_models if not m._meta.managed]

        for m in self.unmanaged_models:
            m._meta.managed = True

        super().setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super().teardown_test_environment(*args, **kwargs)

        for m in self.unmanaged_models:
            m._meta.managed = False
