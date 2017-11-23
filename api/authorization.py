from tastypie.authorization import DjangoAuthorization

# Overwrite Django authorization to allow
# anyone to create a field report
class FieldReportAuthorization(DjangoAuthorization):
    def create_detail(self, object_list, bundle):
        return True
