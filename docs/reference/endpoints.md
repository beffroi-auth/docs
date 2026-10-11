---
title: Endpoints
description: Every route the bundle serves, its method, the plane it belongs to and the specification it answers.
---

# Endpoints

Paths are relative to the issuer, which is where the application imports the routes of the bundle. A
deployment whose issuer is `https://op.example.com` serves the token endpoint at
`https://op.example.com/token`.

Every route name carries its plane. `beffroi_protocol_*` is server to server, called by a client or a
resource server; `beffroi_interaction_*` is a browser, where a person reads a page and answers. The
`BEFFROI_PLANE` environment variable restricts a process to one plane, so an interaction never reaches a
machine that only serves the protocol, and the other way round.

## The protocol plane

| Method | Path | Route | Specification |
|---|---|---|---|
| `GET` | `/.well-known/openid-configuration` | `beffroi_protocol_discovery` | OIDC Discovery 1.0 §4 |
| `GET` | `/.well-known/oauth-authorization-server` | `beffroi_protocol_authorization_server_metadata` | RFC 8414 |
| `GET` | `/jwks` | `beffroi_protocol_jwks` | RFC 7517 |
| `POST` | `/token` | `beffroi_protocol_token` | RFC 6749 §3.2 |
| `GET` `POST` | `/userinfo` | `beffroi_protocol_userinfo` | OIDC Core §5.3 |
| `POST` | `/introspect` | `beffroi_protocol_introspection` | RFC 7662, RFC 9701 |
| `POST` | `/revoke` | `beffroi_protocol_revocation` | RFC 7009 |
| `POST` | `/par` | `beffroi_protocol_pushed_authorization_request` | RFC 9126 |
| `POST` | `/device_authorization` | `beffroi_protocol_device_authorization` | RFC 8628 §3.1 |
| `POST` | `/backchannel_authentication` | `beffroi_protocol_backchannel_authentication` | CIBA Core §7 |
| `POST` | `/register` | `beffroi_protocol_client_registration` | RFC 7591 |
| `GET` | `/register/{client_id}` | `beffroi_protocol_client_configuration_read` | RFC 7592 §2.1 |
| `PUT` | `/register/{client_id}` | `beffroi_protocol_client_configuration_update` | RFC 7592 §2.2 |
| `DELETE` | `/register/{client_id}` | `beffroi_protocol_client_configuration_delete` | RFC 7592 §2.3 |

The endpoints a deployment actually announces are the ones it has wired. The discovery document is built
from what is wired, never from a list kept beside it, so a grant you did not enable is not advertised.

## The interaction plane

| Method | Path | Route | What it is |
|---|---|---|---|
| `GET` `POST` | `/authorize` | `beffroi_interaction_authorize` | The authorization endpoint, OIDC Core §3.1.2 |
| `GET` `POST` | `/login` | `beffroi_interaction_login` | Where a person proves who they are |
| `GET` `POST` | `/login/code` | `beffroi_interaction_login_code` | The second factor, when one is asked for |
| `POST` | `/login/passkey/options` | `beffroi_interaction_passkey_login_options` | The assertion options of a passkey ceremony |
| `POST` | `/login/passkey` | `beffroi_interaction_passkey_login` | The assertion itself |
| `GET` `POST` | `/consent` | `beffroi_interaction_consent` | What a client is asking for, and the answer |
| `GET` `POST` | `/logout` | `beffroi_interaction_logout` | RP-initiated logout, OIDC RP-Initiated Logout 1.0 |
| `GET` `POST` | `/device` | `beffroi_interaction_device` | Where the code shown by a device is confirmed, RFC 8628 §3.3 |
| `GET` | `/initiate-login` | `beffroi_interaction_initiate_login` | Third party initiated login, OIDC Core §4 |
| `POST` | `/locale` | `beffroi_interaction_locale` | The language a visitor chose for the pages |

### The account pages

A person reads what the provider holds of them, and takes it back, without an administrator. Each page
belongs to no client and to no interaction, and each one but the home refuses a browser that holds no
session rather than sending it to a login.

