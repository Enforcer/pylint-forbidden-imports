from collections import defaultdict
from typing import Dict, Set

from astroid import scoped_nodes
from astroid.node_classes import Import, ImportFrom

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker

from pylint_forbidden_imports.modules import (
    get_top_package_from_qualified_path,
    get_top_package_name,
)


class ForbiddenImports(BaseChecker):
    """This checker implements Java-like package protection.

    To use it, one has to define `allowed-modules-dependencies` in their .pylintrc, e.g.

    allowed-modules-dependencies=mypackage->myotherpackage,  # mypackage can use myotherpackage
                                 *->mypackage,               # everything can use mypackage
                                 assembly->*                 # assembly may use everything

    In other words, one defines a permissions graph using edges.

    If a package appears at least once in definitions list, it is considered to be forbidden
    unless explicitly allowed later.
    """

    __implements__ = IAstroidChecker

    name = "forbidden-imports"

    MODULE_CANNOT_BE_IMPORTED_HERE = "this-package-is-forbidden-to-be-imported-here"

    msgs = {
        "C5101": (
            '"%s" must not be imported by "%s".',
            MODULE_CANNOT_BE_IMPORTED_HERE,
            "",
        ),
    }
    options = (
        (
            "allowed-modules-dependencies",
            {"default": (), "type": "csv", "metavar": "<modules>", "help": "No help!"},
        ),
    )

    priority = -1

    def __init__(self, linter=None) -> None:
        super().__init__(linter)
        self._allowed_package_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._all_packages_with_dependencies: Set[str] = set()
        self._imported_packages: Set[str] = set()
        self._dependecies_always_allowed: Set[str] = set()

    def open(self) -> None:
        dependents_with_wildcard: Set[str] = set()

        for entry in self.config.allowed_modules_dependencies:
            dependent, dependency = entry.split("->")
            if dependency == "*":
                dependents_with_wildcard.add(dependent)
                continue

            if dependent == "*":
                self._dependecies_always_allowed.add(dependency)
                continue

            self._allowed_package_dependencies[dependent].add(dependency)
            self._all_packages_with_dependencies.update([dependent, dependency])

        for dependent in dependents_with_wildcard:
            self._allowed_package_dependencies[dependent].update(
                self._all_packages_with_dependencies
            )

    def leave_module(self, node: scoped_nodes.Module) -> None:
        """Perform checks using gathered imports."""
        current_package_name = get_top_package_name(node)
        # omitting packages that have no restrictions (e.g. stdlib, 3rd party etc)
        imported_packages_that_have_any_rules = (
            self._imported_packages
            & self._all_packages_with_dependencies - {current_package_name}
        )

        allowed_package_dependencies = self._allowed_package_dependencies[
            current_package_name
        ]
        forbidden_packages = (
            imported_packages_that_have_any_rules
            - allowed_package_dependencies
            - self._dependecies_always_allowed
        )

        for package_name in forbidden_packages:
            self.add_message(
                self.MODULE_CANNOT_BE_IMPORTED_HERE,
                node=node,
                args=(package_name, current_package_name),
            )

        self._imported_packages.clear()

    def visit_import(self, node: Import) -> None:
        """Just record what packages has been imported in the current module."""
        imported_packages = [
            get_top_package_from_qualified_path(name) for name, _alias in node.names
        ]
        self._imported_packages.update(imported_packages)

    def visit_importfrom(self, node: ImportFrom) -> None:
        """Just record what packages one imported from in the current module."""
        self._imported_packages.add(get_top_package_from_qualified_path(node.modname))
