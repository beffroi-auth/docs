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
metadata before the list of the community, and so are the families of keys a thread of the server and the
worker open when they start. Every other list of several implementations of one interface, a
port, an interface of the model or an interface of the bridge, is fed by a tag, every service carrying the tag
being in it, and a list a role switches takes as well the services of that role while the role is on:

| Tag | What the class implements | What reads the tagged list |
|---|---|---|
| `beffroi.password_algorithm` | `PasswordAlgorithmInterface` | `WiredPasswordAlgorithms`, the hasher of the first wired making every new hash |
| `beffroi.password_hasher` | `AlgorithmPasswordHasherInterface` | `PasswordHasherRegistry`, which hands each hash to the hasher that supports its algorithm |
| `beffroi.retirement_hold` | `RetirementHoldInterface` | `KeyRetirement`, which leaves in service a key one of them still needs, unless an operator forces its retirement |
| `beffroi.chain` | `ChainInterface` | The step that signs the head of every chain, and the commands that name one |
| `beffroi.authentication_predicate` | `AuthenticationPredicateInterface` | `WiredAuthenticationPredicates`, which the `acr` vocabulary and the floor of a tenant name predicates from |
| `beffroi.passkey_attestation_policy` | `PasskeyAttestationPolicyInterface` | `WiredPasskeyAttestationPolicies`, which the policy of passkey attestation of a tenant is named from |
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
| `TenantRepositoryInterface` | `save` | Where what a tenant decided of itself is written, the floor of its logins and the contact it gives its people | `DoctrineTenantRepository` (application) |
| `AmbientTenantInterface` | `provide` | The tenant of the unit of work in progress, for what is not a use case, such as a column type; it names that tenant or throws | `TenantProvider` (application) |
| `LinkedIdentityRepositoryInterface` | `find`, `save` | A linked identity by its provider and its subject | `DoctrineLinkedIdentityRepository` (application) |
| `LinkedIdentitiesOfAPersonInterface` | `of` | The linked identities of one person, for their archive | `DoctrineLinkedIdentityRepository` (application) |
| `UpstreamProvidersInterface` | `of` | The upstream providers a tenant declares, whatever their protocol | `SamlUpstreamProviders` (application) |
| `ClaimsInterface` | `named` | A claim a person is described with in this deployment, by its name of OIDC Core §5.1, or nothing when nothing wired answers that name: what a profile written at the console is held to | `WiredClaims` (application) |
| `ClaimHistoryInterface` | `record` | Where a change of a claim is written, taking the next position of the chain of the history of its tenant | `DoctrineClaimHistory` (application) |
| `ChangesOfAPersonInterface` | `lastOf`, `everyChangeOf` | The changes of one person, the last few or all of them in pages | `DoctrineClaimHistory` (application) |
| `CanPageChangesOfAPersonInterface` | `pageOfChanges` | One page of those changes, over a period | `DoctrineClaimHistory` (application) |
| `AtomicWritesInterface` | `atomically` | Several writes that are one fact, all of them kept or none | `DoctrineAtomicWrites` (application) |
| `UuidGeneratorInterface` | `timeOrdered`, `opaque` | A UUID version 7 for a row, a version 4 for a value a party sees, a subject above all | `SymfonyUuidGenerator` (core) |
| `RandomnessInterface` | `bytes` | The bytes of the secret values drawn through it, an authorization code, a refresh token, a TOTP secret and a backup code among them | `PlatformRandomness` (core) |
| `CanCountUsersInterface` | `countUsersIn` | How many people a tenant has, whatever their state, and nothing of anybody: the statistics of the instance | `DoctrineUserRepository` (application) |

