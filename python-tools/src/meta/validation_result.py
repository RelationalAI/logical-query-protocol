"""Validation result data structures for grammar validation."""

from dataclasses import dataclass, field as dataclass_field
from typing import List, Optional


@dataclass
class ValidationError:
    """A single validation error."""
    category: str  # "completeness", "field_coverage", "oneof_coverage", "soundness"
    message: str
    proto_type: Optional[str] = None
    rule_name: Optional[str] = None


@dataclass
class ValidationWarning:
    """A single validation warning."""
    category: str
    message: str
    proto_type: Optional[str] = None
    rule_name: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of grammar validation."""
    errors: List[ValidationError] = dataclass_field(default_factory=list)
    warnings: List[ValidationWarning] = dataclass_field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings don't affect validity)."""
        return len(self.errors) == 0

    @property
    def has_any_issues(self) -> bool:
        """True if there are any errors or warnings."""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def add_error(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.errors.append(ValidationError(category, message, proto_type, rule_name))

    def add_warning(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.warnings.append(ValidationWarning(category, message, proto_type, rule_name))

    def summary(self) -> str:
        """Return a summary of validation results."""
        lines = []
        if self.is_valid:
            lines.append("Validation PASSED")
        else:
            lines.append("Validation FAILED")

        error_count = len(self.errors)
        warning_count = len(self.warnings)
        lines.append(f"  {error_count} error(s), {warning_count} warning(s)")

        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  [{error.category}] {error.message}")

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  [{warning.category}] {warning.message}")

        return "\n".join(lines)
