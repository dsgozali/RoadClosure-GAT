class SnowflakeReadOnlyRouter:
    router_app_labels = {"racp"}
    def db_for_read(self, model, **hints):
        return "TA_VOL" if model._meta.app_label in self.router_app_labels else None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.router_app_labels:
            raise RuntimeError("Snowflake is read-only in this project")
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "TA_VOL":
            return False
        if app_label in self.router_app_labels:
            return False

        return None