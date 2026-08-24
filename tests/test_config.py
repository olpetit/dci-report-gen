import os

from dci_report_gen.config import load_config


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_load_config():
    path = os.path.join(FIXTURES, "sample_config.yaml")
    config = load_config(path)

    assert config.title == "Test Report"
    assert config.author == "Test Author"
    assert config.date == "2024-06-01"
    assert len(config.sections) == 1

    section = config.sections[0]
    assert section.name == "OCP Jobs"
    assert section.source.type == "dci"
    assert "2024-06-01" in section.source.query
    assert section.render.style == "table"
    assert len(section.render.columns) == 3


def test_var_substitution():
    path = os.path.join(FIXTURES, "sample_config.yaml")
    config = load_config(path, var_overrides={"date_start": "2024-07-01"})

    assert "2024-07-01" in config.sections[0].source.query
    assert "2024-06-01" not in config.sections[0].source.query


def test_auto_date():
    path = os.path.join(FIXTURES, "sample_config.yaml")
    config = load_config(path)
    assert config.date == "2024-06-01"


def test_include_results_config():
    path = os.path.join(FIXTURES, "config_with_results.yaml")
    config = load_config(path)

    assert config.data is not None
    assert config.data["jobs"].include_results is True


def test_context_config():
    path = os.path.join(FIXTURES, "config_with_results.yaml")
    config = load_config(path)

    assert config.context is not None
    assert config.context["site_hardware"]["site5"] == "HPE DL110"
    assert config.context["site_hardware"]["site10"] == "Dell SPR-EE"


def test_default_include_results_false():
    path = os.path.join(FIXTURES, "sample_config.yaml")
    config = load_config(path)

    for section in config.sections:
        assert section.source.include_results is False


def test_default_context_empty():
    path = os.path.join(FIXTURES, "sample_config.yaml")
    config = load_config(path)

    assert config.context == {}


def test_include_files_config():
    path = os.path.join(FIXTURES, "config_with_results.yaml")
    config = load_config(path)

    assert config.data["jobs_with_files"].include_files is True
    assert config.data["jobs_with_files"].file_patterns == ["ibi_cluster_timing", "microcode_"]
    assert config.data["jobs"].include_files is False
    assert config.data["jobs"].file_patterns is None