## Groups

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `GroupRepositoryInterface` | `findByName`, `save` | The groups of a tenant, by their exact name | `DoctrineGroupRepository` (application) |
| `GroupMembershipRepositoryInterface` | `save`, `remove` | Where a membership is written and taken back | `DoctrineGroupMembershipRepository` (application) |
| `GroupsOfAPersonInterface` | `of` | The memberships of one person with their sources | `DoctrineGroupMembershipRepository` (application) |
| `GroupsOfATenantInterface` | `of`, `find` | The groups of a tenant, all of them or one by its identifier | `DoctrineGroupRepository` (application) |
| `MembersOfAGroupInterface` | `membersOf`, `countMembersOf` | The members of one group a page at a time, or how many it holds, which delivers none of them | `DoctrineGroupMembershipRepository` (application) |
| `AdministratorGroupsInterface` | `groupsAdministering` | The names of the groups whose members [administer a tenant](../../administrators/people/groups.md#who-administers-the-tenant), none for a tenant nobody administers | `ConfigurationAdministratorGroups` (core), from `tenant.administrators` |

## Credentials

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `CredentialRepositoryInterface` | `findByUser`, `find`, `findByExternalId`, `save` | The credentials of a person, of one kind or of all, the revoked ones included | `DoctrineCredentialRepository` (application) |
| `CanPageCredentialsInterface` | `pageOfCredentials` | One page of the credentials of one kind a person holds | `DoctrineCredentialRepository` (application) |
| `CanForgetCredentialsInterface` | `credentialsOf`, `forget` | Every credential of a tenant, and the removal of one, for the floor that forgets them | `DoctrineCredentialRepository` (application) |
| `PasswordHasherInterface` | `hash`, `verify`, `needsRehash` | What a use case does with a password | `PasswordHasherRegistry` (core) |
| `AlgorithmPasswordHasherInterface` | `supports`, `hash`, `verify`, `needsRehash` | A hasher of named algorithms, which only the registry calls | `NativePasswordHasher` and `Pbkdf2PasswordHasher`, which verifies the PBKDF2 hashes an import brings and makes none (core), tagged |
| `PasswordAlgorithmsInterface` | `all`, `named`, `defaultAlgorithm` | The algorithms a hash may name, the first naming the hasher of every new one | `WiredPasswordAlgorithms` (core) |
| `PasswordAttemptLimiterInterface` | `attempt`, `reset` | How many passwords may be tried on a person in a window, counted atomically and shared by every process of a deployment | `RateLimitedAttempts` (application), five a minute, under the locks of the database |
| `CodeAttemptLimiterInterface` | `mayAttempt`, `attempt` | How many codes a person may try in a window, counted the same way | `RateLimitedAttempts` (application), five a minute, under the locks of the database |
| `TotpUsesInterface` | `acceptStep`, `spendBackupCode` | The use of a code of an authenticator application or of a backup code, recorded atomically: of two requests presenting one code at once, one is accepted and the other refused as replayed (RFC 6238 §5.2) | `DoctrineTotpUses` (application) |
| `PasskeyUsesInterface` | `recordUse` | The use of a passkey and its sign count, recorded atomically: of two assertions carrying one counter at once, one signs in (WebAuthn Level 3 §6.1.1) | `DoctrinePasskeyUses` (application) |
| `BreachedPasswordsInterface` | `looksUp`, `timesSeen` | What a list of compromised passwords says of a digest | `PwnedPasswords` (application) |
| `PasskeyRegistrarInterface` | `creationOptions`, `verifyAttestation` | The registration ceremony of WebAuthn Level 3 §7.1 | `WebauthnPasskeyRegistrar` (core) |
| `PasskeyAuthenticatorInterface` | `requestOptions`, `verifyAssertion` | The authentication ceremony of WebAuthn Level 3 §7.2 | `WebauthnPasskeyAuthenticator` (core) |
| `PasskeyAttestationPoliciesInterface` | `named` | The policy of passkey attestation a tenant names, what its enrolment asks of an authenticator (WebAuthn Level 3 §5.4.7), or a refusal naming the wired ones | `WiredPasskeyAttestationPolicies` (core) |
| `AttestationRootReaderInterface` | `read` | A root of passkey attestations a tenant pins, read from its PEM, the certificate of no certificate authority refused (RFC 5280 §4.2.1.9) | `PkiAttestationRootReader` (core) |
| `MetadataBlobStoreInterface` | `write`, `readAll` | The FIDO metadata the ceremonies read | `FileMetadataBlobStore` (application) |
| `AuthenticatorListStoreInterface` | `write`, `read` | The list of passkey providers the community keeps, as the console downloaded it, which names models and nothing else | `FileAuthenticatorListStore` (application) |
| `AuthenticatorModelSourceInterface` | `model` | The make and model a source names for the AAGUID a passkey declared, or nothing; read by the page of the passkeys and the console, by no ceremony | `MetadataAuthenticatorModels`, then `StoredAuthenticatorList` (core), asked in that order by `AuthenticatorModels` |
| `TotpAlgorithmInterface` | `codeAt`, `provisioningUri` | The code of a time step (RFC 6238 §4.2), and the URI an application scans | `OtphpTotpAlgorithm` (core) |
| `SecretSealerInterface` | `seal`, `unseal` | The secret of a TOTP, sealed by the key management service of the tenant | `EnvelopeSecretSealer` (core), one per purpose: what the provider keeps under one, and each sort of secret that leaves it under its own, so that an envelope opens as no other sort |
| `TicketRepositoryInterface` | `find`, `unspentOf`, `holdsSpent`, `save`, `forget` | The tickets of one kind, found by identifier only, the row holding a hash of the value, and whether the store holds one spent since it was read; the three ports below are this one for their kind | `DoctrineTicketRepository` (application), one per kind |
| `EnrolmentTicketRepositoryInterface` | `find`, `unspentOf`, `holdsSpent`, `save`, `forget` | The enrolment tickets of a person | `DoctrineEnrolmentTicketRepository` (application) |
| `PasswordTicketRepositoryInterface` | `find`, `unspentOf`, `holdsSpent`, `save`, `forget` | The password tickets of a person | `DoctrinePasswordTicketRepository` (application) |
| `TotpTicketRepositoryInterface` | `find`, `unspentOf`, `holdsSpent`, `save`, `forget` | The tickets of a person for an authenticator application | `DoctrineTotpTicketRepository` (application) |
| `AddressConfirmationRepositoryInterface` | `find`, `unspentOf`, `save`, `forget` | The confirmations of one kind of address a person asked for, each kind in a store of its own | `DoctrineEmailConfirmationRepository` and `DoctrinePhoneNumberConfirmationRepository` (application) |
| `AddressConfirmationSenderInterface` | `send` | Where the code and the link of a confirmation go, to the address they establish and to it alone | `QueuedAddressConfirmationSender` (application), which puts it on the lane of notifications |
| `ConfirmationSendLimiterInterface` | `spend` | How many confirmations go out for a person and to an address, each counted on a budget of its own, atomically and for every process of a deployment | `RateLimitedConfirmationSends` (application), from the `BEFFROI_CONFIRMATION_SENDS_*` variables |
| `CredentialChangeNotifierInterface` | `tell` | Where a change to the ways a person signs in is handed once it is done, to be [told to that person](../../administrators/people/credentials/index.md#what-the-person-is-told): the act, the kind of the credential when it changed one, when, and the person, and no identifier of what changed | `QueuedCredentialChangeNotifier` (application), which puts it on the lane of notifications |

## Sessions

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `AuthenticationSessionRepositoryInterface` | `find`, `findActiveByUser`, `save` | The sessions of the provider | `DoctrineAuthenticationSessionRepository` (application) |
| `CanPageActiveSessionsInterface` | `pageOfActiveSessions` | One page of the sessions open in the name of a person | `DoctrineAuthenticationSessionRepository` (application) |
| `CanCountActiveSessionsInterface` | `countActiveSessionsIn` | How many sessions of a tenant are open at a moment, neither ended nor expired, and nothing of whose they are | `DoctrineAuthenticationSessionRepository` (application) |
| `CanFindUnendedSessionsInterface` | `findUnendedByUser` | The sessions of one person that nothing has ended, those past their expiry included, for what ends every session of a person but the one it keeps, and for the administration API, which lists them | `DoctrineAuthenticationSessionRepository` (application) |
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
| `RetirementHoldInterface` | `holds`, `name` | What still needs a retiring key past its window, whose retirement waits for it | `FailedMessagesSealedTo` (application), tagged: a message waiting in the failure transport holds the message key it is sealed to |
| `MailSigningKeyRepositoryInterface` | `current`, `ofKind`, `save`, `remove` | The keys a tenant signs its mail with, the current one of each format and the ones it replaced | `FileMailSigningKeyRepository` (application) |
| `OpenableKeysInterface` | `open` | A family of keys of a tenant a process opens when it starts, through the port a request would open them with | `ActiveSigningKeys`, `PublishedDecryptionKeys`, `ActiveKeptSigningKeys`, `KeptDecryptionKeysInService`, `MessageKeysInService`, `ApplicationServerKeysInService` (core, use cases of `Beffroi\Core\Application\Key`) and `DataKeysOfTheTenant` (application) |
| `JwsSignerInterface` | `sign` | A compact JWS signed by the active key of an algorithm | `JwtLibraryJwsSigner` (core) |
| `JwsVerifierInterface` | `verify` | A compact JWS verified against the published keys of the tenant | `JwtLibraryJwsVerifier` (core) |
| `HeldKeyJwsVerifierInterface` | `verify` | A compact JWS the provider signed for itself and keeps, the signed head of a chain, verified against every signing key the tenant holds, retired ones included; never one a third party presents | `JwtLibraryHeldKeyJwsVerifier` (core) |
| `JweDecrypterInterface` | `decrypt` | A compact JWE encrypted to a published key, opened | `JwtLibraryJweDecrypter` (core) |
| `MessageBodySealerInterface` | `seal` | The body of a message sealed to the message key, without asking the key management service anything | `JwtLibraryMessageBodySealer` (core) |
| `MessageBodyOpenerInterface` | `open` | A sealed body opened by the process that consumes it | `JwtLibraryMessageBodyOpener` (core) |

## The journal, the archive and the rest

| Port | Methods | What it answers | Wired to |
|---|---|---|---|
| `JournalInterface` | `record` | Where an act is written, taking the next position of the chain of the journal of its tenant | `DoctrineJournal` (application) |
| `ActsOfAPersonInterface` | `lastOf`, `everyActOf` | The acts of one person, the last of some names or all of them in pages | `DoctrineJournal` (application) |
| `CanPageActsOfAPersonInterface` | `pageOfActs` | One page of the journal of a person | `DoctrineJournal` (application) |
| `CanCountActsInterface` | `countActsSince` | How many acts of each name the journal of a tenant holds since a moment, and nothing of whose they are | `DoctrineJournal` (application) |
| `ChainOfRowsInterface` | `lockedHead`, `head`, `linkedAfter`, `rowsOutsideTheChain`, `forgetUpTo` | The three chains of a tenant, the journal, the history of the claims and what clients were given: each row linked to the one before it, its head locked while a row is appended, read back to be checked, and forgotten from its start past its retention | `DoctrineChains` (application) |
| `RelinkableChainsInterface` | `relink` | A chain linked again as the database holds it, once a person has read what its check found; refused when the store may not rewrite its links | `DoctrineChains` (application) |
| `SignedCheckpointsInterface` | `last`, `keep` | The last signed head of each chain, kept where the role of the database cannot write | `FileChainCheckpoints` (application), beside the keys of the tenant |
| `CheckpointCopiesInterface` | `copy` | Where a signed head leaves the instance, so that a copy outlives whoever holds the database and the keys | `LoggedCheckpointCopies` (application), a line of the log channel `chain` |
| `PersonalArchiveRepositoryInterface` | `find`, `latestOf`, `save`, `forget`, `forgetExpired` | The archives people asked for | `DoctrinePersonalArchiveRepository` (application) |
| `ArchiveChapterInterface` | `name`, `of` | One chapter of an archive, read in the clear | Seven chapters of the core and two of `beffroi/oidc`, tagged |
| `ArchiveContainerInterface` | `mediaType`, `extension`, `wrap` | The archive wrapped under the passphrase a person chose | `ZipArchiveContainer` (application) |
| `DeadRecordsInterface` | `forgetWhatIsDead` | The rows of a store that can no longer do anything, dropped and counted | Thirteen stores of the application, tagged |
| `PushSubscriptionRepositoryInterface` | `findActiveByUser`, `findByEndpoint`, `find`, `save` | The browsers of a person the provider may push to | `DoctrinePushSubscriptionRepository` (application) |
| `CanPageActiveSubscriptionsInterface` | `pageOfActiveSubscriptions` | One page of those browsers | `DoctrinePushSubscriptionRepository` (application) |
| `ExclusiveSectionsInterface` | `exclusively` | What runs alone among every process of a deployment, under a name: the redemption of a ticket, so that of two requests redeeming one ticket at once, one writes what it opens and the other is refused | `LockedSections` (application), under the locks of the database |
| `MonotonicClockInterface` | `now`, `waitFor` | A duration measured and waited out, so that a password checked against a hash the hasher would replace takes at least the time of the decoy hash | `PlatformMonotonicClock` (core) |

## What else the bridge of the core ships

The bridge of the core holds nineteen stores in memory, for tests and for an integration of one's own that wires
the core without the stores of the application: `InMemoryUserRepository`, `InMemoryCredentialRepository`,
`InMemoryAuthenticationSessionRepository`, `InMemoryTenantKeyRepository` and their siblings; the journal and the
chains have none. Beside them, `InMemoryTotpUses` and `InMemoryPasskeyUses` record the use of a code or a passkey
on the credential they are handed. The bridge holds three implementations that answer nothing, `NullBreachedPasswords`,
which asks no list, `NullGeoLocator`, which finds no place, and `NullUserAgentParser`, which reads no device, two
sources fixed for tests, `FixedUuidGenerator` and `FixedRandomness`, and the clock of the platform,
`PlatformMonotonicClock`. The protocol has ports of its own, which [the ports of the protocol](../oidc/ports.md)
list.
