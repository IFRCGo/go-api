# Attention! deployments/PersonnelViewset CSV output does not use this:
class CsvListMixin:
    def get_csv_serializer_class(self):
        return self.csv_serializer_class

    def get_serializer_class(self):
        """
        By default include_docs_urls configures the underlying SchemaView to generate public schemas.
        This means that views will not be instantiated with a request instance.
        i.e. Inside the view self.request will be None.
        """
        if self.action == "list" and self.request is not None:
            format = self.request.GET.get("format", "json")
            if format == "csv":
                return self.get_csv_serializer_class()
        return super().get_serializer_class()
