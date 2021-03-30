#!/usr/bin/python3
import sys
from sys import platform
import json
from pprint import pprint
import os
import platform
import click
from pathlib import Path
from drupal_dockerizer import AppConfig, check_tool, Pull, DockerizerConfig, findConfigPath, getNetworkId, checkLocalhostPort, check_socket
from drupal_dockerizer.dockerizer_config import CONFIG_NAME

sys.tracebacklimit = 0

_PY3_MIN = sys.version_info[:2] >= (3, 6)
_PY_MIN = _PY3_MIN
if not _PY_MIN:
    raise SystemExit('ERROR: Drupal Dockerizer requires a minimum of Python3 version 3.6. Current version: %s' %
                     ''.join(sys.version.splitlines()))

app_config = AppConfig()
tag = '2.0.0'
requirements_tools = ['docker', 'docker-compose', 'git']

if not app_config.data['is_check_requirements_tools']:
    for tool in requirements_tools:
        check_tool(tool)
    app_config.data['is_check_requirements_tools'] = True
    app_config.save()

CURRENT_DIR = Path().absolute()


@click.group()
def cli():
    """
    Drupal Dockerizer Cli
    """
    pass


@cli.command('init')
@click.option('--php', help='php version', type=click.Choice(['7.1-develop', '7.2-develop', '7.3-develop', '7.4-develop', '8.0-develop', '7.1-production', '7.2-production', '7.3-production', '7.4-production', '8.0-production']))
@click.option('--solr', help='solr version', type=click.Choice(['4', '5', '6', '7', '8']))
@click.option('--solr-configs', type=click.Path(exists=True, resolve_path=True), help='path to solr configs')
@click.option('--memcache', is_flag=True, help='install memcache')
@click.option('--adminer', is_flag=True, help='install adminer')
@click.option('--network/--no-network', default=True, help='use networking for containers, only for Linux systems')
@click.option('--ssl-cert', type=click.Path(exists=True, resolve_path=True), help='path to ssl certeficate')
@click.option('--ssl-key', type=click.Path(exists=True, resolve_path=True), help='path to ssl private key')
@click.option('--vscode-ext/--no-vscode-ext', default=True, help='generate vscode launch.json file for setup php debug')
def init(php, solr, solr_configs, memcache, adminer, network, ssl_cert, ssl_key, vscode_ext):
    """
    Initializate config for project
    """
    if not os.path.exists(CURRENT_DIR.joinpath('index.php')):
        click.echo(
            'Please run Drupal dockerizer from drupal dir where placed index.php file.')
        exit()
    drupal_root_dir = CURRENT_DIR.parent
    conf_path = drupal_root_dir.joinpath(CONFIG_NAME)
    if os.path.exists(conf_path):
        question = click.confirm(
            'This command will replace exist config. Genarete new config and replace?')
        if question is False:
            exit()
    conf = DockerizerConfig(CURRENT_DIR, conf_path, load=False)
    if ssl_cert and ssl_key:
        conf.data['ssl_cert_path'] = str(os.path.abspath(ssl_cert))
        conf.data['ssl_key_path'] = str(os.path.abspath(ssl_key))
        conf.data['ssl_enabled'] = True

    if php:
        conf.data['phpversion'] = php
    conf.data['user_uid'] = os.getuid()
    conf.data['user_gid'] = os.getgid()
    # Fix for mac os platform
    if platform == "darwin":
         conf.data['user_gid'] = 201
    conf.data['drupal_root_dir'] = str(drupal_root_dir)
    conf.data['compose_project_name'] = str(CURRENT_DIR.parts[-2])
    conf.data['docker_runtime_dir'] = conf.data['compose_project_name']
    conf.data['domain_name'] = conf.data['compose_project_name'] + '.devel'
    conf.data['drupal_web_root'] = str(CURRENT_DIR.parts[-1])
    conf.data['drupal_files_dir'] = str(CURRENT_DIR
                                        .joinpath('sites')
                                        .joinpath('default')
                                        .joinpath('files')
                                        )
    if solr:
        conf.data['solr'] = True
        conf.data['solr_version'] = int(solr)
        conf.data['solr_configs_path'] = solr_configs

    conf.data['memcache'] = memcache
    conf.data['install_adminer'] = adminer

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
    conf.data['xdebug_enviroment'] = 'remote_enable=1 remote_connect_back=0 remote_host=10.254.254.254 remote_port=9000 show_error_trace=0 show_local_vars=1 remote_autostart=1 show_exception_trace=0 idekey=VSCODE'
    if platform.system() == 'Linux' and network:
        conf.data['advanced_networking'] = True
        conf.data['network_id'] = getNetworkId()
        conf.data[
            'xdebug_enviroment'] = f'remote_enable=1 remote_connect_back=1 remote_port=9000 remote_host=192.168.{conf.data["network_id"]}.1 show_error_trace=0 show_local_vars=1 remote_autostart=1 show_exception_trace=0 idekey=VSCODE'
        debug_config["configurations"][0]["hostname"] = f"192.168.{conf.data['network_id']}.1"
    else:
        conf.data['advanced_networking'] = False

    conf.save()

    if vscode_ext:
        vscode_dir = drupal_root_dir.joinpath('.vscode')
        if not os.path.exists(str(vscode_dir)):
            os.mkdir(str(vscode_dir))
        file_write = open(str(vscode_dir.joinpath('launch.json')), 'w')
        json.dump(debug_config, file_write, indent=2)
        file_write.close()
        click.echo(
            f'Debug settings for vscode generate on path {str(vscode_dir.joinpath("launch.json"))}')
    click.echo('Config generated with settings:')
    pprint(conf.data)


