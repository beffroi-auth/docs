---
title: The ports of the protocol
description: The interfaces through which beffroi/oidc asks the outside for what it cannot do itself, what the bundle answers each one with, and what ships in the package.
---

# The ports of the protocol

`beffroi/oidc` knows no HTTP, no database and no container. What it needs of the outside it asks through a
port: an interface of `Beffroi\Oidc\Port`, one capability each, with the few methods that capability needs and
the exceptions an implementation may throw written in its contract. A use case is given the ports it calls
and no other.

[The bundle](../symfony-bundle/index.md) answers every port. An integration outside Symfony answers them
itself, and starts from the implementations the package ships, [below](#what-ships-in-the-package).

**Besides its own**, the package uses eighteen ports of [the core](../core/ports.md), `Beffroi\Core\Port`:
it calls sixteen and implements two. And it calls two interfaces of the PHP-FIG, the clock of PSR-20, which
the use cases read the time from, and the event dispatcher of PSR-14, which every act leaves through.

| Port of the core | What the protocol does with it |
|---|---|
| `RandomnessInterface` | Draws every value it hands out and recognises later: codes, tokens, references, user codes |
| `UuidGeneratorInterface` | Names what it records, grants, consents and families of refresh tokens among them, and the `jti` of a logout token |
| `JwsSignerInterface` | Signs what the tenant issues: ID tokens, `at+jwt`, logout tokens, signed UserInfo, introspection and authorization responses |
| `JwsVerifierInterface` | Verifies what the tenant signed and is handed back: an `at+jwt`, an `id_token_hint` |
| `JweDecrypterInterface` | Opens a request object encrypted to the tenant |
| `PublicKeySetProviderInterface` | The JWK Set it publishes |
| `SignatureAlgorithmsInterface`, `KeyEncryptionAlgorithmsInterface`, `ContentEncryptionAlgorithmsInterface` | The algorithms it is wired with, which it signs, verifies and encrypts with and announces |
| `UserRepositoryInterface` | The person a public `sub` or a login hint names, and the person of a token |
| `AuthenticationSessionRepositoryInterface` | The session a token descends from |
| `CredentialRepositoryInterface` | What a person holds, when a request asks for more than the session proved |
| `LinkedIdentityRepositoryInterface` | The person the assertion of a trusted issuer is about (RFC 7523 §3) |
| `PasswordHasherInterface`, `PasswordAlgorithmsInterface` | The secrets of the clients, hashed when they are kept and read back by the algorithm they name |
| `SecretSealerInterface` | Seals what nobody but the provider may read: the person an `at+jwt` of a token exchange or of a JWT bearer grant is about, and the references a backchannel request keeps for the client it calls back |
| `KeyBoundArtifactInterface`, implemented | Six kinds of document bound to a key of the tenant, the ID token, the `at+jwt`, the logout token, the signed authorization response, the pushed request and the request object encrypted to it, each declaring how long a retiring key stays published for it |
| `ArchiveChapterInterface`, implemented | The two chapters the protocol adds to the archive of a person: the consents, and what each client was given |

## What the protocol keeps

| Port | What it answers | In the bundle |
|---|---|---|
| `AuthorizationCodeRepositoryInterface` | The codes waiting for the token endpoint, consumed atomically, and kept once used so that a replay is told from an unknown code | Doctrine |
| `LoggedInClientsInterface` | The clients a session signed in, which the logout channels tell | Doctrine, the store of codes |
| `RefreshTokenRepositoryInterface` | Refresh tokens by the digest of their value, by family, by code and by session, rotated and revoked ones kept | Doctrine |
| `RefreshTokensOfAConsentInterface` | What a client can still renew for a person, for the consent that person takes back | Doctrine |
| `AccessTokenRepositoryInterface` | Opaque access tokens, under the digest of their value and never the value | Doctrine |
| `CanRevokeAccessTokenInterface`, `CanRevokeAccessTokensByGrantInterface`, `CanRevokeAccessTokensBySessionInterface`, `CanRevokeAccessTokensByConsentInterface` | What a store of opaque access tokens can take back: one token, the tokens of a grant, of a session, of a consent | Doctrine, the same store |
| `ConsentRepositoryInterface`, `ActiveConsentsInterface`, `CanPageActiveConsentsInterface` | The consents, and the ones in force for the page of the account | Doctrine |
| `InteractionRepositoryInterface` | An authorization request between the pages a person goes through | Doctrine |
| `PushedAuthorizationRecordRepositoryInterface` | The pushed requests waiting for the authorization endpoint (RFC 9126 §2.2) | Doctrine |
| `DeviceAuthorizationRecordRepositoryInterface` | The device authorization requests, by device code and by user code (RFC 8628 §3.2) | Doctrine |
| `BackchannelAuthenticationRecordRepositoryInterface` | The backchannel requests waiting for their person and their client (CIBA Core §7) | Doctrine |
| `RecordedGrantsInterface`, `CanRevokeGrantsByConsentInterface` | The grant a token descends from, whichever flow wrote its record, and the grants a person leaves to a client | The module, over the three stores of records above |
| `InitialAccessTokenRepositoryInterface`, `IssuedInitialAccessTokensInterface` | The initial access tokens of a tenant, looked up by digest, and listed for whoever issued them (RFC 7591 §1.2) | Doctrine |
| `PairwiseSubjectRepositoryInterface` | The person a pairwise identifier of a sector names (OIDC Core §8.1) | Doctrine |
| `PairwiseSaltInterface` | The salt the pairwise identifiers of a tenant are computed with | A file beside the sealed keys, sealed like them |
| `DisclosuresInterface`, `DisclosuresOfAPersonInterface` | What a client was given of a person, written and forgotten, and read for that person | Doctrine |

## The clients

| Port | What it answers | In the bundle |
|---|---|---|
| `ClientRepositoryInterface` | The client of a tenant that carries an identifier | The module, over every source wired |
| `ClientSourceInterface` | One source of clients | The clients the configuration declares, and the clients registered dynamically, in Doctrine |
| `ClientInventoryInterface` | Every client of a source, for whoever runs the deployment | The module, over the same two sources |
| `ClientStoreInterface` | The rows of the clients registered dynamically (RFC 7591 §3.2.1, RFC 7592) | Doctrine |
| `UnusedClientsInterface` | The clients a source may drop for lack of use | Doctrine; the declared clients answer none, and are never dropped |
| `ClientRegistrationPolicyInterface` | Whether a tenant registers clients, and under which policy | The configuration |
| `TrustedIssuersInterface` | The third parties whose assertions a tenant trusts (RFC 7523 §3) | The configuration |
| `PushedAuthorizationRequirementInterface`, `RegisteredAccessTokenShapesInterface`, `RegisteredResourcesInterface`, `RegisteredScopesInterface`, `UnsignedRequestObjectsInterface` | What the clients of a tenant registered, read as a set: whether every one pushes its requests, which shapes of access token and which resources and scopes they take, whether one reads unsigned request objects | The module, over the sources |

## What the workers share

Each of these remembers something between two requests, and is meant to be shared by every worker of a
deployment: a replay on another worker is a replay all the same, and a budget is the budget of the whole
deployment.

| Port | What it remembers | In the bundle |
|---|---|---|
| `ClientAssertionReplayGuardInterface` | The `jti` of a client assertion until it expires (RFC 7523 §3) | The cache pool `beffroi.client_assertions` |
| `IssuerAssertionReplayGuardInterface` | The `jti` of an assertion a trusted issuer signed, until it expires | `beffroi.issuer_assertions` |
| `RequestObjectReplayGuardInterface` | The `jti` of a request object until it expires (CIBA Core §7.1.1) | `beffroi.request_objects` |
| `SoftwareStatementReplayGuardInterface` | The `jti` of a software statement until it expires (RFC 7591 §2.3) | `beffroi.software_statements` |
| `DpopProofReplayGuardInterface` | The `jti` of a DPoP proof, per key, for as long as the proof stands (RFC 9449 §11.1) | `beffroi.dpop` |
| `DpopNonceInterface` | Whether a proof must carry a nonce, and whether the one it carries is current (RFC 9449 §8) | `beffroi.dpop` when nonces are required, nothing otherwise |
| `ClientJwksCacheInterface` | The keys read back from a `jwks_uri`, with when they were read | `beffroi.client_keys`, and `beffroi.issuer_keys` for trusted issuers |
| `ClientLoadBudgetInterface` | What an authenticated client may still ask in the window | A rate limiter on `beffroi.load` |

The bundle declares each pool on `cache.app`, in a pool of its own, so that a deployment points one at a
shared store without touching the rest of its cache.

## What the provider fetches

| Port | What it reads | In the bundle |
|---|---|---|
| `ClientJwksFetcherInterface` | The JWK Set behind a `jwks_uri` (RFC 7591 §2) | Symfony's HTTP client, over HTTPS, no redirect followed, with a timeout and a bound on the size of the answer |
| `RequestObjectFetcherInterface` | The request object behind a `request_uri` the client registered (RFC 9101 §5.2) | The same |
| `SectorIdentifierDocumentFetcherInterface` | The document behind a `sector_identifier_uri` (OIDC Registration §5) | The same |

## JOSE and X.509

| Port | What it does | In the bundle |
|---|---|---|
| `CompactJwtReaderInterface` | Reads a compact JWT a client sent, and verifies nothing | `web-token/jwt-library` |
| `JwtKeyVerifierInterface` | Verifies a JWT against the keys a client publishes, and never against a key the token itself carries in `jwk`, `jku` or `x5c` | `web-token/jwt-library` |
| `ProofKeyVerifierInterface` | Verifies a DPoP proof against the public key of its own header, and names that key by its thumbprint | `web-token/jwt-library` |
| `ClientAssertionSecretVerifierInterface` | Verifies the MAC of a `client_secret_jwt` assertion against the secret of the client | `web-token/jwt-library` |
| `JweEncrypterInterface` | Encrypts a document to a key a client publishes | `web-token/jwt-library` |
| `CertificateReaderInterface` | Reads what a client certificate says of its holder, and writes a distinguished name the way it reads one | `spomky-labs/pki-framework` |

## Where the endpoints are

| Port | What it answers | In the bundle |
|---|---|---|
| `EndpointLocatorInterface` | The URL of every endpoint of a tenant, under its issuer | The router |
| `MutualTlsEndpointLocatorInterface` | The same endpoints on the host that asks for a client certificate, or none (RFC 8705 §5) | The router, under `mutual_tls.origin` |
| `ClientConfigurationEndpointInterface` | The URL where one client reads, replaces and deletes itself (RFC 7592 §3) | The router |

## Reaching somebody

| Port | What it answers | In the bundle |
|---|---|---|
| `PendingApprovalNotifierInterface` | Telling a person that a backchannel request waits for them | A message on the lane of the notifications |
| `LogoutTokenDeliveryInterface` | The budget a logout token is written for, which its `exp` and the retirement of its signing key read. It bounds the token and not the sending: a send that comes after it carries an expired token | The waits of the retry policy of that lane and the timeout of the sender, from `back_channel_logout` |

## What the wiring says

The rest are the ports through which the provider learns what it is wired with, which is what it serves and
what it announces at once. Most of them are answered by the module itself, out of the classes the
integration tags: a grant, a client authentication method, a shape of access token, a kind of subject
identifier is a class and a line of wiring, and the port that lists them is never a list kept beside it.

| Port | What it lists | Answered by |
|---|---|---|
| `ServedGrantsInterface` | The grants the token endpoint serves, and what each one does | The module, over the tagged grants |
| `ClientAuthenticationMethodsInterface` | The client authentication methods, in the order they are tried | The module, over the tagged methods |
| `CodeChallengeMethodsInterface` | The PKCE methods | The module: `S256` |
| `ServedAccessTokenShapesInterface`, `AccessTokenIssuerInterface` | The shapes access tokens are written in, and the issuer that picks the one a client registered | The module |
| `AccessTokenShapeIssuerInterface`, `AccessTokenVerifierInterface` | The writer and the reader of one shape | The module: `at+jwt` and opaque |
| `IdTokenIssuerInterface` | The ID token of a response | The module |
| `ConfirmationReaderInterface`, `ServedTokenSchemesInterface` | What a token is bound to, read back, and the schemes a token is presented under | The module, over the tagged kinds of binding |
| `ServedDeliveryModesInterface` | The ways a client is told that a backchannel request was answered | The module |
| `ServedAuthorizationDetailTypesInterface`, `AuthorizationDetailsReaderInterface` | The types of authorization detail, and the reading of a request or a claim through them | The module, over the tagged types, none in the bundle |
| `PresentedTokenTypesInterface` | The types of token a token exchange reads | The module |
| `OfferedScopesInterface` | Every scope a tenant hands out tokens for | The module |
| `ClaimsProviderInterface` | The claims of a person, by scope and by name, and what is served | The module |
| `SubjectIdentifierResolverInterface`, `PresentedSubjectReaderInterface`, `AssignedSubjectTypesInterface`, `SubjectIdentifierKindInterface` | The `sub` a client sees, the person a `sub` names for a client, and the kinds of identifier | The module: `public` and `pairwise` |
| `SectorIdentifierSourceInterface`, `SectorIdentifiersInterface` | The sector of a client (OIDC Core §8.1), read through every source wired | The module |
| `MetadataContributorInterface` | What one capability adds to the discovery document | The module, one contributor per capability |
| `FlowPicturesInterface` | The flows served, one picture per wired grant | The module, from the wired grants |
| `ServedResponseModesInterface` | The response modes of the authorization endpoint | The bundle, one renderer per mode |
| `ServedLogoutChannelsInterface` | The logout channels served | The bundle |
| `ProvableMethodsInterface` | What the logins of the deployment can prove, as `amr` values | The bundle, over the logins of the firewall |

[Discovery and JWKS](discovery-and-jwks.md) says what the discovery document makes of them.

## What ships in the package

The package carries the implementations that need nothing but its own dependencies, under
`Beffroi\Oidc\Bridge`:

| Namespace | What is in it |
|---|---|
| `Configuration` | The clients, the registration policy and the trusted issuers, read from what a deployment declares and validated when it starts |
| `JwtLibrary` | The reader of a compact JWT, the verifier of a client's signature, of a DPoP proof and of a `client_secret_jwt` MAC, and the JWE encrypter, on `web-token/jwt-library` |
| `Pki` | The reader of a client certificate, on `spomky-labs/pki-framework` |
| `Null` | `NoDpopNonce`, the provider that asks no nonce of a proof |
| `InMemory` | The stores, the replay guards, the cache of the keys of a client and a pairwise salt, for tests and examples: nothing in them survives the process |

The stores that outlive a request, the router, the HTTP client and the lanes are the integration's, which is
what the bundle provides.
