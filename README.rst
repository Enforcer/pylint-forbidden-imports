How does it work?
===============
...

Why?
===============
To enforce certain conventions project-wide in an automatic way, without having to watch for it during code review.

How to use it?
===============
After installing a package just run `pylint`, appending `pylint_forbidden_imports` to your `--load-plugins` option.

An example::

    pylint my_cool_project --load-plugins=pylint_forbidden_imports

or append it to your `pylintrc` file::

    [MASTER]
    load-plugins=pylint_forbidden_imports


Development
===========
Install dev dependencies: ::
	pip install -e .[dev]
