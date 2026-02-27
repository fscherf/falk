from django.core.validators import RegexValidator
from django import forms

from falk.components import HTML5Base

CharacterValidator = RegexValidator(
    regex=r"^[A-Za-z]+$",
    message="Only characters are allowed",
)


class DjangoForm(forms.Form):
    character_field = forms.CharField(
        max_length=50,
        validators=[CharacterValidator],
    )


def DjangoFormComponent(request, template_context, HTML5Base=HTML5Base):
    form = DjangoForm()

    def handle_submit(event):
        form = DjangoForm(event["form_data"])

        if form.is_valid():
            value = form.cleaned_data["character_field"]

            template_context.update({
                "form": DjangoForm(),
                "message": f"Value: {value}",
            })

        else:
            template_context.update({
                "form": form,
                "message": "Invalid value",
            })

    template_context.update({
        "message": "No value",
        "handle_submit": handle_submit,
        "form": form,
    })

    return """
        <HTML5Base title="Django Form">
            <h1>Django Form</h1>
            <p id="message">{{ message }}</p>

            <form onsubmit="{{ falk.run_callback(handle_submit) }}">
                {{ form }}
                <br/>
                <input type="submit" value="Submit">
            </form>
        </HTML5Base>
    """
