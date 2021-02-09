# Drupal Dockerizer CLI.

## Prepare instalation

This project require next tools:
- git [insruction for install](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- ansible [insruction for install](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)
- docker [insruction for install](https://docs.docker.com/get-docker/)
- docker-compose [insruction for install](https://docs.docker.com/compose/install/)

After install docker need add your user to docker group and logout/login to you system, see [instruction](https://docs.docker.com/engine/install/linux-postinstall/)
## How to use

Go to your drupal project directory, navigate to the `web` directory where the` index.php` file is located, and run `drupal-dockerizer init` in terminal to create a drupal dockerizer configuration placed in the root directory of the drupal project named `.drupal -dockerizer.yml`. Now you can change the configuration in this file. For more information see [Drupal Dockerizer Repository](https://github.com/jet-dev-team/drupal-dockerizer)

To create docker containers, run `drupal-dockerizer up` inside any directory in your drupal project. After running this command, you can work with drupal, for example, you can install drupal site by running command `drupal-dockerizer drush si --account-pass = admin --site-name = Drupal -y`

To stop docker containers run `drupal-dockerizer stop`. This command just stop containers, all data in database, solr, memcache, php is safe at this point.

Run `drupal-dockerizer down` to remove all data and contexts. This command removes the entire volumes created by Drupal Dockerizer and removes all containers.

You can run any drush command in your project by running `drupal-dockerizer drush <drush-command>` when containers are running.

If you don't have php or composer on your system, you can install drupal project using composer container. To use composer run `drupal-dockerizer composer <composer-command>`
## Build
### Manualy build pip package
Create python virual enviroment and activate by [instruction](https://docs.python.org/3/tutorial/venv.html).
Run `pip install -r requirements.txt` for install dependency

Command for build pip package: `python3 setup.py sdist bdist_wheel`
Go to `dist` folder now you can install package to your system by run `pip intall drupal_dockerizer-*.whl`

### Build package in docker:

Buid image: `docker build -t drupal_dockerizer .`

Copy created packages from container:
`docker run --rm --volume $PWD:/app --user $(id -u):$(id -g) drupal_dockerizer cp -R /code/dist /app/drupal_dockerizer_package`

## Install
Go to folder with builded package and run `pip intall drupal_dockerizer-*.whl`
## Development

Create python virual enviroment and activate by [instruction](https://docs.python.org/3/tutorial/venv.html).

Run `pip install --editable .` for install drupal_dockerizer to current enviroment.

Now you can edit files in folder drupal_dockerizer and use command `drupal-dockerizer` to see results from terminal or debug.

## Uninstall
For uninstall package run `pip uninstall drupal_dockerizer`
