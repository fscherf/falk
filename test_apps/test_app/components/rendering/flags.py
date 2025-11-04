from datetime import datetime

from test_app.components.events.click import Counter
from test_app.components.base import Base


def Wrapper(
        props,
        context,
        state,
        skip_rendering,
        force_rendering,
        initial_render,
):

    if initial_render:
        state["id"] = props.get("id", "")

    def _skip_rendering():
        skip_rendering()

    def _force_rendering():
        force_rendering()

    context.update({
        "skip_rendering": _skip_rendering,
        "force_rendering": _force_rendering,
        "timestamp": str(datetime.now()),
    })

    return """
        <style>
            .wrapper-component {
                border: 1px solid grey;
                padding: 1em;
            }

            .wrapper-component-body {
                border: 1px solid grey;
                margin: 1em 0;
                padding: 1em;
            }
        </style>

        <div class="wrapper-component" id="{{ state.id }}">
            <div>
                <strong>Wrapper</strong>
            </div>

            rendered at: <span class="timestamp">{{ timestamp }}</span>

            <div class="wrapper-component-body" data-skip-rerendering>
                {{ props.children }}
            </div>

            <button
              class="render"
              onclick="{{ callback(render) }}">
                Render
            </button>

            <button
              class="skip-rendering"
              onclick="{{ callback(skip_rendering) }}">
                Skip Rendering
            </button>

            <button
              class="force-rendering"
              onclick="{{ callback(force_rendering) }}">
                Force Rendering
            </button>
        </div>
    """


def RenderingFlags(
    Base=Base,
    Wrapper=Wrapper,
    Counter=Counter,
):

    return """
        <Base title="Skip Rerender Attribute">
            <h2>Rendering Flags</h2>

            <Wrapper id="outer-wrapper">
                <Counter id="counter-1" initial_value="{{ 1 }}" />
                <Counter id="counter-2" initial_value="{{ 2 }}" />

                <br/>

                <Wrapper id="inner-wrapper">
                    <Counter id="counter-3" initial_value="{{ 3 }}" />
                    <Counter id="counter-4" initial_value="{{ 4 }}" />
                </Wrapper>
            </Wrapper>
        </Base>
    """
