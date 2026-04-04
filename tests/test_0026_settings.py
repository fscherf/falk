import pytest


def test_settings_dependencies(start_falk_app):
    """
    This test tests the dependencies `get_setting` and `set_setting`.
    """

    def configure_app(mutable_settings, get_setting, set_setting):
        assert mutable_settings["debug"] is False
        assert get_setting("debug") is False

        set_setting("debug", True)

        assert mutable_settings["debug"] is True
        assert get_setting("debug") is True

        with pytest.raises(ValueError, match=r"Unknown settings key.*"):
            set_setting("debug2", True)

    mutable_app, base_url, _ = start_falk_app(
        configure_app=configure_app,
    )
