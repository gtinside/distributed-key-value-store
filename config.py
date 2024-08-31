
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.yaml', '.secrets.yaml'],
    environments = True,
    apply_default_on_none = True
)

print(settings.server.ip)  # Will print "127.0.0.1" for development, "0.0.0.0" for production, or the default value
print(settings.zooKeeper.host)  # Will print "localhost"
print(settings.dataDirectory)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
