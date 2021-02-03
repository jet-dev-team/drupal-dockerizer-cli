#!/usr/bin/python3
import os
import subprocess
import appdirs
import sys
import yaml
import json
from pprint import pprint
import pathlib
import platform
from contextlib import closing
import socket

writer = sys.stdout.write
sys.tracebacklimit = 0

_PY3_MIN = sys.version_info[:2] >= (3, 6)
_PY_MIN = _PY3_MIN
if not _PY_MIN:
    raise SystemExit('ERROR: Drupal Dockerizer requires a minimum of Python3 version 3.6. Current version: %s' %
                     ''.join(sys.version.splitlines()))

APP_CONFIG_DIR = pathlib.Path(
    appdirs.user_config_dir()).joinpath('drupal_dockerizer')
APP_CONFIG_PATH = APP_CONFIG_DIR.joinpath('config.yml')

# Init config directory.
if not os.path.exists(str(APP_CONFIG_DIR)):
    os.mkdir(str(APP_CONFIG_DIR))

# Init Config File.
if not os.path.exists(str(APP_CONFIG_PATH)):
    file_config = open(str(APP_CONFIG_PATH), 'w')
    yaml.safe_dump({
            'is_check_requirements_tools': False,
            'version': 0.1
        },
        file_config, sort_keys=True
    )
    file_config.close()
    del file_config


# Read app config.
file_config = open(str(APP_CONFIG_PATH), 'r')
APP_CONFIG = dict(yaml.full_load(file_config))
file_config.close()


# Method for check tool that shoud be exist on platform.
def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        raise SystemExit(
            f'ERROR: Drupal Dockerizer requires program {name}\n\r{e}')
    return True

# Check requirements tools that shoud be exist in system.
requirements_tools = [
    'ansible',
    'docker',
    'docker-compose',
    'git'
]
if not APP_CONFIG.get('is_check_requirements_tools'):
    for tool in requirements_tools:
        is_tool(tool)
    # Save result of check to config for perfomance.
    APP_CONFIG['is_check_requirements_tools'] = True
    file_config = open(str(APP_CONFIG_PATH), 'w')
    yaml.dump(APP_CONFIG, file_config, sort_keys=True)
    file_config.close()


TAG = 'pre-release'
CURRENT_DIR = pathlib.Path().absolute()
CONFIG_NAME = '.drupal_dockerizer.yml'
CONFIG_PATH = str(CURRENT_DIR.joinpath(CONFIG_NAME))


def getVars():
    if not os.path.exists(CONFIG_PATH):
        raise FileExistsError('Config not exist. Please run init.\r\n')
    read_config = open(CONFIG_PATH, 'r')
    vars = yaml.full_load(read_config)
    read_config.close()
    return vars


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(3)
        return sock.connect_ex((host, port)) == 0


def getNetworkId():
    ipRange = range(2, 256)
    network_id = 2
    for i in ipRange:
        network_id = i
        ip = f'192.168.{i}.10'
        if not check_socket(ip, 80):
            break
    return network_id


def checkLocalhostPort(port):
    location = not check_socket('127.0.0.1', port)
    if location:
        writer(f'Port {port} is open\r\n')
    else:
        raise ConnectionError(
            f'Port {port} is not open. Please down app on this port or choose another port.')


