from modeltranslation.translator import TranslationOptions, register

from .models import (
    Action,
    ActionsTaken,
    AdminKeyFigure,
    Appeal,
    AppealDocument,
    Country,
    CountryKeyFigure,
    CountrySnippet,
    DisasterType,
    Event,
    EventLink,
    ExternalPartner,
    FieldReport,
    GDACSEvent,
    GeneralDocument,
    KeyFigure,
    MainContact,
    Region,
    RegionEmergencySnippet,
    RegionKeyFigure,
    RegionPreparednessSnippet,
    RegionProfileSnippet,
    RegionSnippet,
    SituationReportType,
    Snippet,
    Source,
    SupportedActivity,
)


@register(Action)
class ActionTO(TranslationOptions):
    fields = ("name", "tooltip_text")


@register(ActionsTaken)
class ActionsTakenTO(TranslationOptions):
    fields = ("summary",)


@register(Appeal)
class AppealTO(TranslationOptions):
    fields = ("name",)


@register(AppealDocument)
class AppealDocumentTO(TranslationOptions):
    fields = ("name",)


@register(GeneralDocument)
class GeneralDocumentTO(TranslationOptions):
    fields = ("name",)


@register(Country)
class CountryTO(TranslationOptions):
    fields = (
        "name",
        "society_name",
        "overview",
        "additional_tab_name",
    )


@register(CountrySnippet)
class CountrySnippetTO(TranslationOptions):
    fields = ("snippet",)


@register(DisasterType)
class DisasterTypeTO(TranslationOptions):
    fields = ("name", "summary")


@register(Event)
class EventTO(TranslationOptions):
    fields = ("name", "summary", "title")
    skip_fields = ("name",)  # XXX: CUSTOM field Not used by TranslationOptions, but used in lang/tasks.py


@register(ExternalPartner)
class ExternalPartnerTO(TranslationOptions):
    fields = ("name",)


@register(FieldReport)
class FieldReportTO(TranslationOptions):
    fields = ("title", "summary", "description", "actions_others", "other_sources")
    skip_fields = ("summary",)  # XXX: CUSTOM field Not used by TranslationOptions, but used in lang/tasks.py


@register(GDACSEvent)
class GDACSEventTO(TranslationOptions):
    fields = ("title", "description", "country_text")


@register(MainContact)
class MainContactTO(TranslationOptions):
    fields = ("extent",)


@register(Region)
class RegionTO(TranslationOptions):
    fields = (
        "label",
        "additional_tab_name",
    )


@register(RegionSnippet)
class RegionSnippetTO(TranslationOptions):
    fields = ("snippet",)


@register(RegionEmergencySnippet)
class RegionEmergencySnippetTO(TranslationOptions):
    fields = (
        "title",
        "snippet",
    )


@register(RegionProfileSnippet)
class RegionProfileSnippetTO(TranslationOptions):
    fields = (
        "title",
        "snippet",
    )


@register(RegionPreparednessSnippet)
class RegionPreparednessSnippetTO(TranslationOptions):
    fields = (
        "title",
        "snippet",
    )


@register(SituationReportType)
class SituationReportTypeTO(TranslationOptions):
    fields = ("type",)


@register(Snippet)
class SnippetTO(TranslationOptions):
    fields = ("snippet",)


@register(SupportedActivity)
class SupportedActivityTO(TranslationOptions):
    fields = ("name",)


@register(EventLink)
class EventLinkTO(TranslationOptions):
    fields = ("title", "description")


@register(Source)
class SourceTO(TranslationOptions):
    fields = ("spec",)


@register(KeyFigure)
class KeyFigureTo(TranslationOptions):
    fields = ("deck",)


@register(AdminKeyFigure)
class AdminKeyFigureTo(TranslationOptions):
    fields = ("deck",)


@register(CountryKeyFigure)
class CountryKeyFigureTo(TranslationOptions):
    pass


@register(RegionKeyFigure)
class RegionKeyFigureTo(TranslationOptions):
    pass
