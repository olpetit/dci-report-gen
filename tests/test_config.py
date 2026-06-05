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
