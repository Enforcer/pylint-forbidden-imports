from collections import defaultdict
from typing import Dict, Set

import astroid
from astroid import scoped_nodes
from astroid.node_classes import Import, ImportFrom

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class ForbiddenImports(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'forbidden-imports'

    MODULE_CANNOT_BE_IMPORTED_HERE = 'this-package-is-forbidden-to-be-imported-here'

    msgs = {
        'C5101': ('"%s" must not be imported by "%s".', MODULE_CANNOT_BE_IMPORTED_HERE, ''),
    }
    options = (
        (
            "allowed-modules-dependencies",
            {
                "default": (),
                "type": "csv",
                "metavar": "<modules>",
                "help": "No help!"
            }
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
            dependent, dependency = entry.split('->')
            if dependency == '*':
                dependents_with_wildcard.add(dependent)
                continue
            elif dependent == '*':
                self._dependecies_always_allowed.add(dependency)
                continue

            self._allowed_package_dependencies[dependent].add(dependency)
            self._all_packages_with_dependencies.update([dependent, dependency])

        for dependent in dependents_with_wildcard:
            self._allowed_package_dependencies[dependent].update(self._all_packages_with_dependencies)

    def _get_top_module_name(self, node: scoped_nodes.Module) -> str:
        return self._get_top_package_from_qualified_path(node.name)

    def _get_top_package_from_qualified_path(self, full_module_name: str) -> str:
        return full_module_name.split('.')[0]        

    def leave_module(self, node: scoped_nodes.Module) -> None:
        current_package_name = self._get_top_module_name(node)
        # omitting packages that have no restrictions (e.g. stdlib, 3rd party etc)
        imported_packages_that_have_any_rules = (
            self._imported_packages & self._all_packages_with_dependencies - {current_package_name}
        )

        allowed_package_dependencies = self._allowed_package_dependencies[current_package_name]
        forbidden_packages = (
            imported_packages_that_have_any_rules - allowed_package_dependencies - self._dependecies_always_allowed
        )

        for package_name in forbidden_packages:
            self.add_message(
                self.MODULE_CANNOT_BE_IMPORTED_HERE,
                node=node,
                args=(package_name, current_package_name)
            )

        self._imported_packages.clear()

    def visit_import(self, node: Import) -> None:
        imported_packages = [self._get_top_package_from_qualified_path(name) for name, _alias in node.names]
        self._imported_packages.update(imported_packages)

    def visit_importfrom(self, node: ImportFrom) -> None:
        self._imported_packages.add(self._get_top_package_from_qualified_path(node.modname))


def register(linter):
    linter.register_checker(ForbiddenImports(linter))
