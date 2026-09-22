"""Unit tests for resume skill enrichment from Learn progress."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "resume_skills",
    API_DIR / "services" / "resume_skills.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_skills"] = _mod
_SPEC.loader.exec_module(_mod)

branch_completion_hints = _mod.branch_completion_hints
build_gap_catalog = _mod.build_gap_catalog
generate_skills_from_progress = _mod.generate_skills_from_progress
missing_slugs_for_upgrade = _mod.missing_slugs_for_upgrade
skill_level_and_evidence = _mod.skill_level_and_evidence
suggest_specialization = _mod.suggest_specialization
SKILL_RULES = _mod.SKILL_RULES


def test_empty_progress_yields_no_skills():
    assert generate_skills_from_progress([]) == []
    assert generate_skills_from_progress(set()) == []


def test_docker_junior_with_only_dockerfile_episode():
    skills = generate_skills_from_progress(["b10-docker"])
    docker = next(s for s in skills if s["key"] == "docker")
    assert docker["level"] == "junior"
    assert docker["sourceSlugs"] == ["b10-docker"]
    assert "junior" in docker["display"]


def test_docker_middle_requires_docker_and_compose():
    skills = generate_skills_from_progress(["b10-docker", "b11-compose"])
    docker = next(s for s in skills if s["key"] == "docker")
    assert docker["level"] == "middle"
    assert "Dockerfile" in docker["evidence"]
    assert "docker-compose" in docker["evidence"]
    assert "pet project" in docker["evidence"]
    assert set(docker["sourceSlugs"]) == {"b10-docker", "b11-compose"}


def test_docker_compose_alone_is_junior():
    skills = generate_skills_from_progress(["b11-compose"])
    docker = next(s for s in skills if s["key"] == "docker")
    assert docker["level"] == "junior"


def test_fastapi_middle_with_two_slugs():
    skills = generate_skills_from_progress(["b04-fastapi-health", "s01e05-fastapi"])
    fastapi = next(s for s in skills if s["key"] == "fastapi")
    assert fastapi["level"] == "middle"


def test_selected_keys_filter():
    skills = generate_skills_from_progress(
        ["b10-docker", "b11-compose", "s01e03-git"],
        selected_keys=["docker"],
    )
    assert len(skills) == 1
    assert skills[0]["key"] == "docker"


def test_suggest_specialization_devops():
    completed = ["b10-docker", "b11-compose", "map-k8s", "map-cicd"]
    assert suggest_specialization(completed) == "DevOps-инженер"


def test_branch_hints_when_majority_done():
    devops_slugs = []
    for rule in SKILL_RULES:
        if rule.map_branch == "devops":
            devops_slugs.extend(rule.episode_slugs)
    unique = list(dict.fromkeys(devops_slugs))
    take = unique[: max(1, int(len(unique) * 0.7))]
    hints = branch_completion_hints(take)
    assert any("devops" in h.lower() for h in hints)


def test_missing_slugs_for_docker_upgrade():
    assert missing_slugs_for_upgrade("docker", ["b10-docker"]) == ["b11-compose"]
    assert missing_slugs_for_upgrade("docker", ["b10-docker", "b11-compose"]) == []


def test_skill_level_helper_docker():
    rule = next(r for r in SKILL_RULES if r.key == "docker")
    level, evidence = skill_level_and_evidence(rule, ["b10-docker", "b11-compose"])
    assert level == "middle"
    assert "docker-compose" in evidence


def test_build_gap_catalog_includes_missing_docker_slug():
    catalog = build_gap_catalog(["b10-docker"], selected_keys=["docker"])
    docker = next(c for c in catalog if c["skillKey"] == "docker")
    assert docker["missingSlugs"] == ["b11-compose"]
    assert docker["inResume"] is True


def test_build_gap_catalog_flags_skill_not_in_resume():
    catalog = build_gap_catalog(
        ["b10-docker", "b11-compose"],
        selected_keys=[],
    )
    docker = next(c for c in catalog if c["skillKey"] == "docker")
    assert docker["inResume"] is False
    assert docker["missingSlugs"] == []
