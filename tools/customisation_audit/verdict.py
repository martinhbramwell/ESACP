"""Verdict + PromotionStrategy enums per plan §6."""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    IN_FIXTURE_CORRECT = "in_fixture_correct"
    DRIFTED = "drifted"
    DB_ONLY = "db_only"
    ORPHAN_FIXTURE = "orphan_fixture"
    DISCARDABLE_CORE_EDIT = "discardable_core_edit"
    FIXTURE_EQUIVALENT_CORE_EDIT = "fixture_equivalent_core_edit"
    HUMAN_REVIEW_CORE_EDIT = "human_review_core_edit"
    ENUMERATE_ONLY = "enumerate_only"
    INFORMATIONAL = "informational"


class PromotionStrategy(str, Enum):
    FIXTURE_JSON = "fixture_json"
    FIXTURES_CUSTOM_SCRIPTS = "fixtures_custom_scripts"
    APP_TRANSLATIONS_CSV = "app_translations_csv"
    V14_PATCH_SCRIPT = "v14_patch_script"
    MANUAL = "manual"
    NONE = "none"
