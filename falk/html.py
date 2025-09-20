from html.parser import HTMLParser
from enum import Enum, auto
import secrets
import base64

from falk.errors import (
    InvalidScriptBlockError,
    InvalidStyleBlockError,
    MultipleRootNodesError,
    InvalidSettingsError,
    MissingRootNodeError,
    UnbalancedTagsError,
    UnclosedTagsError,
)

SINGLE_TAGS = [
    "link",
    "meta",
    "img",
    "input",
]


def render_attribute_string(attribute_list=None, overrides=None):
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

    attr_string = " ".join(attribute_string_parts)

    if attr_string:
        attr_string = " " + attr_string

    return attr_string


def get_attribute(attribute_list, name):
    for key, value in attribute_list:
        if name == key:
            return value


class RootAttributeParser(HTMLParser):
    class StopFeeding(Exception):
        pass

    # HTML parser hooks
    def handle_starttag(self, tag_name, attribute_list):
        self.render(
            tag_name=tag_name,
            attribute_list=attribute_list,
            self_closing=False,
        )

    def handle_startendtag(self, tag_name, attribute_list):
        self.render(
            tag_name=tag_name,
            attribute_list=attribute_list,
            self_closing=True,
        )

    # rendering helper
    def get_index(self):
        line_number, offset = self.getpos()
        lines = self._html_source.splitlines(keepends=True)
        index = sum(len(lines[i]) for i in range(line_number - 1))
        index += offset

        return index

    def render(self, tag_name, attribute_list, self_closing):
        attribute_string = render_attribute_string(
            attribute_list=attribute_list,
            overrides=self._attributes,
        )

        index = self.get_index()

        self._output += self._html_source[:index]
        self._output += f"<{tag_name}{attribute_string}"

        if self_closing:
            self._output += " /"

        self._output += ">"
        self._output += self._html_source[index+len(self.get_starttag_text()):]

        raise self.StopFeeding()

    # API
    def add_attributes(self, html_source, attributes):
        self._html_source = html_source
        self._attributes = attributes
        self._output = ""

        tag_handled = False

        try:
            self.feed(data=html_source)

        except self.StopFeeding:
            tag_handled = True

        if not tag_handled:
            raise MissingRootNodeError()

        return self._output


