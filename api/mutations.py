import strawberry


@strawberry.type
class Mutation:
    """
    class ErrorType(graphene.ObjectType):
        verifyCode = graphene.String()
        email = graphene.String()
        session = graphene.String()
        userName = graphene.String()
        user = graphene.String()


    Existing Mutation
    - register
        - captcha
        - verify_token using email
    - logout
    - change_email
    - forget_password
    - update_profile
        - first_name: str
        - last_name: str
        - country: str
        - city: str
        - avatar: str
    """

    noop: strawberry.ID = strawberry.ID("noop")
