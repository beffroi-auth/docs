---
title: The ports of the core
description: The interfaces the outside implements for the core, one capability each, what each one answers, and what implements it in the core and in the application.
---

# The ports of the core

The core asks the outside for what it cannot do itself: storage, randomness, a hasher, the key management
service, the ceremonies of WebAuthn. Each of these is a port, an interface of `Beffroi\Core\Port`, and each port
has one to five methods, so a caller sees what it calls and nothing more. When two callers need disjoint halves of
a store, the store has two ports: a person's page reads `CanPageCredentialsInterface`, where a login reads
`CredentialRepositoryInterface`.

Where a port says what its implementations throw, it says it in its contract, as `@throws`: `JwsSignerInterface`
throws when the tenant has no active key or when the key management service does not answer, and
`GeoLocatorInterface` never throws at all, an address nothing knows being no place.

Beside its ports, the core reads two PSR interfaces it is handed: a clock (PSR-20), which its use cases read the
time from, and an event dispatcher (PSR-14), which the application binds to its event bus ([events](events.md)).

## Where the implementations live

Most ports have one implementation, which the application aliases the interface to; a name in the tables below
is that implementation, in the bridge of the core (`Beffroi\Core\Bridge`) or in the application (`App`). Where
the tables name a class of the application, an integration of one's own around the components implements the
port itself. The sources of the model of an authenticator are a list the wiring names in order, the FIDO
metadata before the list of the community. Every other list of several implementations of one interface, a
port, an interface of the model or an interface of the bridge, is fed by a tag, every service carrying the tag
being in it, and a list a role switches takes as well the services of that role while the role is on:

| Tag | What the class implements | What reads the tagged list |
|---|---|---|
| `beffroi.password_algorithm` | `PasswordAlgorithmInterface` | `WiredPasswordAlgorithms`, the hasher of the first wired making every new hash |
| `beffroi.password_hasher` | `AlgorithmPasswordHasherInterface` | `PasswordHasherRegistry`, which hands each hash to the hasher that supports its algorithm |
| `beffroi.authentication_predicate` | `AuthenticationPredicateInterface` | `WiredAuthenticationPredicates`, which the `acr` vocabulary and the floor of a tenant name predicates from |
| `beffroi.archive_chapter` | `ArchiveChapterInterface` | The archive a person asks for, one chapter per class |
| `beffroi.dead_records` | `DeadRecordsInterface` | The hourly step that drops the rows that can no longer do anything |
| `beffroi.key_bound_artifact` | `KeyBoundArtifactInterface` | The retirement window of a key |
| `beffroi.signature_algorithm` | `JoseSignatureAlgorithmInterface` | `JoseSignatureAlgorithms`, the first wired being the default signature algorithm |
| `beffroi.key_encryption_algorithm` | `JoseKeyEncryptionAlgorithmInterface` | `JoseKeyEncryptionAlgorithms` |
| `beffroi.content_encryption_algorithm` | `JoseContentEncryptionAlgorithmInterface` | `JoseContentEncryptionAlgorithms` |
| `beffroi.message_sealing_algorithm` | `JoseMessageSealingAlgorithmInterface` | `JoseMessageSealingAlgorithms` |
| `beffroi.application_server_algorithm` | `JoseApplicationServerAlgorithmInterface` | `JoseApplicationServerAlgorithms`: the services carrying the tag, none in the application, and `Vapid` while web push is on, which `BEFFROI_WEB_PUSH_SUBJECT` decides |
| `beffroi.claim` | `ClaimInterface` | `WiredClaims`, the claims a person may describe themselves with and an upstream profile may fill |

