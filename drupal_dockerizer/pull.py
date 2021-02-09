import os


class Pull():
  repository = 'https://github.com/jet-dev-team/drupal-dockerizer.git'

  def __init__(self, playbook='', config_path='', tag='', become=False) -> None:
      self.playbook = playbook
      self.config_path = config_path
      self.tag = tag
      self.become = "--ask-become-pass" if become else ""

  def __setattr__(self, name, value) -> None:
    if name == 'config_path':
      self.__dict__[name] = '@' + str(value)
      return
    self.__dict__[name] = value

  def run(self) -> None:
    command = [
        'ANSIBLE_FORCE_COLOR=true',
        'ansible-pull',
        '--extra-vars',
        self.config_path,
        '-U',
        self.repository,
        self.playbook,
        '-C',
        self.tag,
        self.become
    ]
    os.system(" ".join(command))
