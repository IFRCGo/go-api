from modeltranslation.translator import register, TranslationOptions
from .models import (
    Action,
    ActionsTaken,
    Appeal,
    AppealDocument,
    GeneralDocument,
    Country,
    CountrySnippet,
    DisasterType,
    Event,
    ExternalPartner,
    FieldReport,
    GDACSEvent,
    MainContact,
    Region,
    RegionSnippet,
    RegionEmergencySnippet,
    RegionProfileSnippet,
    RegionPreparednessSnippet,
    SituationReport,
    SituationReportType,
    Snippet,
    SupportedActivity,
    EventFeaturedDocument,
    EventLink,
)


@register(Action)
class ActionTO(TranslationOptions):
    fields = ('name', 'tooltip_text')


@register(ActionsTaken)
class ActionsTakenTO(TranslationOptions):
    fields = ('summary',)


@register(Appeal)
class AppealTO(TranslationOptions):
    fields = ('name',)


@register(AppealDocument)
class AppealDocumentTO(TranslationOptions):
    fields = ('name',)


@register(GeneralDocument)
class GeneralDocumentTO(TranslationOptions):
    fields = ('name',)


@register(Country)
class CountryTO(TranslationOptions):
    fields = ('name', 'society_name', 'overview', 'additional_tab_name',)


@register(CountrySnippet)
class CountrySnippetTO(TranslationOptions):
    fields = ('snippet',)


@register(DisasterType)
class DisasterTypeTO(TranslationOptions):
    fields = ('name', 'summary')


@register(Event)
class EventTO(TranslationOptions):
    fields = ('name', 'slug', 'summary')


@register(ExternalPartner)
class ExternalPartnerTO(TranslationOptions):
    fields = ('name',)


@register(FieldReport)
class FieldReportTO(TranslationOptions):
    fields = ('summary', 'description', 'actions_others', 'other_sources')


@register(GDACSEvent)
class GDACSEventTO(TranslationOptions):
    fields = ('title', 'description', 'country_text')


@register(MainContact)
class MainContactTO(TranslationOptions):
    fields = ('extent',)


@register(Region)
class RegionTO(TranslationOptions):
    fields = ('label', 'additional_tab_name',)


@register(RegionSnippet)
class RegionSnippetTO(TranslationOptions):
    fields = ('snippet',)


@register(RegionEmergencySnippet)
class RegionEmergencySnippetTO(TranslationOptions):
    fields = ('title', 'snippet',)


@register(RegionProfileSnippet)
class RegionProfileSnippetTO(TranslationOptions):
    fields = ('title', 'snippet',)


@register(RegionPreparednessSnippet)
class RegionPreparednessSnippetTO(TranslationOptions):
    fields = ('title', 'snippet',)


@register(SituationReport)
class SituationReportTO(TranslationOptions):
    fields = ('name',)


@register(SituationReportType)
class SituationReportTypeTO(TranslationOptions):
    fields = ('type',)


@register(Snippet)
class SnippetTO(TranslationOptions):
    fields = ('snippet',)


@register(SupportedActivity)
class SupportedActivityTO(TranslationOptions):
    fields = ('name',)


@register(EventFeaturedDocument)
class EventFeaturedDocumentTO(TranslationOptions):
    fields = ('title', 'description')


@register(EventLink)
class EventLinkTO(TranslationOptions):
    fields = ('title', 'description')
