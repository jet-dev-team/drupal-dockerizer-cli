# Drupal Dockerizer CLI.

## Build
### Manualy build pip package
Create python virual enviroment and activate by [instruction](https://docs.python.org/3/tutorial/venv.html).
Run `pip install -r requirements.txt` for install dependency

Command for build pip package: `python3 setup.py sdist bdist_wheel`
Go to `dist` folder now you can install package to your system by run `pip intall drupal_dockerizer-*.whl`

## Build package in docker:

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
