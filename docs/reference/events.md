---
title: Events
description: Every event the core, the protocol and the SAML package dispatch, what each one carries, what listens to it, and how it crosses the broker.
---

# Events

The core, `beffroi/oidc` and `beffroi/saml` dispatch PSR-14 events, and the bundle replays them on Messenger. Every
event names its act, the date it happened, its tenant and the provenance of the request it came from, as [the
events of the core](../core/events.md#what-every-event-carries) describe; the tables below say what each one
carries beyond those four, and who it concerns:

- **a person**, when it implements `ConcernsAPersonInterface` and names the subject of their account, never the
  `sub` a client was given;
- **a client**, when it implements `ConcernsAClientInterface` and names the client by the identifier it was
  registered under, never the client itself.

## Every event crosses the broker

An event is routed to the transport `async_priority_low`, the database unless the deployment names a broker,
every one of them by the interface they all implement, so an event added to a package leaves the process without
a line of configuration. Its body is a JWE to the message key of the tenant; what stays readable on the transport
is the class of the event, its stamps and the slug of its tenant. Nothing listens in the process that raised it,
and an event nothing listens to is announced all the same.

## What listens

**Every event is written to the journal.** `WriteTheActDownHandler` hears every event of the three packages and
writes one row: the act, the date, the provenance, sealed, the subject when the event concerns a person and the
client when it concerns a client, and nothing else. A row is kept `beffroi.journal.retention` days, 180 by default,
and `beffroi:user:journal` reads it back for a person.

The other listeners of the bundle each hear one event, or an interface a few of them implement:

| Listener | Hears | What it does |
|---|---|---|
| `BackChannelLogoutHandler` | `session.ended` | Mints a logout token for each client of the session that registered a back-channel logout URI (Back-Channel Logout 1.0 §2.6), each one raising `logout_token.issued` |
| `RevokeTheTokensOfTheSessionHandler` | `session.ended` | Revokes the refresh tokens of the session and removes its opaque access tokens, dated by the end of the session |
| `RevokeWhatOutlivedTheSessionHandler` | `refresh_token.outlived_its_session` | The same again, dated by the end of the session, for what a refresh in flight had saved |
| `EnrichTheProvenanceHandler` | `user.authenticated`, through `SessionProvenanceInterface` | Finds the place of the two provenances of the session and writes it on its row |
| `BuildThePersonalArchiveHandler` | `archive.asked` | Builds the archive the person asked for |
| `RecordClientUseHandler` | `authorization_code.issued` and `tokens.issued`, through `ClientInUseInterface` | Dates the last use of the client, which the removal of the clients nobody uses reads |
| `WriteWhatTheClientWasGivenHandler` | `tokens.issued` | Writes, beside the act, what the client was given of the person, kept as long as the act |
| `QueueLogoutTokenHandler` | `logout_token.issued` | Hands the token to the notifications lane, `async_notifications`, which posts it to the client |
| `QueueClientNotificationHandler` | `backchannel_request.answered` | Hands the call to the notification endpoint of the client to the same lane |
| `RecordTheServiceProviderOfTheSessionHandler` | `saml.service_provider.signed_in` | Records the part of the service provider in the session, for the logout the identity provider starts |

A logout token its client refuses is given up at once. One that cannot be delivered is tried again on the
schedule of `beffroi.back_channel_logout`, and goes to the failure transport once that schedule runs out. Either
way, `logout_token.given_up` is raised.

## The events of the core

| Act | Class | Raised when | Carries beyond the four | Concerns |
|---|---|---|---|---|
| `user.authenticated` | `UserAuthenticated` | A session is opened | The session | A person |
| `authentication.failed` | `AuthenticationFailed` | A login is refused | The method claimed, the reason, the identifier as typed, the user when one answers | A person, or nobody |
| `session.ended` | `AuthenticationSessionEnded` | A session ends | The session, which says who ended it | A person |
| `password.used` | `PasswordUsed` | A password is accepted | The credential | A person |
| `passkey.used` | `PasskeyUsed` | A passkey assertion is verified | The credential, and whether its sign count did not grow | A person |
| `totp.used` | `TotpUsed` | A code of the authenticator application is accepted | The credential | A person |
| `backup_code.used` | `BackupCodeUsed` | A backup code is spent | The credential | A person |
| `person.provisioned` | `PersonProvisioned` | An upstream provider creates a person | The subject and the name of the provider | A person |
| `credential.enrolled` | `CredentialEnrolled` | A passkey or a TOTP is enrolled | The credential | A person |
| `credential.renamed` | `CredentialRenamed` | A passkey is renamed | The credential, and the name it had | A person |
| `credential.revoked` | `CredentialRevoked` | A credential is revoked | The credential | A person |
| `credential.forgotten` | `CredentialForgotten` | The floor of the tenant forgets a credential | The credential | A person |
| `password.changed` | `PasswordChanged` | A person replaces their own password | The credential | A person |
| `password.rehashed` | `PasswordRehashed` | A password is stored again under the algorithm and the parameters of the hasher | The credential | A person |
| `backup_codes.renewed` | `BackupCodesRenewed` | A person draws another set of backup codes | The credential | A person |
| `enrolment_ticket.issued` | `EnrolmentTicketIssued` | An enrolment ticket is issued | The ticket | A person |
| `person.described_themselves` | `PersonDescribedThemselves` | A person says something of themselves | The user, the name of the claim, whether it was taken back | A person |
| `archive.asked` | `PersonAskedForTheirArchive` | A person asks for their archive | The identifier of the archive and the subject | A person |
| `archive.taken` | `PersonTookTheirArchive` | A person downloads it | The same | A person |
| `archive.dropped` | `PersonDroppedTheirArchive` | A person has it dropped | The same | A person |
| `tenant.key_staged` | `TenantKeyStaged` | A key is drawn and staged, published in the JWK Set when its algorithm is one the set carries | The key | Nobody |
| `tenant.key_rotated` | `TenantKeyRotated` | A key takes over | The key activated, and the one it replaced | Nobody |
| `tenant.key_retired` | `TenantKeyRetired` | A key leaves the service | The key, and why | Nobody |
| `tenant.data_keys_rewrapped` | `TenantDataKeysRewrapped` | The data keys are wrapped by another client | The counts, the clients and the master key | Nobody |
| `tenant.data_keys_destroyed` | `TenantDataKeysDestroyed` | The data keys are erased | The counts | Nobody |
| `kms.unavailable` | `KmsUnavailable` | The key management service fails on the path of a request | What the service said | Nobody |
| `load.budget_spent` | `LoadBudgetSpent` | A request is refused for a spent load budget | The budget, the route, the client when one was authenticated | Nobody |

## The events of the protocol

| Act | Class | Raised when | Carries beyond the four | Concerns |
|---|---|---|---|---|
| `authorization_code.issued` | `AuthorizationCodeIssued` | An authorization code leaves for a client | The client, the subject, the grant, the session, the hash of the code, the scopes, when it expires | A person, a client |
| `authorization_code.replayed` | `AuthorizationCodeReplayed` | A code is presented a second time (RFC 6749 §4.1.2), and the tokens issued from it are revoked | The hash of the code, the subject, the client it was issued to, the client that presented it, the hashes of the tokens revoked | A person |
| `tokens.issued` | `TokensIssued` | The token endpoint answers a client, whatever the grant | The grant type and the grant, the client, the subject, null for a client acting for itself (RFC 6749 §4.4), the session, the scopes granted, when the access token expires, whether an ID token left, what the tokens are bound to, the hash of the refresh token, the claims asked for by name, the authorization details, the shape of the access token; never a token | A person or nobody, a client |
| `refresh_token.rotated` | `RefreshTokenRotated` | A refresh token is replaced by its successor (RFC 6749 §6) | The client, the subject, the family, the hashes of both tokens, when the successor expires | A person, a client |
| `refresh_token.reuse_detected` | `RefreshTokenReuseDetected` | A rotated refresh token is presented again, and its whole family revoked (RFC 9700 §4.13.2) | The client, the subject, the family, the hash presented, the hashes revoked | A person, a client |
| `refresh_token.outlived_its_session` | `RefreshTokenOutlivedItsSession` | A refresh token still recorded active is presented for a session that ended, and refused | The client, the subject, the session, when the session ended | A person, a client |
| `token.revoked` | `TokenRevoked` | A client gives a token back at the revocation endpoint (RFC 7009 §2.1) | The client that revoked it, the subject, null for a token naming nobody, the type of the token, its hash, the grant, the access tokens revoked with a refresh token | A person, or nobody |
| `client_authentication.failed` | `ClientAuthenticationFailed` | A client fails to authenticate, at any endpoint that authenticates one | The reason, the client identifier as typed, the method presented | Nobody |
| `consent.granted` | `ConsentGranted` | A person agrees, on the consent page, on the page that confirms a device code, or when answering a backchannel request | The consent, the client, the subject, the scopes, the authorization details, the consent it takes over from | A person, a client |
| `consent.revoked` | `ConsentRevoked` | A person takes a consent back, on their account or by the console | The consent, the client, the subject, the grants revoked with it, and the hashes of the refresh and access tokens revoked | A person, a client |
| `introspection.answered` | `IntrospectionAnswered` | A resource server is told who an active token names (RFC 7662 §2.2). An inactive token, or one naming nobody, raises nothing | The client that asked, the subject | A person, a client |
| `userinfo.answered` | `UserInfoAnswered` | A client is answered the claims of a person (OIDC Core §5.3) | The client, the subject; never which claims | A person, a client |
| `logout_token.issued` | `LogoutTokenIssued` | A logout token is minted for a client of a session that ended (Back-Channel Logout 1.0 §2.6) | The client, the subject, the logout URI, the session, the token | A person, a client |
| `logout_token.given_up` | `LogoutTokenGivenUp` | A logout token is refused by its client, or could not be delivered within the retries (Back-Channel Logout 1.0 §2.8) | The client, the subject, the session, what the last attempt came back with; never the token | A person, a client |
| `backchannel_request.answered` | `BackchannelRequestAnswered` | A backchannel request is answered, yes or no, for a client registered to be called (CIBA Core §10.2) | The client, the subject, null when the request named nobody, the notification endpoint, the identifier of the request, the notification token | A person or nobody, a client |
| `pushed_request.refused` | `PushedRequestRefused` | A `request_uri` presented at the authorization endpoint grants nothing (RFC 9126 §4) | The reason, the client that presented it, the client it was pushed by; never the reference | Nobody |
| `registered_client.deleted` | `RegisteredClientDeleted` | A client that registered itself is gone: deleted at its configuration endpoint (RFC 7592 §2.3), by `beffroi:client:delete`, or dropped for want of use | The client | A client |

The reason of `client_authentication.failed` is one of `malformed_credentials`, `multiple_mechanisms`,
`mismatched_client_id`, `unsupported_scheme`, `no_credentials`, `unknown_client`, `unexpected_method`,
`invalid_secret`, `invalid_assertion`, `replayed_assertion`, `unreadable_client_keys`, `unexpected_certificate` and
`unreadable_certificate`; the client is answered `invalid_request` or `invalid_client` (RFC 6749 §5.2) whatever it
is. The reason of `pushed_request.refused` is one of `unknown_request_uri`, `expired_request_uri`,
`already_used_request_uri` and `other_client`; the client is answered `invalid_request_uri` whatever it is.

## The event of the SAML package

| Act | Class | Raised when | Carries beyond the four | Concerns |
|---|---|---|---|---|
| `saml.service_provider.signed_in` | `ServiceProviderSignedIn` | Single sign-on answers a service provider with an assertion written from a session | The session, the entity ID of the service provider, the subject; never the `NameID` it was given | A person |
