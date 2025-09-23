from html.parser import HTMLParser

from falk.utils.iterables import add_unique_value

from falk.errors import (
    InvalidStyleBlockError,
    MultipleRootNodesError,
    MissingRootNodeError,
    UnbalancedTagsError,
    UnclosedTagsError,
)

SINGLE_TAGS = [
    "link",
    "meta",
    "img",
    "br",
    "hr",
    "input",
]


class ComponentTemplateParser(HTMLParser):

    # rendering helper
    def get_index(self):
        line_number, offset = self.getpos()

        return sum(self._line_lengths[:line_number-1]) + offset

    def get_current_tag_name(self, normalized_tag_name):
        index = self.get_index()

        # handle self closing tags
        if self._input[index+1] == "/":
            index += 1

        return self._input[index+1:index+len(normalized_tag_name)+1]

    def get_attribute(self, attribute_list, name):
        for key, value in attribute_list:
            if name == key:
                return value

    def render_attribute_string(self, attribute_list=None, overrides=None):
        attribute_string_parts = []
        attribute_list = attribute_list or []
        attributes = {}

        for key, value in attribute_list:
            attributes[key] = value

        attributes.update(overrides or {})

        for key, value in attributes.items():
            if value is None:
                attribute_string_parts.append(key)

            else:
                attribute_string_parts.append(
                    f'{key}="{value}"',
                )

        attribute_string = " ".join(attribute_string_parts)

        if attribute_string:
            attribute_string = " " + attribute_string

        return attribute_string

    def render_function_args_string(self, attribute_list=None, overrides=None):
        function_args_parts = []
        attribute_list = attribute_list or []
        attributes = {}

        for key, value in attribute_list:
            attributes[key] = value

        attributes.update(overrides or {})

        for key, value in attributes.items():

            # key only attributes: <div foo></div>
            if value is None:
                function_args_parts.append(
                    f"{key}=None",
                )

                continue

            value = value.strip()

            # expressions: <div foo="{{ i }}"></div>
            if value.startswith("{{") and value.endswith("}}"):
                value = value[2:-2].strip()

            # simple attribute strings: <div foo="bar"></div>
            else:
                value = f'"{value}"'

            function_args_parts.append(
                f'{key}={value}',
            )

        return ", ".join(function_args_parts)

    def is_component(self, tag_name):
        return tag_name[0].isupper()

    def write(self, *lines):
        self._output["jinja2_template"] += "".join(lines)

    def run_root_node_checks(self, normalized_tag_name):
        is_root_node = (
            not self._stack
            and normalized_tag_name not in ("link", "style", "script")
        )

        if is_root_node:
            if self._has_root_node:
                raise MultipleRootNodesError(
                    "HTML blocks can not contain more than one root node",
                )

            self._has_root_node = True

        return is_root_node

    # HTMLParser hooks
    def handle_decl(self, declaration):
        self.write("<!", declaration, ">")

    def handle_starttag(self, normalized_tag_name, attribute_list):
        is_root_node = self.run_root_node_checks(
            normalized_tag_name=normalized_tag_name,
        )

        tag_name = self.get_current_tag_name(
            normalized_tag_name=normalized_tag_name,
        )

        # style and script blocks
        if not self._stack:

            # styles
            if normalized_tag_name == "style":
                self._stack.append("style")

                return

            # style URLs
            if normalized_tag_name == "link":
                href = self.get_attribute(attribute_list, "href")

                if not href:
                    raise InvalidStyleBlockError(
                        "link nodes need to define a href",
                    )

                add_unique_value(
                    self._output["style_urls"],
                    href,
                )

                return

            # script URLs
            if normalized_tag_name == "script":
                src = self.get_attribute(attribute_list, "src")

                if src:
                    add_unique_value(
                        self._output["script_urls"],
                        src,
                    )

                self._stack.append("script")

                return

        # update stack
        if normalized_tag_name not in SINGLE_TAGS:
            self._stack.append(tag_name)

        # components
        if self.is_component(tag_name):
            overrides = {
                "_component_name": tag_name,
                "_node_id": None,
                "_token": None,
            }

            if is_root_node:
                overrides.update({
                    "_node_id": "{{ node_id }}",
                    "_token": "{{ _token }}",
                })

            self.write(
                "{% call _render_component(",
                self.render_function_args_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                ),
                ") %}",
            )

        # HTML tags
        else:
            overrides = {}

            if is_root_node:
                overrides.update({
                    "data-falk-id": "{{ node_id }}",
                    "data-falk-token": "{{ _token }}",
                })

            self.write(
                "<",
                tag_name,
                self.render_attribute_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                ),
                ">",
            )

    def handle_startendtag(self, normalized_tag_name, attribute_list):
        is_root_node = self.run_root_node_checks(
            normalized_tag_name=normalized_tag_name,
        )

        tag_name = self.get_current_tag_name(
            normalized_tag_name=normalized_tag_name,
        )

        # components
        if self.is_component(tag_name):
            overrides = {
                "_component_name": tag_name,
                "_node_id": None,
                "_token": None,
            }

            if is_root_node:
                overrides.update({
                    "_node_id": "{{ node_id }}",
                    "_token": "{{ _token }}",
                })

            self.write(
                "{{ _render_component(",
                self.render_function_args_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                ),
                ") }}",
            )
        # HTML tags
        else:
            self.write(
                "<",
                tag_name,
                self.render_attribute_string(
                    attribute_list=attribute_list,
                ),
                " />",
            )

    def handle_data(self, data):
        # styles
        if self._stack == ["style"]:
            self._output["styles"].append(data.strip())

        # scripts
        elif self._stack == ["script"]:
            self._output["scripts"].append(data.strip())

        # HTML
        else:
            if data.strip() and not self._has_root_node:
                raise MissingRootNodeError()

            self.write(data)

    def handle_endtag(self, normalized_tag_name):
        tag_name = self.get_current_tag_name(
            normalized_tag_name=normalized_tag_name,
        )

        if normalized_tag_name in SINGLE_TAGS:
            return

        # styles and scripts
        if (normalized_tag_name in ("style", "script") and
                self._stack == [tag_name]):

            self._stack.pop()

            return

        # update stack
        if not self._stack:
            raise UnbalancedTagsError(
                f"<{tag_name}> got closed before it got opened",
            )

        if tag_name != self._stack[-1]:
            raise UnbalancedTagsError(
                f"expected </{self._stack[-1]}>, got </{tag_name}>",
            )

        self._stack.pop()

        # components
        if self.is_component(tag_name):
            self.write(
                "{% endcall %}",
            )

        # HTML tags
        else:
            self.write(
                "</",
                tag_name,
                ">",
            )

    # public API
    def parse(self, component_template):
        self._input = component_template

        self._output = {
            "styles": [],
            "style_urls": [],
            "jinja2_template": "",
            "scripts": [],
            "script_urls": [],
        }

        self._has_root_node = False
        self._stack = []
        self._line_lengths = []

        for line in component_template.splitlines(keepends=True):
            self._line_lengths.append(len(line))

        self.feed(data=component_template)

        if not self._has_root_node:
            raise MissingRootNodeError()

        if self._stack:
            raise UnclosedTagsError(
                f"stack: {', '.join(self._stack)}",
            )

        return self._output


def parse_component_template(component_template):
    return ComponentTemplateParser().parse(
        component_template=component_template,
    )
