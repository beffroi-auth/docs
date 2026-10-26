---
title: The ports of the core
description: The interfaces the outside implements for the core, one capability each, what each one answers, and what implements it in the core and in the bundle.
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
time from, and an event dispatcher (PSR-14), which the bundle binds to its event bus ([events](events.md)).

## Where the implementations live

Most ports have one implementation, which the bundle aliases the interface to; a name in the tables below is that
implementation, in the bridge of the core (`Beffroi\Core\Bridge`) or in the bundle. Where several implementations
of one interface are read as one list, a port, an interface of the model or an interface of the bridge, a tag
feeds that list, every service carrying the tag being in it:

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
| `beffroi.application_server_algorithm` | `JoseApplicationServerAlgorithmInterface` | `JoseApplicationServerAlgorithms`, the configuration of web push tagging the algorithm when web push is turned on |
| `beffroi.claim` | `ClaimInterface` | `WiredClaims`, the claims a person may describe themselves with and an upstream profile may fill |

## Identity

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `UserRepositoryInterface` | `find`, `findBySubject`, `findByUsername`, `findAllByEmail`, `save` | The users of a tenant, a username and an address being found by their blind indexes | `DoctrineUserRepository` (bundle) |
| `TenantRepositoryInterface` | `save` | Where what a tenant decided of itself is written, the floor of its logins | `DoctrineTenantRepository` (bundle) |
| `AmbientTenantInterface` | `provide` | The tenant of the unit of work in progress, for what is not a use case, such as a column type; it names that tenant or throws | `TenantProvider` (bundle) |
| `LinkedIdentityRepositoryInterface` | `find`, `save` | A linked identity by its provider and its subject | `DoctrineLinkedIdentityRepository` (bundle) |
| `LinkedIdentitiesOfAPersonInterface` | `of` | The linked identities of one person, for their archive | `DoctrineLinkedIdentityRepository` (bundle) |
| `UpstreamProvidersInterface` | `of` | The upstream providers a tenant declares, whatever their protocol | `SamlUpstreamProviders` (bundle) |
| `ClaimHistoryInterface` | `record`, `forgetBefore` | Where a change of a claim is written, and forgotten past its retention | `DoctrineClaimHistory` (bundle) |
| `ChangesOfAPersonInterface` | `lastOf`, `everyChangeOf` | The changes of one person, the last few or all of them in pages | `DoctrineClaimHistory` (bundle) |
| `CanPageChangesOfAPersonInterface` | `pageOfChanges` | One page of those changes, over a period | `DoctrineClaimHistory` (bundle) |
| `AtomicWritesInterface` | `atomically` | Several writes that are one fact, all of them kept or none | `DoctrineAtomicWrites` (bundle) |
| `UuidGeneratorInterface` | `timeOrdered`, `opaque` | A UUID version 7 for a row, a version 4 for a value a party sees, a subject above all | `SymfonyUuidGenerator` (core) |
| `RandomnessInterface` | `bytes` | The bytes of the secret values drawn through it, an authorization code, a refresh token, a TOTP secret and a backup code among them | `PlatformRandomness` (core) |

## Groups

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `GroupRepositoryInterface` | `findByName`, `save` | The groups of a tenant, by their exact name | `DoctrineGroupRepository` (bundle) |
| `GroupMembershipRepositoryInterface` | `save`, `remove` | Where a membership is written and taken back | `DoctrineGroupMembershipRepository` (bundle) |
| `GroupsOfAPersonInterface` | `of` | The memberships of one person with their sources | `DoctrineGroupMembershipRepository` (bundle) |

