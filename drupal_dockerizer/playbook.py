import os
from pathlib import Path

CURRENT_DIR = Path().absolute()


class Playbook:
    def __init__(self, playbook="", drupal_root_dir="", become=False) -> None:
        self.playbook = playbook
        self.drupal_root_dir = drupal_root_dir
        self.become = "--ask-become-pass" if become else ""

    def run(self) -> None:
        os.chdir(Path(self.drupal_root_dir).joinpath(".drupal_dockerizer"))
        command = [
            "ANSIBLE_FORCE_COLOR=true",
            "ansible-playbook",
            self.playbook,
            self.become,
        ]
        os.system(" ".join(command))
        os.chdir(CURRENT_DIR)
