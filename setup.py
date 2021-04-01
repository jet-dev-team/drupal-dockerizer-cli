import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="drupal_dockerizer",
    entry_points="""
        [console_scripts]
        drupal-dockerizer=drupal_dockerizer.cli:cli
    """,
    version="0.0.4",
    author="Vladislav Sadretdinov",
    author_email="svicervlad@gmail.com",
    description="Cli tool for up drupal projects in docker containers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jet-dev-team/drupal-dockerizer-cli",
    include_package_data=True,
    install_requires=["Click", "appdirs", "PyYAML", "wheel"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
