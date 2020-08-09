import warnings
from collections import defaultdict
from typing import Optional, Set, Union

from astroid import scoped_nodes
from astroid.node_classes import Import, ImportFrom

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker

from pylint_forbidden_imports.modules import (
    get_top_package_name,
    get_values_from_dunder_all,
    is_submodule,
    DunderAllNotFound,
)


class EncapsulatedModules(BaseChecker):
    """This checked verifies if imports are getting only things enumarated in __all__.

    In order to configure it, one has to add an option `encapsulated-modules` to their
    .pylintrc file with a list of modules to protect, e.g. encapsulated_modules=auctions
    """

    __implements__ = IAstroidChecker

    name = "encapsulated-modules"

    MODULE_ENCAPSULATION_VIOLATED = "violated-encapsulation-of-a-module"

    msgs = {
        "C5102": (
            '"%s" must not be imported - it is a private detail of "%s" module.',
            MODULE_ENCAPSULATION_VIOLATED,
            "",
        )
    }
    options = (
        (
            "encapsulated-modules",
            {"default": (), "type": "csv", "metavar": "<modules>", "help": "No help!"},
        ),
        (
            "encapsulated-modules-friendships",
            {"default": (), "type": "csv", "metavar": "<modules>", "help": "No help!"},
        ),
    )

    priority = -1

    def __init__(self, linter=None) -> None:
        super().__init__(linter)
        self._encapsulated_modules: Set[str] = set()
        self._encapsulated_modules_friendships: Dict[str, Set[str]] = defaultdict(set)
        self._current_package: str = ""

    def open(self) -> None:
        self._encapsulated_modules = set(self.config.encapsulated_modules)
        for friendship in self.config.encapsulated_modules_friendships:
            friend, encapsulated = friendship.split("->")
            self._encapsulated_modules_friendships[friend].add(encapsulated)

    def visit_import(self, node: Import) -> None:
        """Check if we do not import submodules outside a protected package.

        e.g. .pylintrc:
        encapsulated-modules=auctions

        files structure
        auctions
        | __init__.py
        └─ domain
          └─ __init__.py

        auctions/__init__.py DOES NOT have `domain` in __all__

        import auctions.domain  # raises a warning outside auctions package
        """
        imported_modules = [name for name, _alias in node.names]
        for imported_module in imported_modules:
            if "." not in imported_module:
                continue
            top_module, imported_name = imported_module.split(".", maxsplit=1)
            self._check_for_encapsulation_violation(node, top_module, {imported_name})

    def visit_module(self, node: scoped_nodes.Module) -> None:
        """Just extract current top-level package name to later use it in checks."""
        self._current_package = get_top_package_name(node)

    def visit_importfrom(self, node: ImportFrom) -> None:
        """Check if we do not import objects absent in __all__ of a protected package."""
        imported_module = node.modname
        imported_names = {name for name, _alias in node.names}
        self._check_for_encapsulation_violation(node, imported_module, imported_names)

    def _check_for_encapsulation_violation(
        self, node: Union[Import, ImportFrom], module_name: str, names: Set[str]
    ) -> None:
        if is_submodule(module_name, self._current_package):
            return  # same top-level package, always allowed

        closest_protected_parent_module = self._get_the_closest_protected_parent_module(
            module_name
        )
        if not closest_protected_parent_module:
            return

        modules_allowed_for_current = self._encapsulated_modules_friendships[self._current_package]
        if closest_protected_parent_module in modules_allowed_for_current:
            # self._current_package is allowed, they are friends <3
            return

        try:
            dunder_all_names = get_values_from_dunder_all(
                node, closest_protected_parent_module
            )
        except DunderAllNotFound:
            warnings.warn(
                "Protected module '{}' does not define __all__".format(
                    closest_protected_parent_module
                )
            )
            return

        forbidden_names = names - dunder_all_names
        for name in forbidden_names:
            self.add_message(
                self.MODULE_ENCAPSULATION_VIOLATED,
                node=node,
                args=(name, closest_protected_parent_module),
            )

    def _get_the_closest_protected_parent_module(
        self, module_name: str
    ) -> Optional[str]:
        protected_parent_modules = [
            package
            for package in self._encapsulated_modules
            if is_submodule(module_name, package)
        ]
        protected_parent_modules.sort(
            key=lambda value: -len(value)
        )  # longest is the closest
        try:
            return protected_parent_modules[0]
        except IndexError:
            return None
