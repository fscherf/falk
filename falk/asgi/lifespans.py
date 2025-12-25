import asyncio
import logging

logger = logging.getLogger("falk")


async def run_entry_point(mutable_app, entry_point):
    loop = asyncio.get_event_loop()

    def _func():
        try:
            entry_point(mutable_app)

        except Exception:
            logger.exception(
                "exception raised while running %s",
                entry_point,
            )

    return loop.run_in_executor(
        executor=mutable_app["executor"],
        func=_func,
    )


async def shutdown(mutable_app, send):
    await run_entry_point(
        mutable_app=mutable_app,
        entry_point=mutable_app["entry_points"]["on_shutdown"],
    )

    if mutable_app["executor"]:
        mutable_app["executor"].shutdown(
            wait=False,
        )

    await send({"type": "lifespan.shutdown.complete"})


async def handle_lifespan(mutable_app, scope, receive, send):
    try:
        while True:
            event = await receive()

            # startup
            if event["type"] == "lifespan.startup":
                await run_entry_point(
                    mutable_app=mutable_app,
                    entry_point=mutable_app["entry_points"]["on_startup"],
                )

                await send({"type": "lifespan.startup.complete"})

            # shutdown
            elif event["type"] == "lifespan.shutdown":
                await shutdown(
                    mutable_app=mutable_app,
                    send=send,
                )

                break

    # unplanned shutdown
    except asyncio.CancelledError:
        await shutdown(
            mutable_app=mutable_app,
            send=send,
        )

    except Exception:
        logger.exception("exception raised while handling lifespan events")

        if event["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.failed"})

        else:
            await send({"type": "lifespan.shutdown.failed"})

        raise
