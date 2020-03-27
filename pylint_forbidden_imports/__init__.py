"""Entry file for pylint to register checkers."""
from pylint.lint import PyLinter

from pylint_forbidden_imports.encapsulated_modules import EncapsulatedModules
from pylint_forbidden_imports.forbidden_imports import ForbiddenImports


def register(linter: PyLinter) -> None:
    """Register checkers with pylint."""
    linter.register_checker(ForbiddenImports(linter))
    linter.register_checker(EncapsulatedModules(linter))
