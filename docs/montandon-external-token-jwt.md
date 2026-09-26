# Montandon external token (JWT)

This document describes how GO API issues JWT tokens for external integrations, including the [Montandon](https://www.montandon.io/) alert platform.

## Overview

Authenticated GO users can create **external tokens** via the REST API. Each token is a signed JWT (RS256) whose claims identify the user and token lifetime. Montandon and other external services use these tokens to authenticate callbacks or API access on behalf of a GO user.

## API flow

1. User accepts Montandon license terms (optional gate; currently commented out in code):
   - `POST /api/v2/user/{user_id}/accepted_license_terms/`
2. User creates an external token:
   - `POST /api/v2/external-token/`
   - Body: `{ "title": "My integration name", "expire_timestamp": "<optional ISO datetime>" }`
3. Response includes the signed JWT string in the `token` field (read-only; not stored in the database).

List and retrieve tokens at `/api/v2/external-token/` (tokens with `is_old_token=True` are hidden from the API).

## Database model

`registrations.UserExternalToken`:

| Field | Purpose |
|-------|---------|
| `title` | Human-readable label for the integration |
| `user` | Owning GO user |
| `jti` | UUID — unique token identifier (JWT claim) |
| `created_at` | Creation timestamp |
| `expire_timestamp` | Expiration datetime (JWT `exp` claim) |
| `is_old_token` | Legacy Montandon tokens (migration cleanup flag) |

Default expiry when omitted: `JWT_EXPIRE_TIMESTAMP_DAYS` (settings/env, default 365 days). Maximum allowed expiry is the same setting.

## JWT payload structure

Built by `UserExternalToken.get_payload()`:

```json
{
  "jti": "<uuid string>",
  "userId": <integer Django user id>,
  "exp": <datetime — encoded as Unix timestamp by PyJWT>,
  "inMovement": true
}
```

| Claim | Meaning |
|-------|---------|
| `jti` | Token id — use for revocation/blacklist if implemented |
| `userId` | GO user primary key |
| `exp` | Expiration (must be in the future at creation) |
| `inMovement` | Always `true` for current tokens; marks IFRC “in movement” context for Montandon |

## Signing

- **Algorithm:** RS256
- **Private key:** `OIDC_RSA_PRIVATE_KEY` (PEM) or `OIDC_RSA_PRIVATE_KEY_BASE64_ENCODED`
- **Public key:** `OIDC_RSA_PUBLIC_KEY` (for verifiers)
- **Header:** `kid` set to JWK thumbprint of the private key (`registrations.utils.jwt_encode_handler`)

If OIDC keys are not configured, token creation returns HTTP 400.

## Configuration (environment)

| Variable | Description |
|----------|-------------|
| `OIDC_RSA_PRIVATE_KEY` / `_BASE64_ENCODED` | PEM private key for signing |
| `OIDC_RSA_PUBLIC_KEY` / `_BASE64_ENCODED` | PEM public key for verification |
| `JWT_EXPIRE_TIMESTAMP_DAYS` | Max/default token lifetime in days |

## Montandon integration

- Alert source enum: `notifications.models.AlertSource.MONTANDON` (value `100`)
- Email templates can include `related_montandon_events` for alert notifications
- User profile field `accepted_montandon_license_terms` tracks license acceptance

External services should validate the JWT signature with the published public key, check `exp`, and use `userId` / `jti` as needed for authorization.

## Related code

- `registrations/models.py` — `UserExternalToken`, `get_payload()`
- `registrations/serializers.py` — `UserExternalTokenSerializer`
- `registrations/utils.py` — `jwt_encode_handler()`
- `registrations/views.py` — `UserExternalTokenViewset`
- `main/urls.py` — route registration

## Security notes

- Tokens are only returned once at creation; store them securely on the client.
- Updates are not allowed (`update` raises validation error).
- Delete via API is disabled; revoke by expiry or future blacklist on `jti`.
