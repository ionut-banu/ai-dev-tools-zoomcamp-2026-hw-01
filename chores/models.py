from django.core.exceptions import ValidationError
from django.db import models


class HouseholdMember(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Chore(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    KIND_ONE_OFF = "one_off"
    KIND_RECURRING = "recurring"
    KIND_CHOICES = [
        (KIND_ONE_OFF, "One-off"),
        (KIND_RECURRING, "Recurring"),
    ]

    ASSIGNMENT_MANUAL = "manual"
    ASSIGNMENT_AUTO_ROTATE = "auto_rotate"
    ASSIGNMENT_MODE_CHOICES = [
        (ASSIGNMENT_MANUAL, "Manual"),
        (ASSIGNMENT_AUTO_ROTATE, "Auto-rotate"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    interval_days = models.PositiveIntegerField(null=True, blank=True)
    assignment_mode = models.CharField(
        max_length=15, choices=ASSIGNMENT_MODE_CHOICES
    )
    assignee = models.ForeignKey(
        HouseholdMember,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assigned_chores",
    )
    rotation_pool = models.ManyToManyField(
        HouseholdMember, blank=True, related_name="rotation_chores"
    )
    next_due_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}

        if self.kind == self.KIND_ONE_OFF and self.interval_days is not None:
            errors["interval_days"] = "One-off chores must not have interval_days set."
        elif self.kind == self.KIND_RECURRING and not self.interval_days:
            errors["interval_days"] = "Recurring chores require interval_days >= 1."

        if self.assignment_mode == self.ASSIGNMENT_MANUAL and self.assignee_id is None:
            errors["assignee"] = "Manual assignment requires an assignee."

        # rotation_pool is a many-to-many field, so it can only be inspected
        # once the instance has a primary key. New auto-rotate chores are
        # validated at the form layer instead (see chores/forms.py, Task 3).
        if self.assignment_mode == self.ASSIGNMENT_AUTO_ROTATE and self.pk is not None:
            if self.rotation_pool.count() < 2:
                errors["rotation_pool"] = (
                    "Auto-rotate requires at least 2 members in the rotation pool."
                )

        if errors:
            raise ValidationError(errors)


class CompletionLog(models.Model):
    chore = models.ForeignKey(
        Chore, on_delete=models.CASCADE, related_name="completion_logs"
    )
    completed_by = models.ForeignKey(
        HouseholdMember, on_delete=models.PROTECT, related_name="completions"
    )
    completed_at = models.DateTimeField()
    due_date_at_completion = models.DateField()

    def __str__(self):
        return f"{self.chore} completed by {self.completed_by} at {self.completed_at}"
