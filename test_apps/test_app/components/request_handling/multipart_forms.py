import json

from test_app.components.events.click import Counter
from test_app.components.base import Base


def MultipartForms(
        request,
        context,
        Base=Base,
        Counter=Counter,
        file_upload_max_files=1,
):

    def handle_submit(event):
        context.update({
            "form_data": event["formData"],

            "form_data_string": json.dumps(
                event["formData"],
                indent=2,
            ),

            "files_string": json.dumps({
                key: {
                    "filename": value.filename,
                    "size": value.size,
                } for key, value in request["files"].items()
            }),
        })

    context.update({
        "handle_submit": handle_submit,
        "form_data": {},
        "form_data_string": "",
        "files_string": "",
    })

    return """
        <Base title="Multipart Forms">
            <h2>Multipart Forms</h2>

            <form onsubmit="{{ callback(handle_submit) }}">
                <label for="field-1" >Field 1:</label>
                <input type="text" name="field-1">
                <br/>

                <label for="last-name" >Field 2:</label>
                <input type="text" name="field-2">
                <br/>

                <input type="file" name="file-1">
                <br/>

                <input type="file" name="file-2">
                <br/>

                <input type="submit" value="Submit">

                {% if request.query.get("token", ["1"]) == ["1"] %}
                    {{ upload_token(
                        max_files=int(request.query.get("max_files", ["0"])[-1]),
                        max_file_size=int(request.query.get("max_file_size", ["0"])[-1]),
                    ) }}
                {% endif %}
            </form>

            <h3>Form Data</h3>
            <pre
                id="form-data"
                class="{% if form_data_string %}filled{% else %}empty{% endif %}"
            >{{ form_data_string }}</pre>
            <pre
                id="file-data"
                class="{% if files_string %}filled{% else %}empty{% endif %}"
            >{{ files_string }}</pre>

            <h3>Counter</h3>
            <Counter />
        </Base>
    """