| Method | Path | Route | What is on it |
|---|---|---|---|
| `GET` | `/account` | `beffroi_interaction_account` | One card per page below, with what the account holds there |
| `GET` `POST` | `/account/approvals` | `beffroi_interaction_account_approvals` | What somebody is waiting on an answer for now, CIBA Core §7.1 |
| `GET` | `/account/profile` | `beffroi_interaction_account_profile` | What the provider holds of this person, one line per claim |
| `GET` | `/account/profile/changes` | `beffroi_interaction_account_profile_changes` | What those claims said before, and when they changed |
| `GET` | `/account/password` | `beffroi_interaction_account_password` | When the password was last written, and the form that replaces it |
| `GET` | `/account/passkeys` | `beffroi_interaction_account_passkeys` | The passkeys of this person, with their names, dates and state |
| `GET` | `/account/two-factor` | `beffroi_interaction_account_two_factor` | The second factor, and the backup codes that go with it |
| `GET` | `/account/two-factor/enrol` | `beffroi_interaction_account_two_factor_enrolment` | The two steps of a TOTP enrolment, the key and the first code |
| `GET` | `/account/consents` | `beffroi_interaction_account_consents` | One line per client this person agreed to, with the scopes it holds |
| `GET` | `/account/applications/{id}` | `beffroi_interaction_account_application` | What one of those applications holds, behind its line |
| `GET` | `/account/sessions` | `beffroi_interaction_account_sessions` | Where this person is signed in, and what each session proved |
| `GET` | `/account/sign-ins` | `beffroi_interaction_account_sign_ins` | What the journal holds of their sign-ins, successes and refusals |
| `GET` | `/account/notifications` | `beffroi_interaction_account_notifications` | The browsers the provider can reach by web push |
| `GET` | `/account/archive` | `beffroi_interaction_account_archive` | The file holding everything the provider knows of them |
| `GET` | `/account/archive/file` | `beffroi_interaction_account_archive_file` | That file, downloaded as it was built |

An action is taken where it is read, so each page posts to a route of its own. A form answers `303 See
Other` towards the page it came from, accepted or refused, which is what RFC 9110 §15.4.4 says of a
response to a POST that is not its result: a reload reads a page again instead of sending the form a
second time. Three answers are the response itself rather than a redirection, each one read once: the
backup codes that end an enrolment, the notice that the session this browser was reading on has ended, and
the archive wrapped under a passphrase, which is the file.

| Method | Path | Route |
|---|---|---|
| `POST` | `/account/profile` | `beffroi_interaction_account_profile_describe` |
| `POST` | `/account/password` | `beffroi_interaction_account_password_change` |
| `POST` | `/account/passkeys/options` | `beffroi_interaction_account_passkeys_options` |
| `POST` | `/account/passkeys` | `beffroi_interaction_account_passkeys_enrol` |
| `POST` | `/account/passkeys/{id}/name` | `beffroi_interaction_account_passkeys_rename` |
| `POST` | `/account/passkeys/{id}/revoke` | `beffroi_interaction_account_passkeys_revoke` |
| `POST` | `/account/two-factor/begin` | `beffroi_interaction_account_two_factor_begin` |
| `POST` | `/account/two-factor` | `beffroi_interaction_account_two_factor_enrol` |
| `POST` | `/account/two-factor/revoke` | `beffroi_interaction_account_two_factor_revoke` |
| `POST` | `/account/two-factor/backup-codes` | `beffroi_interaction_account_two_factor_backup_codes` |
| `POST` | `/account/consents/{id}/revoke` | `beffroi_interaction_account_consents_revoke` |
| `POST` | `/account/sessions/{id}/revoke` | `beffroi_interaction_account_sessions_revoke` |
| `POST` | `/account/sessions/revoke-others` | `beffroi_interaction_account_sessions_revoke_others` |
| `POST` | `/account/notifications` | `beffroi_interaction_account_notifications_subscribe` |
| `POST` | `/account/notifications/{id}/name` | `beffroi_interaction_account_notifications_name` |
| `POST` | `/account/notifications/{id}/revoke` | `beffroi_interaction_account_notifications_revoke` |
| `POST` | `/account/archive` | `beffroi_interaction_account_archive_ask` |
| `POST` | `/account/archive/file` | `beffroi_interaction_account_archive_wrapped_file` |
| `POST` | `/account/archive/drop` | `beffroi_interaction_account_archive_drop` |

[:octicons-arrow-right-24: The account pages](../symfony-bundle/account.md)

### The scripts the pages load

Served by the bundle so a deployment has no build step to run for them.

| Method | Path | Route |
|---|---|---|
| `GET` | `/passkey.js` | `beffroi_interaction_passkey_script` |
| `GET` | `/push.js` | `beffroi_interaction_push_script` |
| `GET` | `/push-worker.js` | `beffroi_interaction_push_worker` |
| `GET` | `/copy.js` | `beffroi_interaction_copy_script` |
| `GET` | `/password-strength.js` | `beffroi_interaction_password_strength_script` |
