from django import forms


class EnumArrayWidget(forms.Widget):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def value_from_datadict(self, data, files, name):
        """
        Get the checkbox values and or them to get the final value
        """
        value = data.getlist(name)
        return ','.join(value)

    def render(self, name, value, attrs=None, renderer=None):
        html = f'<select id="id_{name}" name="{name}" multiple="">'
        values = value.split(',')
        for v, label in self.choices:
            checked = str(v) in values
            html += f'''
                <option value="{v}" {"selected" if checked else ""}>{label}</option>
            '''
        html += '</select>'

        return html
