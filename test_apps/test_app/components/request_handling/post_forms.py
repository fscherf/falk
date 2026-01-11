import json

from test_app.components.base import Base


def PostForms(context, Base=Base):
    def handle_submit(event):
        context.update({
            "form_data": event["form_data"],

            "form_data_string": json.dumps(
                event["form_data"],
                indent=2,
            ),
        })

        if "update_form" in event["form_data"]:
            context["form_data"]["text_field"] = (
                context["form_data"]["text_field"][::-1]
            )

        if "clear_form" in event["form_data"]:
            context["form_data"] = {}

    context.update({
        "handle_submit": handle_submit,
        "form_data": {},
        "form_data_string": "",
    })

    return """
        <Base title="POST Forms">
            <h2>POST Forms</h2>

            <form onsubmit="{{ callback(handle_submit) }}" method="post">
                <label for="text_field" >Text Field:</label>
                <input type="text" name="text_field" value="{{ form_data.text_field }}">
                <br/>

                <label for="number_field" >Number Field:</label>
                <input type="number" name="number_field" value="{{ form_data.number_field }}">
                <br/>

                <label for="textarea_field">Textarea Field:</label>
                <textarea name="textarea_field">{{ form_data.textarea_field }}</textarea>
                <br/>

                <label for="select_field" >Select:</label>
                <select name="select_field">
                    {% for value in ["option-1", "option-2", "option-3"] %}
                        <option
                          value="{{ value }}"
                          _="{% if form_data.select_field == value %}selected{% endif %}"
                        >{{ value }}</option>
                    {% endfor %}
                </select>
                <br/>

                <label for="checkbox_field">Checkbox:</label>
                <input
                  type="checkbox"
                  name="checkbox_field"
                  _="{% if form_data.checkbox_field %}checked{% endif %}">
                <br/>

                <br/>
                <label for="name">Clear Form:</label>
                <input type="checkbox" name="clear_form">
                <br/>
                <label for="name">Update Form:</label>
                <input type="checkbox" name="update_form">
                <br/>
                <input type="submit" value="Submit">
            </form>

            <h3>Form Data</h3>
            <pre
                class="{% if form_data_string %}filled{% else %}empty{% endif %}"
            >{{ form_data_string }}</pre>
        </Base>
    """