def init(args):
    if '-h' in args:
        writer("""help for Drupal Dockerizer configuration init.
    --solr=<version>            availible version: 4, 5, 6, 7, 8
    --solr-configs=<path>       path to solr configs
    --memcache                  install memcache
    --adminer                   install adminer
    --php=<version>             choose phpversion
    --drush_version=<version>   choose drush version
    --network                   use networking for containers, using by default fo Linux system
    --ssl-cert=<path>           path to ssl certeficate
    --ssl-key=<path>            path to ssl certeficate private key
    \r\n
    To see more options visit https://github.com/jet-dev-team/drupal-dockerizer\r\n""")
        sys.exit(0)

    if not os.path.exists(CURRENT_DIR.joinpath('index.php')):
        writer(
            'Please run Drupal dockerizer from drupal dir where placed index.php file.')
        sys.exit(0)

    drupal_root_dir = CURRENT_DIR.parent
    CONFIG_PATH = drupal_root_dir.joinpath(CONFIG_NAME)

    if os.path.exists(CONFIG_PATH):
        writer(f'Config exist. Please run `drupal-dockerizer up` or remove config and run init again. \n\r'
               f'Config placed in {str(pathlib.Path().absolute().joinpath(CONFIG_PATH))}')
        sys.exit(0)
    user_uid = os.getuid()

    project_name = CURRENT_DIR.parts[-2]

    domain_name = project_name + '.devel'
    drupal_web_root = CURRENT_DIR.parts[-1]
    drupal_files_dir = (CURRENT_DIR
                        .joinpath('sites')
                        .joinpath('default')
                        .joinpath('files')
                        )
    phpversion = '7.4-develop'
    solr = False
    solr_version = 4
    memcache = False
    install_adminer = False
    advanced_networking = False
    solr_configs_path = ''
    drush_version = 8
    drush_commands = ['cc drush', 'cr', 'cron']
    custom_drupal_settings = """if (file_exists($app_root . '/' . $site_path . '/settings.local.php')) {
    include $app_root . '/' . $site_path . '/settings.local.php';
  }
  """
    ssl_cert_path = False
    ssl_key_path = False
    for arg in args:
        if '--solr' in arg.split('='):
            solr = True
            solr_version = arg.split('=')[1]
            drush_commands.append('sapi-r')
            drush_commands.append('sapi-i')
        if '--solr-configs' in arg.split('='):
            solr_configs_path = os.path.abspath(arg.split('=')[1])
        if '--php' in arg.split('='):
            phpversion = arg.split('=')[1]
        if '--memcache' == arg:
            memcache = True
        if '--adminer' == arg:
            install_adminer = True
        if '--drush_version' in arg.split('='):
            drush_version = arg.split('=')[1]
        if '--network' in args:
            advanced_networking = True
        if '--ssl-cert' in arg.split('='):
            ssl_cert_path = arg.split('=')[1]
        if '--ssl-key' in arg.split('='):
            ssl_key_path = arg.split('=')[1]

    network_id = 2
    port = 80
    xdebug_enviroment = 'remote_enable=1 remote_connect_back=0 remote_host=10.254.254.254 remote_port=9000 show_error_trace=0 show_local_vars=1 remote_autostart=1 show_exception_trace=0 idekey=VSCODE'
    debug_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Listen for XDebug",
                "type": "php",
                "request": "launch",
                "pathMappings": {
                    "/var/www": "${workspaceFolder}"
                },
                "port": 9000,
                "xdebugSettings": {
                    "show_hidden": 1,
                    "max_data": -1,
                    "max_depth": 2,
                    "max_children": 100,
                }
            },
        ]
    }
    if (platform.system() == 'Linux' or advanced_networking):
        advanced_networking = True
        network_id = getNetworkId()
        xdebug_enviroment = f'remote_enable=1 remote_connect_back=1 remote_port=9000 remote_host=192.168.{network_id}.1 show_error_trace=0 show_local_vars=1 remote_autostart=1 show_exception_trace=0 idekey=VSCODE'
        debug_config["configurations"][0]["hostname"] = f"192.168.{network_id}.1"
    else:
        checkLocalhostPort(port)

    result = {
        'user_uid': user_uid,
        'compose_project_name': project_name,
        'docker_runtime_dir': str(project_name),
        'drupal_root_dir': str(drupal_root_dir),
        'drupal_web_root': str(drupal_web_root),
        'drupal_files_dir': str(drupal_files_dir),
        'advanced_networking': advanced_networking,
        'network_id': network_id,
        'domain_name': domain_name,
        'xdebug_enviroment': xdebug_enviroment,
        'solr': solr,
        'solr_version': int(solr_version),
        'solr_configs_path': solr_configs_path,
        'memcache': memcache,
        'install_adminer': install_adminer,
        'drush_commands': drush_commands,
        'drush_version': drush_version,
        'custom_drupal_settings': custom_drupal_settings,
        'phpversion': phpversion
    }
    if ssl_cert_path and ssl_key_path:
        result['ssl_cert_path'] = str(os.path.abspath(ssl_cert_path))
        result['ssl_key_path'] = str(os.path.abspath(ssl_key_path))
        result['ssl_enabled'] = True
    writer('Config generated with vars:\r\n')
    pprint(result)

    vscode_dir = drupal_root_dir.joinpath('.vscode')
    if not os.path.exists(str(vscode_dir)):
        os.mkdir(str(vscode_dir))
    file_write = open(str(vscode_dir.joinpath('launch.json')), 'w')
    json.dump(debug_config, file_write, indent=2)
    file_write.close()

    file_write = open(CONFIG_PATH, 'w')
    yaml.dump(result, file_write, sort_keys=True)
    file_write.close()


