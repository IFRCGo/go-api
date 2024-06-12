from django import forms


class EnumArrayWidget(forms.Widget):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def value_from_datadict(self, data, files, name):
        """
        Get the checkbox values and or them to get the final value
        Input processing
        """
        value = data.getlist(name)
        # obsolete: return ','.join(value)
        return [int(v) for v in value]

    def render(self, name, value, attrs=None, renderer=None):
        """
        Output preparation
        """
        html = f'<select id="id_{name}" name="{name}" multiple="">'
        for v, label in self.choices:
            checked = v in value
            html += f"""
                <option value="{v}" {"selected" if checked else ""}>{label}</option>
            """
        html += "</select>"

        return html
