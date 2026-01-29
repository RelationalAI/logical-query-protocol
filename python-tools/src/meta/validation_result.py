"""Validation result data structures for grammar validation."""

from dataclasses import dataclass, field as dataclass_field
from typing import List, Optional


@dataclass
class ValidationIssue:
    """A single validation issue."""
    category: str  # "completeness", "field_coverage", "oneof_coverage", "soundness"
    severity: str  # "error", "warning"
    message: str
    proto_type: Optional[str] = None
    rule_name: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of grammar validation."""
    issues: List[ValidationIssue] = dataclass_field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings are acceptable for some use cases)."""
        return not any(i.severity == "error" for i in self.issues)

    @property
    def has_any_issues(self) -> bool:
        """True if there are any errors or warnings."""
        return len(self.issues) > 0

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add_error(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.issues.append(ValidationIssue(category, "error", message, proto_type, rule_name))
        return None

    def add_warning(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.issues.append(ValidationIssue(category, "warning", message, proto_type, rule_name))
        return None

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
            for issue in self.errors:
                lines.append(f"  [{issue.category}] {issue.message}")

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for issue in self.warnings:
                lines.append(f"  [{issue.category}] {issue.message}")

        return "\n".join(lines)
