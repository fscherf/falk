from test_app.components.base import Base


def InnerComponent():
    return """
        <style>
            #inner-component {
                border: 1px solid grey;
                padding: 1em;
            }
        </style>

        <div id="inner-component">
            <strong>Inner Component:</strong>
            <span id="inner-component-render-state">
                {{ "initial render" if initial_render else "re render" }}
            </span>

            <br/><br/>

            <button
              id="render-inner-component"
              onclick="{{ callback(render) }}">
                Render Inner Component
            </button>

            {{ props.children }}
        </div>
    """


def OuterComponent(
        InnerComponent=InnerComponent,
):
    return """
        <style>
            #outer-component {
                border: 1px solid grey;
                padding: 1em;
            }
        </style>

        <div id="outer-component">
            <strong>Outer Component:</strong>
            <span id="outer-component-render-state">
                {{ "initial render" if initial_render else "re render" }}
            </span>

            <br/><br/>

            <InnerComponent>
                <button
                  id="render-outer-component"
                  onclick="{{ callback(render) }}">
                    Render Outer Component
                </button>
            </InnerComponent>
        </div>
    """


def CallbackPassing(
        Base=Base,
        OuterComponent=OuterComponent,
):

    return """
        <Base title="Callback Passing">
            <h2>Callback Passing</h2>
            <OuterComponent/>
        </Base>
    """
