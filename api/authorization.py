from tastypie.authorization import DjangoAuthorization

# Overwrite Django authorization to allow
# anyone to read or create a field report
class FieldReportAuthorization(DjangoAuthorization):
    def read_list(self, object_list, bundle):
        return True

    def read_detail(self, object_list, bundle):
        return True

    def create_detail(self, object_list, bundle):
        return True