class ComponentTemplateParser(HTMLParser):
    class BlockType(Enum):
        STYLE = auto()
        HTML = auto()
        SCRIPT = auto()

    def get_raw_tag_name(self, normalized_tag_name):
        line_number, offset = self.getpos()
        line = self._source_lines[line_number-1]

        offset += 1

        if line[offset] == "/":
            offset += 1

        return line[offset:offset+len(normalized_tag_name)]

    def _handle_start_tag(self, tag_name, attribute_list, self_closing):
        if tag_name not in ("link", "style", "script"):
            self._html_tag_encountered = True

        # handle link nodes
        if not self._stack and tag_name == "link":
            href = get_attribute(attribute_list, "href")

            if not href:
                raise InvalidStyleBlockError(
                    "link nodes need to define a href",
                )

            self._data["style_urls"].append(href)

            return

        # set block type and update stack
        if not self._stack:
            if tag_name == "style":
                self._block_type = self.BlockType.STYLE

            elif tag_name == "script":
                self._block_type = self.BlockType.SCRIPT

            else:
                # The block type only gets set if the stack is empty. If we
                # set it to HTML, and there is more in _data["html"] than
                # whitespace, we know that we are about to start a second
                # root node.
                if self._data["html"].strip():
                    raise MultipleRootNodesError(
                        "HTML blocks can not contain more than one root node",
                    )

                self._block_type = self.BlockType.HTML

        if tag_name not in SINGLE_TAGS and not self_closing:
            self._stack.append(tag_name)

        # HTML
        if self._block_type == self.BlockType.HTML:
            attribute_string = render_attribute_string(
                attribute_list=attribute_list,
            )

            tag_name = self.get_raw_tag_name(tag_name)

            self._data["html"] += f"<{tag_name}{attribute_string}"

            if self_closing:
                self._data["html"] += " /"

            self._data["html"] += ">"

        # style URLs
        elif self._block_type == self.BlockType.SCRIPT:
            src = get_attribute(attribute_list, "src")

            if src:
                self._data["script_urls"].append(src)

    # HTML parser hooks
    def handle_decl(self, declaration):
        self._declaration = declaration

    def handle_starttag(self, tag_name, attribute_list):
        self._handle_start_tag(
            tag_name=tag_name,
            attribute_list=attribute_list,
            self_closing=False,
        )

    def handle_startendtag(self, tag_name, attribute_list):
        self._handle_start_tag(
            tag_name=tag_name,
            attribute_list=attribute_list,
            self_closing=True,
        )

    def handle_data(self, data):
        if self._block_type in (self.BlockType.STYLE, self.BlockType.SCRIPT):

            # script and style tags don't get parsed further by HTMLParser, so
            # we get their entire content as data, even if they contain HTML
            # tags. So it is safe to clean the strings up and discard
            # empty ones.
            data = data.strip()

        # style block
        if self._block_type == self.BlockType.STYLE:
            self._data["styles"].append(data)

            return

        # HTML block
        elif self._block_type == self.BlockType.HTML:
            self._data["html"] += data

            return

        # script block
        if data and "src" in self.get_starttag_text():
            raise InvalidScriptBlockError(
                "script nodes can not have content and the src attribute set at the same time",  # NOQA
            )

        self._data["scripts"].append(data)

    def handle_endtag(self, tag_name):
        if tag_name in SINGLE_TAGS:
            return

        if not self._stack:
            raise UnbalancedTagsError(
                f"<{tag_name}> got closed before it got opened",
            )

        if tag_name != self._stack[-1]:
            raise UnbalancedTagsError(
                f"expected </{self._stack[-1]}>, got </{tag_name}>",
            )

        if self._block_type == self.BlockType.HTML:
            tag_name = self.get_raw_tag_name(tag_name)
            self._data["html"] += f"</{tag_name}>"

        if tag_name in ("style", "script"):
            self._block_type = self.BlockType.HTML

        self._stack.pop()

    # API
    def parse(self, component_template):
        self._source_lines = component_template.splitlines(keepends=True)
        self._block_type = self.BlockType.HTML
        self._stack = []
        self._declaration = ""
        self._html_tag_encountered = False

        self._data = {
            "style_urls": [],
            "styles": [],
            "html": "",
            "script_urls": [],
            "scripts": [],
        }

        self.feed(component_template)

        if self._stack:
            raise UnclosedTagsError()

        if not self._html_tag_encountered:
            raise MissingRootNodeError()

        self._data["html"] = self._data["html"].strip()

        if self._declaration:
            self._data["html"] = (
                f"<!{self._declaration}>\n" +
                self._data["html"]
            )

        return self._data


def add_attributes_to_root_node(html_source, attributes):
    return RootAttributeParser().add_attributes(
        html_source=html_source,
        attributes=attributes,
    )


def parse_component_template(component_template):
    return ComponentTemplateParser().parse(
        component_template=component_template,
    )


def get_node_id(mutable_app):
    if "node_id_random_bytes" not in mutable_app["settings"]:
        raise InvalidSettingsError(
            "'node_id_random_bytes' needs to be configured to generate node ids",  # NOQA
        )

    random_bytes = mutable_app["settings"]["node_id_random_bytes"]
    token_bytes = secrets.token_bytes(random_bytes)
    random_id = base64.urlsafe_b64encode(token_bytes).rstrip(b"=").decode()

    # The IDs get used as CSS selectors and CSS selectors can not start with
    # a number. To ensure this never happens, we prefix every ID with an
    # uppercase `F`.
    random_id = "F" + random_id

    return random_id