## Identity

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `UserRepositoryInterface` | `find`, `findBySubject`, `findByUsername`, `findAllByEmail`, `save` | The users of a tenant, a username and an address being found by their blind indexes | `DoctrineUserRepository` (application) |
| `TenantRepositoryInterface` | `save` | Where what a tenant decided of itself is written, the floor of its logins | `DoctrineTenantRepository` (application) |
| `AmbientTenantInterface` | `provide` | The tenant of the unit of work in progress, for what is not a use case, such as a column type; it names that tenant or throws | `TenantProvider` (application) |
| `LinkedIdentityRepositoryInterface` | `find`, `save` | A linked identity by its provider and its subject | `DoctrineLinkedIdentityRepository` (application) |
| `LinkedIdentitiesOfAPersonInterface` | `of` | The linked identities of one person, for their archive | `DoctrineLinkedIdentityRepository` (application) |
| `UpstreamProvidersInterface` | `of` | The upstream providers a tenant declares, whatever their protocol | `SamlUpstreamProviders` (application) |
| `ClaimsInterface` | `named` | A claim a person is described with in this deployment, by its name of OIDC Core §5.1, or nothing when nothing wired answers that name: what a profile written at the console is held to | `WiredClaims` (application) |
| `ClaimHistoryInterface` | `record`, `forgetBefore` | Where a change of a claim is written, and forgotten past its retention | `DoctrineClaimHistory` (application) |
| `ChangesOfAPersonInterface` | `lastOf`, `everyChangeOf` | The changes of one person, the last few or all of them in pages | `DoctrineClaimHistory` (application) |
| `CanPageChangesOfAPersonInterface` | `pageOfChanges` | One page of those changes, over a period | `DoctrineClaimHistory` (application) |
| `AtomicWritesInterface` | `atomically` | Several writes that are one fact, all of them kept or none | `DoctrineAtomicWrites` (application) |
| `UuidGeneratorInterface` | `timeOrdered`, `opaque` | A UUID version 7 for a row, a version 4 for a value a party sees, a subject above all | `SymfonyUuidGenerator` (core) |
| `RandomnessInterface` | `bytes` | The bytes of the secret values drawn through it, an authorization code, a refresh token, a TOTP secret and a backup code among them | `PlatformRandomness` (core) |

## Groups

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `GroupRepositoryInterface` | `findByName`, `save` | The groups of a tenant, by their exact name | `DoctrineGroupRepository` (application) |
| `GroupMembershipRepositoryInterface` | `save`, `remove` | Where a membership is written and taken back | `DoctrineGroupMembershipRepository` (application) |
| `GroupsOfAPersonInterface` | `of` | The memberships of one person with their sources | `DoctrineGroupMembershipRepository` (application) |

## Credentials

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `CredentialRepositoryInterface` | `findByUser`, `find`, `findByExternalId`, `save` | The credentials of a person, of one kind or of all, the revoked ones included | `DoctrineCredentialRepository` (application) |
| `CanPageCredentialsInterface` | `pageOfCredentials` | One page of the credentials of one kind a person holds | `DoctrineCredentialRepository` (application) |
| `CanForgetCredentialsInterface` | `credentialsOf`, `forget` | Every credential of a tenant, and the removal of one, for the floor that forgets them | `DoctrineCredentialRepository` (application) |
| `PasswordHasherInterface` | `hash`, `verify`, `needsRehash` | What a use case does with a password | `PasswordHasherRegistry` (core) |
| `AlgorithmPasswordHasherInterface` | `supports`, `hash`, `verify`, `needsRehash` | A hasher of named algorithms, which only the registry calls | `NativePasswordHasher` (core), tagged |
| `PasswordAlgorithmsInterface` | `all`, `named`, `defaultAlgorithm` | The algorithms a hash may name, the first naming the hasher of every new one | `WiredPasswordAlgorithms` (core) |
| `PasswordAttemptLimiterInterface` | `attempt`, `reset` | How many passwords may be tried on a person in a window | `RateLimitedAttempts` (application), five a minute |
| `CodeAttemptLimiterInterface` | `mayAttempt`, `attempt` | How many codes a person may try in a window | `RateLimitedAttempts` (application), five a minute |
| `BreachedPasswordsInterface` | `looksUp`, `timesSeen` | What a list of compromised passwords says of a digest | `PwnedPasswords` (application) |
| `PasskeyRegistrarInterface` | `creationOptions`, `verifyAttestation` | The registration ceremony of WebAuthn Level 3 §7.1 | `WebauthnPasskeyRegistrar` (core) |
| `PasskeyAuthenticatorInterface` | `requestOptions`, `verifyAssertion` | The authentication ceremony of WebAuthn Level 3 §7.2 | `WebauthnPasskeyAuthenticator` (core) |
| `MetadataBlobStoreInterface` | `write`, `readAll` | The FIDO metadata the ceremonies read | `FileMetadataBlobStore` (application) |
| `AuthenticatorListStoreInterface` | `write`, `read` | The list of passkey providers the community keeps, as the console downloaded it, which names models and nothing else | `FileAuthenticatorListStore` (application) |
| `AuthenticatorModelSourceInterface` | `model` | The make and model a source names for the AAGUID a passkey declared, or nothing; read by the page of the passkeys and the console, by no ceremony | `MetadataAuthenticatorModels`, then `StoredAuthenticatorList` (core), asked in that order by `AuthenticatorModels` |
| `TotpAlgorithmInterface` | `codeAt`, `provisioningUri` | The code of a time step (RFC 6238 §4.2), and the URI an application scans | `OtphpTotpAlgorithm` (core) |
| `SecretSealerInterface` | `seal`, `unseal` | The secret of a TOTP, sealed by the key management service of the tenant | `EnvelopeSecretSealer` (core) |
| `EnrolmentTicketRepositoryInterface` | `find`, `unspentOf`, `save`, `forget` | The enrolment tickets of a person | `DoctrineEnrolmentTicketRepository` (application) |

