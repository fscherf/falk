from html.parser import HTMLParser
import os

from falk.import_strings import get_import_string

from falk.errors import (
    InvalidStyleBlockError,
    MultipleRootNodesError,
    InvalidComponentError,
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

FALK_EVENTS = [
    "oninitialrender",
    "onrender",
    "onbeforerequest",
    "onresponse",
    "onbeforeunmount",
]


class ComponentTemplateParser(HTMLParser):

    # rendering helper
    def get_index(self):
        line_number, offset = self.getpos()

        return sum(self._line_lengths[:line_number-1]) + offset

    def get_current_tag_name(self, normalized_tag_name):
        index = self.get_index()

        # handle self closing tags
        if self._component_template[index+1] == "/":
            index += 1

        return (
            self._component_template[index+1:index+len(normalized_tag_name)+1]
        )

    def get_attribute(self, attribute_list, name):
        for key, value in attribute_list:
            if name == key:
                return value

    def resolve_url(self, url):

        # external URLs
        if "://" in url:
            return url

        # verbatim URLs
        if url.startswith("!"):
            return url[1:]

        # static URLs
        prefix = "/static/"

        if url.startswith(prefix):
            return os.path.join(
                self._static_prefix,
                url[len(prefix):],
            )

        raise NotImplementedError(
            f"{get_import_string(self._component)}: '{url}': only external, verbatim, and static URLs are supported",  # NOQA
        )

    def render_attribute_string(
            self,
            attribute_list=None,
            overrides=None,
            sort_names=False,
    ):

        attribute_string_parts = []
        attribute_list = attribute_list or []
        attributes = {}

        for key, value in attribute_list:
            attributes[key] = value

        attributes.update(overrides or {})

        items = attributes.items()

        if sort_names:
            items = sorted(items, key=lambda item: item[0])

        for key, value in items:
            if key == "_":
                attribute_string_parts.append(value)

            elif value is None:
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
                    f"{get_import_string(self._component)}: HTML blocks can not contain more than one root node",  # NOQA
                )

            self._has_root_node = True

        return is_root_node

    def run_falk_event_checks(self, attribute_list):
        # We assume that this function is only called if `is_root_node`
        # is False.

        for name, _ in attribute_list:
            if name.lower() in FALK_EVENTS:
                raise InvalidComponentError(
                    f"{get_import_string(self._component)}: {name} can only be used on the root node",  # NOQA
                )

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

        if not is_root_node and not self.is_component(tag_name):
            self.run_falk_event_checks(attribute_list)

        # style and script blocks
        if not self._stack:

            # styles
            if normalized_tag_name in ("style", "link"):
                if normalized_tag_name == "link":
                    href = self.get_attribute(attribute_list, "href")

                    if not href:
                        raise InvalidStyleBlockError(
                            f"{get_import_string(self._component)}: link nodes need to define a href",  # NOQA
                        )

                else:
                    self._stack.append("style")

                self._output["styles"].append([
                    normalized_tag_name,
                    attribute_list,
                    "",
                ])

                return

            # scripts
            if normalized_tag_name == "script":
                self._output["scripts"].append([
                    normalized_tag_name,
                    attribute_list,
                    "",
                ])

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
                "{% call falk._render_component(",
                self.render_function_args_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                ),
                ") %}",
            )

        # HTML tags
        else:
            self.write(
                "<",
                tag_name,
                self.render_attribute_string(
                    attribute_list=attribute_list,
                ),
            )

            if is_root_node:
                self.write(
                    '{% if _token %} data-falk-id="{{ node_id }}"{% endif %}',
                )

            self.write(">")

    def handle_startendtag(self, normalized_tag_name, attribute_list):
        is_root_node = self.run_root_node_checks(
            normalized_tag_name=normalized_tag_name,
        )

        tag_name = self.get_current_tag_name(
            normalized_tag_name=normalized_tag_name,
        )

        if not is_root_node and not self.is_component(tag_name):
            self.run_falk_event_checks(attribute_list)

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
                "{{ falk._render_component(",
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
            self._output["styles"][-1][2] = data.strip()

        # scripts
        elif self._stack == ["script"]:
            self._output["scripts"][-1][2] = data.strip()

        # HTML
        else:
            if data.strip() and not self._has_root_node:
                raise MissingRootNodeError(
                    get_import_string(self._component),
                )

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
                f"{get_import_string(self._component)}: <{tag_name}> got closed before it got opened",  # NOQA
            )

        if tag_name != self._stack[-1]:
            raise UnbalancedTagsError(
                f"{get_import_string(self._component)}: expected </{self._stack[-1]}>, got </{tag_name}>",  # NOQA
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
    def parse(
            self,
            component_template,
            component,
            root_path,
            static_url_prefix,
            hash_string,
    ):

        self._component_template = component_template
        self._component = component

        if static_url_prefix.startswith("/"):
            static_url_prefix = static_url_prefix[1:]

        self._static_prefix = os.path.join(
            root_path or "/",
            static_url_prefix,
        )

        self._output = {
            "styles": [],
            "jinja2_template": "",
            "scripts": [],
        }

        self._has_root_node = False
        self._stack = []
        self._line_lengths = []

        for line in component_template.splitlines(keepends=True):
            self._line_lengths.append(len(line))

        self.feed(data=component_template)

        if not self._has_root_node:
            raise MissingRootNodeError(
                get_import_string(self._component),
            )

        if self._stack:
            raise UnclosedTagsError(
                f"{get_import_string(self._component)}: stack: {', '.join(self._stack)}",  # NOQA
            )

        # render styles and scripts
        # styles
        for index, style_parts in enumerate(self._output["styles"]):
            tag_name, attribute_list, data = style_parts

            # link tags
            if tag_name == "link":
                href = self.get_attribute(attribute_list, "href")

                overrides = {
                    "href": self.resolve_url(
                        url=href,
                    ),

                    # `rel` is needed to make the browser load and apply the
                    # stylesheet. This override serves as a sensible default.
                    "rel": "stylesheet",
                }

                attribute_string = self.render_attribute_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                    sort_names=True,
                )

                self._output["styles"][index] = f"<link{attribute_string}>"

            # style tags
            else:
                overrides = {}

                identifier = self.get_attribute(
                    attribute_list,
                    "data-falk-id",
                )

                if not identifier:
                    identifier = self.get_attribute(
                        attribute_list,
                        "id",
                    )

                # No identifier found, so we generate a hash of the
                # tags content.
                if not identifier:
                    identifier = hash_string(data)

                overrides["data-falk-id"] = identifier

                attribute_string = self.render_attribute_string(
                    attribute_list=attribute_list,
                    overrides=overrides,
                    sort_names=True,
                )

                self._output["styles"][index] = (
                    f"<style{attribute_string}>{data}</style>"
                )

        # scripts
        for index, style_parts in enumerate(self._output["scripts"]):
            tag_name, attribute_list, data = style_parts
            src = self.get_attribute(attribute_list, "src")
            overrides = {}

            if src:
                overrides["src"] = self.resolve_url(
                    url=src,
                )

            else:
                # The script does not have an URL, so we need to find or
                # create an identifier.
                identifier = self.get_attribute(
                    attribute_list,
                    "data-falk-id",
                )

                if not identifier:
                    identifier = self.get_attribute(
                        attribute_list,
                        "id",
                    )

                # No identifier found, so we generate a hash of the
                # tags content.
                if not identifier:
                    identifier = hash_string(data)

                overrides["data-falk-id"] = identifier

            attribute_string = self.render_attribute_string(
                attribute_list=attribute_list,
                overrides=overrides,
                sort_names=True,
            )

            self._output["scripts"][index] = (
                f"<script{attribute_string}>{data}</script>"
            )

        return self._output


def parse_component_template(
        component_template,
        component,
        root_path,
        static_url_prefix,
        hash_string,
):

    # NOTE: The attributes need to be sorted to normalize the rendered tags
    # so they can be deduplicated while rendering the whole document.

    # NOTE: We need need to find or generate an identifier (URL, id, or hash)
    # here so we don't need to add a necessary hydration/init step to
    # the client.

    return ComponentTemplateParser().parse(
        component_template=component_template,
        component=component,
        root_path=root_path,
        static_url_prefix=static_url_prefix,
        hash_string=hash_string,
    )
