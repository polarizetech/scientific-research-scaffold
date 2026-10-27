"""Bench {{slug}} as a test (TOOL_VERSIONING.md §1b): `make bench` at the tool's root runs it."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import run  # noqa: E402


def test_references_are_pinned_and_tolerances_decided():
    assert run.main(["--verify"]) == 0


def test_tool_agrees_with_its_references():
    assert run.main([]) == 0