## Credentials

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `CredentialRepositoryInterface` | `findByUser`, `find`, `findByExternalId`, `save` | The credentials of a person, of one kind or of all, the revoked ones included | `DoctrineCredentialRepository` (bundle) |
| `CanPageCredentialsInterface` | `pageOfCredentials` | One page of the credentials of one kind a person holds | `DoctrineCredentialRepository` (bundle) |
| `CanForgetCredentialsInterface` | `credentialsOf`, `forget` | Every credential of a tenant, and the removal of one, for the floor that forgets them | `DoctrineCredentialRepository` (bundle) |
| `PasswordHasherInterface` | `hash`, `verify`, `needsRehash` | What a use case does with a password | `PasswordHasherRegistry` (core) |
| `AlgorithmPasswordHasherInterface` | `supports`, `hash`, `verify`, `needsRehash` | A hasher of named algorithms, which only the registry calls | `NativePasswordHasher` (core), tagged |
| `PasswordAlgorithmsInterface` | `all`, `named`, `defaultAlgorithm` | The algorithms a hash may name, the first naming the hasher of every new one | `WiredPasswordAlgorithms` (core) |
| `PasswordAttemptLimiterInterface` | `attempt`, `reset` | How many passwords may be tried on a person in a window | `RateLimitedAttempts` (bundle), five a minute |
| `CodeAttemptLimiterInterface` | `mayAttempt`, `attempt` | How many codes a person may try in a window | `RateLimitedAttempts` (bundle), five a minute |
| `BreachedPasswordsInterface` | `looksUp`, `timesSeen` | What a list of compromised passwords says of a digest | `PwnedPasswords` (bundle) |
| `PasskeyRegistrarInterface` | `creationOptions`, `verifyAttestation` | The registration ceremony of WebAuthn Level 3 §7.1 | `WebauthnPasskeyRegistrar` (core) |
| `PasskeyAuthenticatorInterface` | `requestOptions`, `verifyAssertion` | The authentication ceremony of WebAuthn Level 3 §7.2 | `WebauthnPasskeyAuthenticator` (core) |
| `MetadataBlobStoreInterface` | `write`, `readAll` | The FIDO metadata the ceremonies read | `FileMetadataBlobStore` (bundle) |
| `TotpAlgorithmInterface` | `codeAt`, `provisioningUri` | The code of a time step (RFC 6238 §4.2), and the URI an application scans | `OtphpTotpAlgorithm` (core) |
| `SecretSealerInterface` | `seal`, `unseal` | The secret of a TOTP, sealed by the key management service of the tenant | `EnvelopeSecretSealer` (core) |
| `EnrolmentTicketRepositoryInterface` | `find`, `unspentOf`, `save`, `forget` | The enrolment tickets of a person | `DoctrineEnrolmentTicketRepository` (bundle) |

## Sessions

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `AuthenticationSessionRepositoryInterface` | `find`, `findActiveByUser`, `save` | The sessions of the provider | `DoctrineAuthenticationSessionRepository` (bundle) |
| `CanPageActiveSessionsInterface` | `pageOfActiveSessions` | One page of the sessions open in the name of a person | `DoctrineAuthenticationSessionRepository` (bundle) |
| `AuthenticationPredicatesInterface` | `named` | A predicate of the `acr` policy by its name, refused when nothing wired carries it | `WiredAuthenticationPredicates` (core) |
| `GeoLocatorInterface` | `locate` | The place of an address, on the lane and never on the path of a request | `GeoLite2GeoLocator` (bundle) |
| `UserAgentParserInterface` | `parse` | A device read from a user agent | `NullUserAgentParser` (core), which reads none |

## Keys and sealing

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `TenantKeyRepositoryInterface` | `find`, `findActive`, `findInService`, `findAll`, `save` | The keys of a tenant, whatever they are for | `FileTenantKeyRepository` (bundle) |
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
| `JournalInterface` | `record`, `forgetBefore` | Where an act is written, and forgotten past its retention | `DoctrineJournal` (bundle) |
| `ActsOfAPersonInterface` | `lastOf`, `everyActOf` | The acts of one person, the last of some names or all of them in pages | `DoctrineJournal` (bundle) |
| `CanPageActsOfAPersonInterface` | `pageOfActs` | One page of the journal of a person | `DoctrineJournal` (bundle) |
| `PersonalArchiveRepositoryInterface` | `find`, `latestOf`, `save`, `forget`, `forgetExpired` | The archives people asked for | `DoctrinePersonalArchiveRepository` (bundle) |
| `ArchiveChapterInterface` | `name`, `of` | One chapter of an archive, read in the clear | Seven chapters of the core and two of `beffroi/oidc`, tagged |
| `ArchiveContainerInterface` | `mediaType`, `extension`, `wrap` | The archive wrapped under the passphrase a person chose | `ZipArchiveContainer` (bundle) |
| `DeadRecordsInterface` | `forgetWhatIsDead` | The rows of a store that can no longer do anything, dropped and counted | Nine stores of the bundle, tagged |
| `PushSubscriptionRepositoryInterface` | `findActiveByUser`, `findByEndpoint`, `find`, `save` | The browsers of a person the provider may push to | `DoctrinePushSubscriptionRepository` (bundle) |
| `CanPageActiveSubscriptionsInterface` | `pageOfActiveSubscriptions` | One page of those browsers | `DoctrinePushSubscriptionRepository` (bundle) |

## What else the bridge of the core ships

The bridge of the core holds fourteen stores in memory, for tests and for whoever wires the core without the
bundle: `InMemoryUserRepository`, `InMemoryCredentialRepository`, `InMemoryAuthenticationSessionRepository`,
`InMemoryTenantKeyRepository` and their siblings; the journal has none. It holds three implementations that
answer nothing, `NullBreachedPasswords`, which asks no list, `NullGeoLocator`, which finds no place, and
`NullUserAgentParser`, which reads no device, and two sources fixed for tests, `FixedUuidGenerator` and
`FixedRandomness`. The protocol has ports of its own, which [the ports of the protocol](../oidc/ports.md) list.
