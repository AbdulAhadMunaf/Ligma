from django.db import models


class AITaskTypeChoices(models.TextChoices):
    ACTION = "action", "Action"
    DECISION = "decision", "Decision"
    QUESTION = "question", "Question"
    REFERENCE = "reference", "Reference"


class AITaskStatusChoices(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In progress"
    BLOCKED = "blocked", "Blocked"
    DONE = "done", "Done"
    ARCHIVED = "archived", "Archived"


class AITaskPriorityChoices(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class AIInferenceStatusChoices(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class AIInferenceSourceTierChoices(models.TextChoices):
    FILTER = "tier_1_filter", "Tier 1 filter"
    PATCH = "tier_2_patch", "Tier 2 patch"
    GLOBAL = "tier_3_global", "Tier 3 global"