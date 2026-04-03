def test_entry_points(start_falk_app):
    """
    This test tests the entry points startup and shutdown.
    """

    run_entry_points = []

    def handle_startup_1(mutable_app):
        run_entry_points.append("handle_startup_1")

    def handle_startup_2(mutable_app):
        run_entry_points.append("handle_startup_2")

    def handle_shutdown_1(mutable_app):
        run_entry_points.append("handle_shutdown_1")

    def handle_shutdown_2(mutable_app):
        run_entry_points.append("handle_shutdown_2")

    def configure_app(add_startup_callback, add_shutdown_callback):
        add_startup_callback(handle_startup_1)
        add_startup_callback(handle_startup_2)
        add_shutdown_callback(handle_shutdown_1)
        add_shutdown_callback(handle_shutdown_2)

    _, _, stop_app = start_falk_app(
        configure_app=configure_app,
    )

    assert run_entry_points == [
        "handle_startup_1",
        "handle_startup_2",
    ]

    stop_app()

    assert run_entry_points == [
        "handle_startup_1",
        "handle_startup_2",
        "handle_shutdown_1",
        "handle_shutdown_2",
    ]
