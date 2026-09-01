import pytest
from pydantic import ValidationError
from studio.models import ProjectCreateRequest, ProjectMergeRequest


@pytest.mark.parametrize("bad_name", [
    "../../etc/passwd",
    "..\\..\\Windows\\System32",
    "foo/bar",
    "foo\\bar",
    "..",
    "",
    "   ",
])
def test_project_create_rejects_unsafe_names(bad_name):
    with pytest.raises(ValidationError):
        ProjectCreateRequest(name=bad_name, tools=["postgres"])


@pytest.mark.parametrize("good_name", [
    "my-project",
    "My Project 01",
    "data_lake.v2",
])
def test_project_create_accepts_safe_names(good_name):
    req = ProjectCreateRequest(name=good_name, tools=["postgres"])
    assert req.name == good_name


def test_project_merge_rejects_unsafe_names():
    with pytest.raises(ValidationError):
        ProjectMergeRequest(name="../escape", project_ids=["a", "b"])
