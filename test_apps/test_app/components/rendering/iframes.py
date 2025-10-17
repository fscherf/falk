from test_app.components.events.click import Counter
from test_app.components.base import Base


def Iframe(
        request,
        initial_render,
        state,
        Counter=Counter,
        Base=Base,
):

    if initial_render:
        state["index"] = request["match_info"]["index"]

    return """
        <Base title="iFrames" menu="{{ False }}">
            <h3>iFrame #{{ state.index }}</h3>
            <Counter />
            {% for i in range(100) %}
                <br />
            {% endfor %}
            <span>END</span>
        </Base>
    """


def Iframes(context, state, initial_render, Base=Base):
    if initial_render:
        state["active_index"] = 0

    def set_active_index(args):
        state["active_index"] = args[0]

    context.update({
        "set_active_index": set_active_index,
    })

    return """
        <Base title="iFrames">
            <h2>iFrames</h2>
            <div class="tabs">
                {% for i in range(4) %}
                    <span
                      class="tab{% if i == state.active_index %} active{% endif %}"
                      onClick="{{ callback(set_active_index, [i]) }}">
                        iFrame #{{ i }}
                    </span>
                {% endfor %}
            </div>
            <div class="iframes">
                {% for i in range(4) %}
                    <iframe
                      class="iframe{% if i == state.active_index %} active{% endif %}"
                      src="{{ get_url('rendering__iframe', {'index': i}) }}">
                    </iframe>
                {% endfor %}
            </div>
        </Base>
    """
