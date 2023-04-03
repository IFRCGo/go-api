from haystack import indexes

from flash_update.models import FlashUpdate


class FlashUpdateIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='title')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return FlashUpdate

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