## Sessions

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `AuthenticationSessionRepositoryInterface` | `find`, `findActiveByUser`, `save` | The sessions of the provider | `DoctrineAuthenticationSessionRepository` (application) |
| `CanPageActiveSessionsInterface` | `pageOfActiveSessions` | One page of the sessions open in the name of a person | `DoctrineAuthenticationSessionRepository` (application) |
| `CanFindUnendedSessionsInterface` | `findUnendedByUser` | The sessions of one person that nothing has ended, those past their expiry included, for what ends every session of a person but the one it keeps | `DoctrineAuthenticationSessionRepository` (application) |
| `SubjectsOfSessionsInterface` | `of` | The subject of the person a session names, read where the store keeps it in the clear, so that announcing a replayed code, a reused refresh token or a token a client gave back asks nothing of the key management service | `DoctrineAuthenticationSessionRepository` (application) |
| `AuthenticationPredicatesInterface` | `named` | A predicate of the `acr` policy by its name, refused when nothing wired carries it | `WiredAuthenticationPredicates` (core) |
| `GeoLocatorInterface` | `locate` | The place of an address, on the lane and never on the path of a request | `GeoLite2GeoLocator` (application) |
| `UserAgentParserInterface` | `parse` | A device read from a user agent | `NullUserAgentParser` (core), which reads none |

