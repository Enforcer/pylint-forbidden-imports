How does it work?
=================
This plugin inspects import statements for configured packages. Both checkers are using powerful AST analysis techniques, standard for pylint.

Status
======
This emerged as a standalone experimentation during development of `the Clean Architecture example project`_

Why?
====
To enforce certain conventions project-wide in an automatic way, without having to watch for it during code review. For example: "we do not import anything from `foo` in `bar`." or "we must not import anything from guts of the package `baz`, only what's kept in it's top-level __init__.py `__all__` list".

How to use it?
==============
After installing a package just run `pylint`, appending `pylint_forbidden_imports` to your `--load-plugins` option.

An example::

    pylint my_cool_project --load-plugins=pylint_forbidden_imports

or append it to your `pylintrc` file::

    [MASTER]
    load-plugins=pylint_forbidden_imports


Then, you have to configure the plugin. Example for `.pylintrc`::

    [ARBITRARY-SECTION-NAME]
    encapsulated-modules=auctions,payments
    encapsulated-modules-friendships=auctions_infrastructure->auctions
    allowed-modules-dependencies=auctions_infrastructure->auctions,
                                 main->*,
                                 *->foundation,

All settings are comma-separated. 

`encapsulated-modules` - checks whether we import from it only things kept in top-level __init__.py.
`encapsulated-modules-friendships` - allows for creating exceptions to that rule for "friend" packages.
`allowed-modules-dependencies` - defines which packages are allowed to be imported from certain packages. Asterisk (*) is a wildcard - `main->*`  means main package can import anything while `*->foundation` means that any package can import from foundation.
If a certain package does not appear at least once, no rules are enforced.

Development
===========
Install dev dependencies: ::
    pip install -e .[dev]

.. _the Clean Architecture example project: https://github.com/Enforcer/clean-architecture