def pull(playbook_name, become=False):
    become = "--ask-become-pass" if become else ""
    os.system(f'ANSIBLE_FORCE_COLOR=true ansible-pull '
              f'--extra-vars @{CONFIG_PATH} '
              f'-U https://github.com/jet-dev-team/drupal-dockerizer.git '
              f'{playbook_name} '
              f'-C {TAG} {become}'
              )


def run_drush_command(command=''):
    vars = getVars()
    container = f"{vars.get('compose_project_name')}-{vars.get('phpversion')}"
    os.system(f'docker exec  --interactive --tty {container} drush {command}')


def check_db_parametrs(args):
    vars = getVars()
    if not 'db_dump_path' in vars and len(args) < args.index('import-db') + 1:
        writer('Please provide path to database dump.\r\n')
        sys.exit(0)
    if len(args) > args.index('import-db') + 1:
        if not args[args.index('import-db') + 1].endswith('sql'):
            writer('Please extract you database dump.\r\n')
            sys.exit(0)
    if len(args) > args.index('import-db') + 1:
        if not os.path.abspath(args[args.index('import-db') + 1]):
            writer(
                f"Database dump does not exist in {args[args.index('import-db') + 1]}\r\n")
            sys.exit(0)
        vars['db_dump_path'] = os.path.abspath(
            args[args.index('import-db') + 1])
        vars = yaml.dump(vars, open(CONFIG_PATH, 'w'))
        return
    writer('Try to get path to database dump from config.\r\n')


def composer(command, composerVersion='latest'):
    os.system(f'docker run --rm --interactive --tty '
              f'--volume $PWD:/app '
              f'--user $(id -u):$(id -g) '
              f'composer:{composerVersion} --no-cache --ignore-platform-reqs {command}')


def up(force=False):
    vars = getVars()
    if not 'projects' in APP_CONFIG.keys():
        APP_CONFIG['projects'] = {}
    if vars.get('compose_project_name') in list(APP_CONFIG['projects'].keys()) and not force:
        pull('up.yml')
        sys.exit(0)
    pull('main.yml', become=True)
    APP_CONFIG['projects'][vars.get('compose_project_name')] = {
        'project': vars.get('compose_project_name'),
        'root_dir': vars.get('drupal_root_dir'),
        'domain': vars.get('domain_name') if vars.get('advanced_networking') else 'http://localhost',
        'status': 'up',
    }
    file_config = open(str(APP_CONFIG_PATH), 'w')
    yaml.dump(APP_CONFIG, file_config, sort_keys=True)
    file_config.close()
    if vars.get('advanced_networking'):
        url = f"http{''}://{vars.get('domain_name')}"
        writer(f'Project is up. Site up in {url}\r\n')
    else:
        writer(f'Project is up. Site up in http://localhost\r\n')


def stop():
    vars = getVars()
    pull('stop.yml')
    APP_CONFIG['projects'][vars.get('compose_project_name')]['status'] = 'stop'
    file_config = open(str(APP_CONFIG_PATH), 'w')
    yaml.dump(APP_CONFIG, file_config, sort_keys=True)
    file_config.close()
    writer(f'Project {vars.get("compose_project_name")} stoped\r\n')


def down():
    vars = getVars()
    pull('reset.yml', become=True)
    del APP_CONFIG['projects'][vars.get('compose_project_name')]
    file_config = open(str(APP_CONFIG_PATH), 'w')
    yaml.dump(APP_CONFIG, file_config, sort_keys=True)
    file_config.close()