## Keys and sealing

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `TenantKeyRepositoryInterface` | `find`, `findActive`, `findInService`, `findAll`, `save` | The keys of a tenant, whatever they are for | `FileTenantKeyRepository` (application) |
| `KeyPairGeneratorInterface` | `generate` | A key pair for a wired algorithm, its `kid` the RFC 7638 thumbprint | `JwtLibraryKeyPairGenerator` (core) |
| `KeySealerInterface` | `seal`, `unseal` | The private JWK of a key in an envelope of the key management service, bound to the tenant | `EnvelopeKeySealer` (core) |
| `KeyAlgorithmsInterface` | `all`, `named` | Every algorithm a key may be drawn for | `JoseKeyAlgorithms` (core) |
| `SignatureAlgorithmsInterface` | `all`, `named`, `defaultAlgorithm` | The JWS algorithms the provider signs with | `JoseSignatureAlgorithms` (core) |
| `KeyEncryptionAlgorithmsInterface` | `all`, `named` | The JWE key management algorithms a client encrypts to the provider with | `JoseKeyEncryptionAlgorithms` (core) |
| `ContentEncryptionAlgorithmsInterface` | `all`, `named` | The JWE content encryption algorithms the provider opens | `JoseContentEncryptionAlgorithms` (core) |
| `ApplicationServerAlgorithmsInterface` | `all`, `named` | The algorithms of the keys handed to browsers for web push | `JoseApplicationServerAlgorithms` (core) |
| `MessageSealingAlgorithmsInterface` | `all`, `defaultAlgorithm`, `named` | The algorithm of the key message bodies are sealed to | `JoseMessageSealingAlgorithms` (core) |
| `RotationSchedulesInterface` | `of` | The staging delay and the age of the family of an algorithm | `JoseKeyAlgorithms` (core) |
| `KeyBoundArtifactInterface` | `keyUse`, `longestLifetime` | A kind of artifact bound to a key, and how long it stays usable | Six kinds of `beffroi/oidc`, tagged |
| `SigningKeyProviderInterface` | `activeKey` | The active key of a signature algorithm, opened | `SealedKeyProvider` (core) |
| `SigningKeyOpenerInterface` | `open` | The active key of a signature algorithm opened first, before a caller spends what it cannot get back, and what signs under it afterwards without asking the key management service anything | `JwtLibraryJwsSigner` (core) |
| `DecryptionKeyProviderInterface` | `decryptionKey` | The published key a JWE names, opened | `SealedKeyProvider` (core) |
| `PublicKeySetProviderInterface` | `publicKeys` | The JWK Set of the tenant, which opens nothing | `SealedKeyProvider` (core) |
| `KeptSigningKeyProviderInterface` | `activeKeptSigningKey` | The active key of a kept algorithm that signs, the SAML key | `SealedKeyProvider` (core) |
| `KeptDecryptionKeyProviderInterface` | `keptDecryptionKeys` | The kept keys a peer encrypts to, the keys of an upstream SAML identity provider | `SealedKeyProvider` (core) |
| `ApplicationServerKeyProviderInterface` | `activeApplicationServerKey`, `applicationServerKey` | The key a browser is handed, and the key a subscription was made under | `SealedKeyProvider` (core) |
| `MessageKeyProviderInterface` | `sealingKey`, `messageKey` | The key a body is sealed to, and the key a sealed body names | `SealedKeyProvider` (core) |
| `JwsSignerInterface` | `sign` | A compact JWS signed by the active key of an algorithm | `JwtLibraryJwsSigner` (core) |
| `JwsVerifierInterface` | `verify` | A compact JWS verified against the published keys of the tenant | `JwtLibraryJwsVerifier` (core) |
| `JweDecrypterInterface` | `decrypt` | A compact JWE encrypted to a published key, opened | `JwtLibraryJweDecrypter` (core) |
| `MessageBodySealerInterface` | `seal` | The body of a message sealed to the message key, without asking the key management service anything | `JwtLibraryMessageBodySealer` (core) |
| `MessageBodyOpenerInterface` | `open` | A sealed body opened by the process that consumes it | `JwtLibraryMessageBodyOpener` (core) |

## The journal, the archive and the rest

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `JournalInterface` | `record`, `forgetBefore` | Where an act is written, and forgotten past its retention | `DoctrineJournal` (application) |
| `ActsOfAPersonInterface` | `lastOf`, `everyActOf` | The acts of one person, the last of some names or all of them in pages | `DoctrineJournal` (application) |
| `CanPageActsOfAPersonInterface` | `pageOfActs` | One page of the journal of a person | `DoctrineJournal` (application) |
| `PersonalArchiveRepositoryInterface` | `find`, `latestOf`, `save`, `forget`, `forgetExpired` | The archives people asked for | `DoctrinePersonalArchiveRepository` (application) |
| `ArchiveChapterInterface` | `name`, `of` | One chapter of an archive, read in the clear | Seven chapters of the core and two of `beffroi/oidc`, tagged |
| `ArchiveContainerInterface` | `mediaType`, `extension`, `wrap` | The archive wrapped under the passphrase a person chose | `ZipArchiveContainer` (application) |
| `DeadRecordsInterface` | `forgetWhatIsDead` | The rows of a store that can no longer do anything, dropped and counted | Nine stores of the application, tagged |
| `PushSubscriptionRepositoryInterface` | `findActiveByUser`, `findByEndpoint`, `find`, `save` | The browsers of a person the provider may push to | `DoctrinePushSubscriptionRepository` (application) |
| `CanPageActiveSubscriptionsInterface` | `pageOfActiveSubscriptions` | One page of those browsers | `DoctrinePushSubscriptionRepository` (application) |

## What else the bridge of the core ships

The bridge of the core holds fifteen stores in memory, for tests and for an integration of one's own that wires
the core without the stores of the application: `InMemoryUserRepository`, `InMemoryCredentialRepository`,
`InMemoryAuthenticationSessionRepository`, `InMemoryTenantKeyRepository` and their siblings; the journal has
none. It holds three implementations that answer nothing, `NullBreachedPasswords`, which asks no list,
`NullGeoLocator`, which finds no place, and `NullUserAgentParser`, which reads no device, and two sources fixed
for tests, `FixedUuidGenerator` and `FixedRandomness`. The protocol has ports of its own, which [the ports of
the protocol](../oidc/ports.md) list.
