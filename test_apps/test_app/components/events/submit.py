from pprint import pformat

from test_app.components.base import Base


def Submit(context, Base=Base):
    def format_event_data(event):
        context.update({
            "event_data_string": pformat(event),
        })

    context.update({
        "event_data_string": "{}",
        "format_event_data": format_event_data,
    })

    return """
        <Base title="Submit Events">
            <h2>Submit Events</h2>

            <h3>Form</h3>
            <form onsubmit="{{ callback(format_event_data) }}">
                <div>
                    <label for="text-input-1">Text Input 1:</label>
                    <input name="text-input-1" type="text">
                </div>
                <div>
                    <label for="text-input-2">Text Input 2:</label>
                    <input name="text-input-2" type="text">
                </div>
                <div>
                    <label for="number-input">Number Input:</label>
                    <input name="number-input" type="number">
                </div>
                <div>
                    <label for="range">Range Input:</label>
                    <input name="range" type="range">
                </div>
                <br/>
                <div>
                    <input type="submit" value="Submit">
                </div>
            </form>

            <h3>Event Data</h3>
            <pre>{{ event_data_string }}</pre>
        </Base>
    """
