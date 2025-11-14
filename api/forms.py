from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .logger import logger
from .models import Action, ActionOrg, ActionType, Appeal


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_("organizations"), choices=ActionOrg.choices)
    field_report_types = forms.MultipleChoiceField(label=_("field report types"), choices=ActionType.choices)

    class Meta:
        model = Action
        fields = "__all__"


class AppealForm(forms.ModelForm):
    force_history_save = forms.BooleanField(
        label="Save changes to history",
        required=False,
        initial=False,
        help_text="Check if changes should be saved to AppealHistory, regardless of the values of the fields.",
    )

    class Meta:
        model = Appeal
        fields = "__all__"


class LoginForm(forms.Form):
    email = forms.CharField(label=_("email"), required=True)
    password = forms.CharField(
        label=_("password"),
        widget=forms.PasswordInput(),
        required=True,
    )

    # FIXME: We need to refactor this code
    def get_user(self, username, password):
        if "ifrc" in password.lower() or "redcross" in password.lower():
            logger.warning("User should be warned to use a stronger password.")

        if username is None or password is None:
            raise ValidationError("Should not happen. Frontend prevents login without username/password")

        user = authenticate(username=username, password=password)
        if user is None and User.objects.filter(email=username).count() > 1:
            users = User.objects.filter(email=username, is_active=True)
            # FIXME: Use users.exists()
            if users:
                # We get the first one if there are still multiple available is_active:
                user = authenticate(username=users[0].username, password=password)

        return user

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        user = self.get_user(email, password)
        if not user:
            raise ValidationError("Invalid credentials.")

        cleaned_data["user"] = user
        return cleaned_data
