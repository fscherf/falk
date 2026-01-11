import hashlib
import json
import os

from falk.file_uploads import get_tempfile_upload_handler
from test_app.components.base import Base


def get_md5(path):
    md5_hash = hashlib.md5()

    md5_hash.update(open(path, "rb").read())

    return md5_hash.hexdigest()


def get_component(
        html_id,
        html_name,
        token,
        max_files,
        max_file_size_in_bytes,
):

    def component(
            request,
            context,
            handle_file_upload=get_tempfile_upload_handler(
                max_files=max_files,
                max_file_size_in_bytes=max_file_size_in_bytes,
            ),
    ):

        def handle_submit(event):
            context.update({
                "form_data": event["form_data"],

                "form_data_string": json.dumps(
                    event["form_data"],
                    indent=2,
                ),

                "files_string": json.dumps({
                    key: {
                        "filename": os.path.basename(value),
                        "size": os.stat(value).st_size,
                        "md5": get_md5(value),
                    } for key, value in request["files"].items()
                }),
            })

        context.update({
            "handle_submit": handle_submit,
            "html_id": html_id,
            "html_name": html_name,
            "token": token,
            "form_data": {},
            "form_data_string": "",
            "files_string": "",
        })

        return """
            <div id="{{ html_id }}">
                <h3>{{ html_name }}</h3>
                <pre
                    id="form-data"
                    class="{% if form_data_string %}filled{% else %}empty{% endif %}"
                >{{ form_data_string }}</pre>
                <pre
                    id="file-data"
                    class="{% if files_string %}filled{% else %}empty{% endif %}"
                >{{ files_string }}</pre>


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

                    {% if token %}
                        {{ upload_token() }}
                    {% endif %}
                </form>
            </div>
        """

    # HACK: we need a better way to generate components like this
    component.__qualname__ = html_id

    return component


FileUploadForm1 = get_component(
    html_id="form-1",
    html_name="1 file 1024 bytes max",
    token=True,
    max_files=1,
    max_file_size_in_bytes=1024,
)

FileUploadForm2 = get_component(
    html_id="form-2",
    html_name="2 files a 1024 bytes max",
    token=True,
    max_files=2,
    max_file_size_in_bytes=1024,
)

FileUploadForm3 = get_component(
    html_id="form-3",
    html_name="2 files a 1024 bytes max, no token",
    token=False,
    max_files=2,
    max_file_size_in_bytes=1024,
)


def FileUploadForm4():
    return """
        <div id="form-4">
            <h3>No handler set</h3>

            <form onsubmit="{{ callback(render) }}">
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

                {{ upload_token() }}
            </form>
        </div>
    """


def MultipartForms(
        mutable_app,
        Base=Base,
        FileUploadForm1=FileUploadForm1,
        FileUploadForm2=FileUploadForm2,
        FileUploadForm3=FileUploadForm3,
        FileUploadForm4=FileUploadForm4,
):

    return """
        <Base title="Multipart Forms">
            <h2>Multipart Forms</h2>

            <FileUploadForm1 />
            <FileUploadForm2 />
            <FileUploadForm3 />
            <FileUploadForm4 />
        </Base>
    """
