from setuptools import setup

with open("README.rst") as readme_file:
    long_description = readme_file.read()

setup(
    name="pylint_forbidden_imports",
    packages=["pylint_forbidden_imports"],
    version="1.0.0",
    description="Plugin for PyLint that checks if we import from permitted modules",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Sebastian Buczyński",
    url="https://github.com/Enforcer/pylint_forbidden_imports",
    download_url="https://github.com/Enforcer/pylint_forbidden_imports/archive/1.0.0.tar.gz",
    keywords=["pylint", "imports"],
    classifiers=[],
    include_package_data=True,
    extras_require={"dev": {"pytest", "pylint", "black"}},
)
