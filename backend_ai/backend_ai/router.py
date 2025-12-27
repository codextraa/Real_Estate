class SharedDatabaseRouter:
    """
    Prevents the AI backend from managing shared tables (Auth, Sessions).
    """

    EXTERNAL_APPS = {"sessions", "auth", "contenttypes", "admin"}

    def db_for_read(self, model, **hints):  # pylint: disable=unused-argument
        return "default"

    def db_for_write(self, model, **hints):  # pylint: disable=unused-argument
        return "default"

    def allow_relation(self, obj1, obj2, **hints):  # pylint: disable=unused-argument
        return True

    def allow_migrate(
        self, db, app_label, model_name=None, **hints
    ):  # pylint: disable=unused-argument
        if app_label in self.EXTERNAL_APPS:
            return False
        return True
