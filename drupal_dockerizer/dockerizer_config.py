import os
import appdirs
from pathlib import Path
import yaml

CONFIG_NAME = ".drupal_dockerizer.yml"
CONFIG_NOT_FOUND_MESSAGE = (
    "Can`t find config. Please ensure that config exist in project."
)


def findConfigPath(current_dir: Path) -> str:
    config_path = str(current_dir.joinpath(CONFIG_NAME))
    if not os.path.exists(config_path):
        folder = current_dir.parent
        for i in range(len(folder.parts) + 1):
            if os.path.exists(folder.joinpath(CONFIG_NAME)):
                config_path = str(folder.joinpath(CONFIG_NAME))
                break
            folder = folder.parent
        if not os.path.exists(config_path):
            raise FileNotFoundError(CONFIG_NOT_FOUND_MESSAGE)
    return config_path


class DockerizerConfig:
    data = {
        "user_uid": 1000,
        "user_gid": 1000,
        "compose_project_name": "drupal-project",
        "docker_runtime_dir": "drupal-project",
        "drupal_root_dir": "",
        "drupal_web_root": "",
        "drupal_files_dir": "",
        "advanced_networking": False,
        "network_id": 2,
        "domain_name": "drupal-project.devel",
        "xdebug_enviroment": "",
        "solr": 4,
        "solr": False,
        "solr_version": 4,
        "solr_configs_path": "",
        "memcache": False,
        "install_adminer": False,
        "drush_commands": ["cc drush", "si --account-pass=admin --site-name='Drupal Dockerizer'", "cr"],
        "drush_version": 8,
        "phpversion": "7.4-develop",
        "ssl_cert_path": "",
        "ssl_key_path": "",
        "ssl_enabled": False,
        "custom_drupal_settings": """if (file_exists($app_root . '/' . $site_path . '/settings.local.php')) {
  include $app_root . '/' . $site_path . '/settings.local.php';
}
  """,
    }

    def __init__(self, current_dir, config_file_path=False, load=True) -> None:
        self.current_dir = current_dir
        if config_file_path:
            self.config_file_path = config_file_path
        if load:
            if os.path.exists(self.config_file_path):
                self.load()
            else:
                raise FileNotFoundError(CONFIG_NOT_FOUND_MESSAGE)

    def save(self) -> None:
        file_config = open(self.config_file_path, "w")
        yaml.safe_dump(self.data, file_config, sort_keys=True)
        file_config.close()

    def load(self, config_file_path=False) -> None:
        if not config_file_path:
            self.config_file_path = findConfigPath(self.current_dir)
        else:
            self.config_file_path = config_file_path
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(CONFIG_NOT_FOUND_MESSAGE)
        file_config = open(self.config_file_path, "r")
        self.data = dict(yaml.full_load(file_config))
        file_config.close()
