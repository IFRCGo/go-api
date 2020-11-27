from modeltranslation.translator import register, TranslationOptions
from .models import (
    FieldReport,
    Action,
    ActionsTaken,
    Appeal,
    AppealDocument,
    Country,
    CountrySnippet,
    DisasterType,
    Event,
    GDACSEvent,
    Region,
    RegionSnippet,
    RegionEmergencySnippet,
    RegionProfileSnippet,
    RegionPreparednessSnippet,
    SituationReport,
    SituationReportType,
    Snippet,
)


# Field Report Translation Options
@register(FieldReport)
class FieldReportTO(TranslationOptions):
    fields = ('summary', 'description', 'actions_others', 'other_sources')


@register(Action)
class ActionTO(TranslationOptions):
    fields = ('name',)


@register(ActionsTaken)
class ActionsTakenTO(TranslationOptions):
    fields = ('summary',)


@register(Appeal)
class AppealTO(TranslationOptions):
    fields = ('name',)


@register(AppealDocument)
class AppealDocumentTO(TranslationOptions):
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
    fields = ('name', 'slug', 'summary',)


@register(GDACSEvent)
class GDACSEventTO(TranslationOptions):
    fields = ('title', 'description', 'country_text')


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
