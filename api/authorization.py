from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.exceptions import Unauthorized

# Overwrite Django authorization to allow
# anyone to read or create a field report
class FieldReportAuthorization(DjangoAuthorization):
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        return []

    def create_detail(self, object_list, bundle):
        return True


class UserProfileAuthorization(Authorization):
    def authorize_superuser(self, bundle):
        if bundle.request.user.is_superuser:
            return True
        raise Unauthorized('Not allowed')

    def authorize_user(self, bundle):
        if bundle.request.user == bundle.obj:
            return True
        return self.authorize_superuser(bundle)

    def read_list(self, object_list, bundle):
        if bundle.request.user.is_superuser:
            return object_list
        else:
            return object_list.filter(username=bundle.request.user.username)

    def read_detail(self, object_list, bundle):
        return self.authorize_user(bundle)

    def create_list(self, object_list, bundle):
        return self.authorize_superuser(bundle)

    def create_detail(self, object_list, bundle):
        return self.authorize_superuser(bundle)

    def update_list(self, object_list, bundle):
        allowed = []
        for user in object_list:
            if user.username == bundle.request.user.username:
                allowed.append(obj)
        return allowed

    def update_detail(self, object_list, bundle):
        return self.authorize_user(bundle)

    def delete_list(self, object_list, bundle):
        return self.authorize_superuser(bundle)

    def delete_detail(self, object_list, bundle):
        return self.authorize_superuser(bundle)
