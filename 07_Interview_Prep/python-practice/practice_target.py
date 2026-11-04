"""Tests load your work from exercises/ by default.
Set PRACTICE_TARGET=solutions to run the same tests against the reference solutions."""
import importlib
import os


def load(name: str):
    target = os.environ.get("PRACTICE_TARGET", "exercises")
    return importlib.import_module(f"{target}.{name}")
