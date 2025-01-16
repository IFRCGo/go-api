# Local development
> [!NOTE]
> Using https://github.com/IFRCGo/sdt-api/ as OIDC application

## GO-API: Django config
> [!IMPORTANT]
> `192.168.88.88` is used for local development only
>
> Make sure to replace `192.168.88.88` with your device IP within your local network
>
> This is to make sure your local browser and application (running inside docker) requiring SSO can communitate with go-api using same IP

Update .env with
```
DJANGO_ADDITIONAL_ALLOWED_HOSTS=192.168.88.88

OIDC_ENABLE=true
OIDC_RSA_PRIVATE_KEY_BASE64_ENCODED=YOUR-ENCODED-VALUE
OIDC_RSA_PUBLIC_KEY_BASE64_ENCODED=YOUR-ENCODED-VALUE
```
> [!TIP]
> Generate OIDC RSA keys with 4096 bits using [RSA-KEY-PAIR-GENERATOR](https://it-tools.tech/rsa-key-pair-generator)
>
> Then, encode the keys using [BASE64-STRING-CONVERTER](https://it-tools.tech/base64-string-converter)

> [!IMPORTANT]
> Make sure to run `docker compose up -d serve` to update the container with newly added environment variables
>
> Make sure to run `docker compose run --rm migrate` to run any pending SSO database migrations

## GO-API: Add new local SSO app
Add new "application" from the Django Admin Panel - http://192.168.88.88:8000/en/admin/oauth2_provider/application/

Use the following parameters to create application for SDT:

|Config|Value|
|--|--|
|Redirect uris | http://localhost:8080/accounts/oidc/ifrcgo/login/callback/ |
|Client type | Public |
|Authorization grant type | Authorization code |
|Hash client secret | true |
|Name | SDT Local |
|Algorithm | RSA with SHA-2 256 |

> [!NOTE]
> We are assuming the application is running locally at port 8080

> [!WARNING]
> Copy the **"Client secret:"** before saving the form as it will be hashed after save.
>
> We will also need the client id on the next step.

## SDT: Django config

Add/update the following variables in the `.env` file:
```bash
# OIDC config
OIDC_ADMIN_PANEL_ENABLED=true  # Disable this if you can't access admin panel
OIDC_IFRCGO_ENABLED=true
OIDC_IFRCGO_OIDC_ENDPOINT=http://192.168.88.88:8000/o
OIDC_IFRCGO_CLIENT_ID=CLIENT-ID-FROM-GO-API
OIDC_IFRCGO_CLIENT_SECRET=CLIENT-SECRET-FROM-GO-API
```
