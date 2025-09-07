from html.parser import HTMLParser


class PyxJinja2Transpiler(HTMLParser):

    # parsing helper
    def get_raw_tag_name(self, normalized_tag_name):
        line_number, offset = self.getpos()
        line = self._pyx_source_lines[line_number-1]

        offset += 1

        if line[offset] == "/":
            offset += 1

        return line[offset:offset+len(normalized_tag_name)]

    def is_component(self, unnormalized_tag_name):
        return unnormalized_tag_name[0].isupper()

    # rendering helper
    def render_html_attribute_string(self, attributes):
        attribute_string_parts = []

        for key, value in attributes:
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

    def render_component_props_string(self, attributes):
        props_string_parts = []

        for key, value in attributes:

            # key only attributes: <div foo></div>
            if value is None:
                props_string_parts.append(
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

            props_string_parts.append(
                f'{key}={value}',
            )

        props_string = ", ".join(props_string_parts)

        if props_string:
            props_string = f", {props_string}"

        return props_string

    def render_block_start(self, normalized_tag_name, attributes):
        tag_name = self.get_raw_tag_name(normalized_tag_name)

        # PYX component
        if self.is_component(tag_name):
            props_string = self.render_component_props_string(attributes)

            return f'{{% call _render_component(component_name="{tag_name}"{props_string}) %}}'  # NOQA

        # plain HTML
        html_attrs_string = self.render_html_attribute_string(attributes)

        return f"<{normalized_tag_name}{html_attrs_string}>"

    def render_self_closing_block(self, normalized_tag_name, attributes):
        tag_name = self.get_raw_tag_name(normalized_tag_name)

        # PYX component
        if self.is_component(tag_name):
            props_string = self.render_component_props_string(attributes)

            return f'{{{{ _render_component(component_name="{tag_name}"{props_string}) }}}}'  # NOQA

        # plain HTML
        attr_string = self.render_html_attribute_string(attributes)

        return f"<{normalized_tag_name}{attr_string} />"

    def render_block_end(self, normalized_tag_name):
        tag_name = self.get_raw_tag_name(normalized_tag_name)

        # PYX component
        if self.is_component(tag_name):
            return "{% endcall %}"

        # plain HTML
        return f"</{normalized_tag_name}>"

    # HTML parser hooks
    def handle_decl(self, declaration):
        self._jinja2_source += f"<!{declaration}>"

    def handle_starttag(self, tag, attrs):
        self._jinja2_source += self.render_block_start(
            normalized_tag_name=tag,
            attributes=attrs,
        )

    def handle_startendtag(self, tag, attrs):
        self._jinja2_source += self.render_self_closing_block(
            normalized_tag_name=tag,
            attributes=attrs,
        )

    def handle_endtag(self, tag):
        self._jinja2_source += self.render_block_end(
            normalized_tag_name=tag,
        )

    def handle_data(self, data):
        self._jinja2_source += data

    # API
    def transpile(self, pyx_source):
        self._pyx_source_lines = pyx_source.splitlines(keepends=True)
        self._jinja2_source = ""

        self.feed(data=pyx_source)

        return self._jinja2_source


def transpile_pyx_to_jinja2(pyx_source):
    return PyxJinja2Transpiler().transpile(
        pyx_source=pyx_source,
    )