def __up_project(force=False, conf_path=None):
    '''
    Up docker enviroment, ask sudo(BECOME) password on first run
    '''
    if not conf_path:
        conf_path = findConfigPath(CURRENT_DIR)
    conf = DockerizerConfig(CURRENT_DIR, conf_path)
    if not force and conf.data['compose_project_name'] in list(app_config.data['projects'].keys()):
        pl = Pull('up.yml', conf_path, tag)
    else:
        pl = Pull('main.yml', conf_path, tag, become=True)
        app_config.addProject(conf)
    pl.run()
    app_config.save()
    if conf.data['advanced_networking']:
        url = f"http{''}://{conf.data['domain_name']}"
        click.echo(f'Project is up. Site up in {url}')
    else:
        click.echo(f'Project is up. Site up in http://localhost')


@cli.command('up')
@click.option('--force', is_flag=True, help='rebuild conteiners')
def up_project(force):
    '''
    Up docker enviroment, ask sudo(BECOME) password on first run
    '''
    return __up_project(force)


@cli.command('import-db')
@click.argument('filename', type=click.Path(exists=True, resolve_path=True))
def import_db(filename):
    '''
    Import database from sql file
    '''
    conf_path = findConfigPath(CURRENT_DIR)
    conf = DockerizerConfig(CURRENT_DIR, conf_path)
    conf.data['db_dump_path'] = filename
    conf.save()
    pl = Pull('db.yml', conf_path, tag)
    pl.run()


def __down_project(conf_path=None):
    '''
     Remove all containers and runtime(databases, search indexes, logs, etc.), ask sudo(BECOME) password
    '''
    if not conf_path:
        conf_path = findConfigPath(CURRENT_DIR)
    conf = DockerizerConfig(CURRENT_DIR, conf_path)
    pl = Pull('reset.yml', conf_path, tag, become=True)
    pl.run()
    app_config.removeProject(conf)
    app_config.save()
    click.echo(
        f'Project {conf.data["compose_project_name"]} down. All containers data removed.')


@cli.command('down')
def down_project(conf_path=None):
    '''
     Remove all containers and runtime(databases, search indexes, logs, etc.), ask sudo(BECOME) password
    '''
    return __down_project()


def __stop_project(conf_path=None):
    if not conf_path:
        conf_path = findConfigPath(CURRENT_DIR)
    conf = DockerizerConfig(CURRENT_DIR, conf_path)
    pl = Pull('stop.yml', conf_path, tag)
    pl.run()
    app_config.stopProject(conf)
    app_config.save()
    click.echo(f'Project {conf.data["compose_project_name"]} stoped')


@cli.command('stop')
def stop_project():
    '''
    Stop containers
    '''
    return __stop_project()


@cli.command('drush-commands')
def drush_commands(conf_path=None):
    '''
    Execute drush commands from config in container
    '''
    if not conf_path:
        conf_path = findConfigPath(CURRENT_DIR)
    DockerizerConfig(CURRENT_DIR, conf_path)
    pl = Pull('run-drush-commands.yml', conf_path, tag)
    pl.run()
    click.echo(f'Drush commands from config done')


@cli.command('drush', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
def drush(command, conf_path=None):
    '''
    Execute drush command in drupal container
    '''
    if not conf_path:
        conf_path = findConfigPath(CURRENT_DIR)
    conf = DockerizerConfig(CURRENT_DIR, conf_path)
    container = f"{conf.data['compose_project_name']}-{conf.data['phpversion']}"
    os.system(
        f'docker exec  --interactive --tty {container} drush {" ".join(command)}')


@cli.command('composer', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
def composer(command):
    '''
    Run composer inside docker conteiner
    '''
    os.system(f'docker run --rm --interactive --tty '
              f'--volume $PWD:/app '
              f'--user $(id -u):$(id -g) '
              f'composer --no-cache --ignore-platform-reqs {" ".join(command)}')


@cli.command('projects')
def projects():
    '''
    List launched projects
    '''
    projects = app_config.data.get('projects')
    click.echo('Status projects:\r\n')
    for project in projects.keys():
        click.echo(f'{project} is {projects[project].get("status")}, '
                   f'domain {projects[project].get("domain")}\r\n')


@cli.command('project')
@click.argument('project_name')
@click.option('--up', is_flag=True, help='Up docker enviroment')
@click.option('--stop', is_flag=True, help='Stop docker enviroment')
@click.option('--down', is_flag=True, help='Down docker enviroment and remove project data')
def project(project_name, up, stop, down):
    '''
    Control project.
    '''
    if not project_name in list(app_config.data['projects'].keys()):
        click.echo('Proect not found, run "projects" to see list of projects')
    project_data = app_config.data['projects'][project_name]
    project_path = Path(project_data['root_dir'])
    conf_path = str(project_path.joinpath(CONFIG_NAME))
    if up:
        __up_project(conf_path=conf_path)
    elif down:
        __down_project(conf_path=conf_path)
    elif stop:
        __stop_project(conf_path=conf_path)
    else:
        click.echo(f'{project_name} is {project_data["status"]}')


if __name__ == '__main__':
    cli()
