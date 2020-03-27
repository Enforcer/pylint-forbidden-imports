"""Functions to provide extra operations on modules nodes."""
from typing import Set, Union

from astroid import scoped_nodes
from astroid.node_classes import Import, ImportFrom


def get_top_package_name(node: scoped_nodes.Module) -> str:
    """Extracts top-level package name from a given Module node."""
    return get_top_package_from_qualified_path(node.name)


def get_top_package_from_qualified_path(full_module_name: str) -> str:
    """Gets top-level package name from qualified (dotted) module name."""
    return full_module_name.split(".")[0]


def is_submodule(potential_submodule: str, package: str) -> None:
    """Checks if a module given with full qualified path is a submodule of the package."""
    parts = potential_submodule.split(".")
    for ending_idx in range(1, len(parts) + 1):
        combination = ".".join(parts[:ending_idx])
        if combination == package:
            return True
    return False


def get_values_from_dunder_all(
    node: Union[Import, ImportFrom], module_name: str
) -> Set[str]:
    """Extracts all names given in module's __all__ attribute."""
    module = node.do_import_module(module_name)
    _module, dunder_all = module.lookup("__all__")
    if not dunder_all:
        raise DunderAllNotFound
    dunder_all_assignment_node = dunder_all[0].parent
    return {element.value for element in dunder_all_assignment_node.value.elts}


class DunderAllNotFound(AttributeError):
    """Indicates that module is missing __all__ attribute."""
