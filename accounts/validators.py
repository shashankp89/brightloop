import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    min_length = 9

    def validate(self, password, user=None):
        problems = []
        if len(password) < self.min_length:
            problems.append("be more than 8 characters long")
        if not re.search(r"[A-Z]", password):
            problems.append("contain an uppercase letter")
        if not re.search(r"[a-z]", password):
            problems.append("contain a lowercase letter")
        if not re.search(r"[^A-Za-z0-9]", password):
            problems.append("contain a special character")
        if problems:
            raise ValidationError(
                "Password must " + ", ".join(problems) + ".",
                code="password_weak",
            )

    def get_help_text(self):
        return (
            "Use more than 8 characters, with an uppercase letter, "
            "a lowercase letter and a special character."
        )