if __name__ == '__main__':
    args = sys.argv[1::]
    if len(args) == 0 or '-h' == args[0] or '--help' in args:
        writer(
            """Availible command for Drupal Dockerizer.
    init                        initializate config for project,
                                    add -h to see more options.
    up                          up docker enviroment, it asking sudo(BECOME) password on first run,
                                    add --force to rebuild containers(database data is safe).
    stop                        stop containers
    down                        remove all containers and runtime(databases, serch indexes, logs, etc.),
                                    it asking sudo(BECOME) password
    drush-commands              execute drush commands from config in container
    import-db <path>            import database from sql file
    drush <command>             execute drush command in drupal container
    composer:<vesion>           Run composer command inside official composer docker container`s
                                  - availible versions:
                                    composer, composer:1, composer:2, composer:latest
    drupal-standart-install     install and up standart drupal project
    projects                    list launched projects
    project <name> <command>    run drupal-dockerizer command for project\r\n
    To see more options visit https://github.com/jet-dev-team/drupal-dockerizer\r\n""")
        sys.exit(0)

    if 'init' in args:
        init(args)
        sys.exit(0)

    if 'drupal-standart-install' in args:
        # Setup demo project.
        composer('create-project drupal/recommended-project drupal-project')
        os.chdir(CURRENT_DIR.joinpath('drupal-project'))
        composer('require drush/drush')
        os.chdir(CURRENT_DIR.joinpath('drupal-project').joinpath('web'))
        CURRENT_DIR = CURRENT_DIR.joinpath('drupal-project').joinpath('web')
        CONFIG_PATH = CURRENT_DIR.parent.joinpath(CONFIG_NAME)
        init(args)
        up()
        run_drush_command('si --account-pass=admin --site-name=Drupal -y')
        pull('run-drush-commands.yml')
        vars = getVars()
        if vars.get('advanced_networking'):
            url = f"http{''}://{vars.get('domain_name')}"
            writer(f'Project is up. Site up in {url}\r\n')
        else:
            writer(f'Project is up. Site up in http://localhost\r\n')
        sys.exit(0)

    if 'projects' in args:
        projects = APP_CONFIG.get('projects')
        writer('Status projects:\r\n')
        for project in projects.keys():
            writer(f'{project} is {projects[project].get("status")}, ')
            writer(f'domain {projects[project].get("domain")}\r\n')
        sys.exit(0)

    if 'project' in args:
        if len(args) > args.index('project') + 1:
            project = args[args.index('project') + 1]
            if len(args) == args.index('project') + 2 and project in APP_CONFIG['projects'].keys():
                writer(f'Project {project} status.\r\n')
                pprint(APP_CONFIG['projects'][project])
                sys.exit(0)
            if project in APP_CONFIG['projects'].keys():
                project_params = APP_CONFIG['projects'][project]
                CURRENT_DIR = pathlib.Path(project_params.get('root_dir'))
                CONFIG_PATH = CURRENT_DIR.joinpath(CONFIG_NAME)
            else:
                writer(f'Project {project} does not up.\r\n')
                sys.exit(0)
        else:
            writer(f'Please provide project name and command.\r\n')
            sys.exit(0)

    # Run composer command inside official composer docker container.
    if len(list(filter(lambda x: 'composer' in x, args))) > 0:
        composerArg = list(filter(lambda x: 'composer' in x, args))[0]
        composerVersion = 'latest'
        if composerArg.find(':') > -1:
            composerVersion = composerArg.split(':')[1]
        if len(args) > args.index(composerArg) + 1:
            command = " ".join(args[args.index(composerArg) + 1::])
            composer(command, composerVersion)
        else:
            writer('Provide composer command\r\n')
            sys.exit(0)
        sys.exit(0)

    # Try to find config
    if not os.path.exists(CONFIG_PATH):
        folder = CURRENT_DIR.parent
        for i in range(len(folder.parts) + 1):
            if os.path.exists(folder.joinpath(CONFIG_NAME)):
                CONFIG_PATH = str(folder.joinpath(CONFIG_NAME))
                break
            folder = folder.parent
        if not os.path.exists(CONFIG_PATH):
            writer('Can`t find config. Please ensure that config exist in project.\r\n')
            sys.exit(0)

    if 'drush' in args:
        if len(args) > args.index('drush') + 1:
            commands = " ".join(args[args.index('drush') + 1::])
            run_drush_command(commands)
        else:
            run_drush_command()
        sys.exit(0)

    if 'up' in args:
        if '--force' in args:
            up(force=True)
            sys.exit(0)
        up()
        sys.exit(0)

    if 'down' in args:
        down()
        sys.exit(0)

    if 'stop' in args:
        stop()
        sys.exit(0)

    if 'import-db' in args:
        check_db_parametrs(args)
        pull('db.yml')
        sys.exit(0)

    if 'drush-commands' in args:
        pull('run-drush-commands.yml')
        sys.exit(0)

    writer('Command not availible. Please run --help for see availible commands.\r\n')
    sys.exit(0)
