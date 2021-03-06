import os
import appdirs
from pathlib import Path
import yaml

config_dir_name = "drupal_dockerizer"
config_file_name = "config.yml"
user_config_dir = appdirs.user_config_dir()


class AppConfig:
    data = {}

    def __init__(self) -> None:
        user_config_path = Path(user_config_dir)
        config_dir_path = user_config_path.joinpath(config_dir_name)
        config_file_path = config_dir_path.joinpath(config_file_name)
        self.config_file_path = str(config_file_path)

        if not os.path.exists(str(config_dir_path)):
            os.mkdir(str(config_dir_path))

        if not os.path.exists(self.config_file_path):
            self.data = {
                "is_check_requirements_tools": False,
                "version": "0.0.5",
                "instances": {},
            }
            self.save()
        self.load()

    def save(self):
        file_config = open(self.config_file_path, "w")
        yaml.safe_dump(self.data, file_config, sort_keys=True)
        file_config.close()

    def load(self):
        file_config = open(self.config_file_path, "r")
        self.data = dict(yaml.full_load(file_config))
        file_config.close()

    def addInstance(self, instance_conf):
        self.data["instances"][instance_conf.data["compose_project_name"]] = {
            "instance": instance_conf.data["compose_project_name"],
            "root_dir": instance_conf.data["drupal_root_dir"],
            "domain": instance_conf.data["domain_name"]
            if instance_conf.data["advanced_networking"]
            else "http://localhost",
            "status": "up",
        }

    def stopInstance(self, instance_conf):
        self.data["instances"][instance_conf.data["compose_project_name"]][
            "status"
        ] = "stop"

    def upInstance(self, instance_conf):
        self.data["instances"][instance_conf.data["compose_project_name"]][
            "status"
        ] = "up"

    def removeInstance(self, instance_conf):
        del self.data["instances"][instance_conf.data["compose_project_name"]]
