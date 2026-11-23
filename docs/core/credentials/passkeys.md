---
title: Passkeys
description: WebAuthn enrolment and assertion, what a passkey proves, what a tenant asks of its authenticator, the first passkey of a person who has nothing to sign in with, and the FIDO metadata.
---

# Passkeys

A passkey is a discoverable WebAuthn credential (W3C Web Authentication Level 3), enrolled from the pages of the
account or from an enrolment ticket, and used on its own, with no password in the way. A person holds as many as
they enrol, each with a name they gave it. The provider holds the public key, the counters and the flags of a
passkey, and never anything it could sign with: the private key does not leave the authenticator.

A passkey proves the possession of a key, and it is what lets a client ask for a phishing-resistant
authentication: under the default policy of a tenant, a session a passkey opened answers `phr`, or `phrh` for a
passkey bound to its authenticator ([the classes it answers with](../tenants.md#the-classes-it-answers-with)).

## The relying party

| Parameter | Value |
|---|---|
| Relying party identifier | The host of the issuer (WebAuthn Level 3 §5.4.2) |
| Origin accepted | The origin of the issuer, scheme and port included, so plain HTTP on a loopback host only, as for the issuer |
| Algorithms | ES256 and RS256, COSE `-7` and `-257` (RFC 9053 §2.1, RFC 8812 §2), in that order of preference |
| Challenge | 32 random bytes, drawn for each ceremony (§13.4.3 asks 16 at the least) |
| Resident key | Required: a passkey is a discoverable credential (§5.4.6) |
| User verification | Preferred and never required, so that a security key with no PIN enrols and signs in |
| Attestation | What the [policy of the tenant](#what-the-enrolment-asks) asks (§5.4.7): `none` in the image, `direct` or `enterprise` |

## Enrolling one

On [the page of their passkeys](../../application/account.md#the-pages), `/account/passkeys`, a person adds
one in a click: the page asks for creation options, the browser creates the passkey, and the page posts it back,
named `New passkey` in the language of the page, a name they correct in its line afterwards. The options are
kept in the session of that browser until the passkey comes back, and the page asks for a proof made in the last
five minutes before it lets a passkey be added.

- **The user is named by a handle and not by an identifier.** The user handle of §5.4.3 is 64 random bytes, drawn
  for the first passkey of a person and shared by all of their passkeys, never the subject and never the address
  (§14.6.1). The user entity carries the username as its name, and the `name` claim, or the username, as what the
  authenticator shows.
- **Every passkey the person holds is excluded**, revoked or not, so an authenticator does not enrol twice.
- **What comes back is checked against the options**: the challenge, the origin and the relying party, then the
  record. A credential ID the tenant already holds is refused (§7.1, step 26), so are options drawn for another
  person, a record without its backup flags and a credential of another type than `public-key`.
- **An attestation is verified whatever the policy asks**, in the formats `packed`, `fido-u2f`, `android-key`,
  `tpm` and `apple`; the format `none`, no attestation at all, is taken as it is, and any other format is a
  refusal and never a pass. The policy of the tenant then judges it, below. Its certificates are not kept: the
  passkey keeps what the enrolment proved of its model.
- **The floor of the tenant is asked once the passkey is known.** What a passkey proves is read from the flags of
  its creation, so a tenant whose floor is `phishing_resistant_hardware` refuses a synced passkey once the
  ceremony has answered, and admits one bound to its authenticator.

A passkey enrolled writes the act `credential.enrolled` to the journal of the person.

## What the enrolment asks

The tenant names what the enrolment of a passkey asks of its authenticator, the attestation conveyance of
WebAuthn Level 3 §5.4.7, in `BEFFROI_TENANT_PASSKEY_ATTESTATION`. The policy applies to every enrolment, a
ticket's included.

| Policy | What it enrols | What it refuses | What the passkey keeps |
|---|---|---|---|
| `none`, in the image | Every passkey | Nothing more | The model its authenticator declares |
| `direct` | Every passkey. A full attestation, `basic`, `attca` or `anonca`, of an AAGUID the [FIDO metadata](#the-fido-metadata) know is checked up to the root their statement names | An attestation that does not verify, and a model under a security alert | The model, verified by its attestation, or declared |
| `enterprise` | An attestation that chains up to a root of `BEFFROI_TENANT_PASSKEY_ATTESTATION_ROOTS` and carries the serial number of its authenticator (§8.2.2), or one that chains up to an authority of the tenant itself, `BEFFROI_TENANT_PASSKEY_ATTESTATION_OWN_ROOTS`, under which no serial number is asked | Every other one, and a model under a security alert | `enterprise`, and the serial number when there is one, sealed |

A browser gives an enterprise attestation only for a relying party identifier its configuration, or the
configuration of the authenticator, permits (§5.4.7), here the host of the issuer.

**A model under a security alert** is one whose last status report in the FIDO metadata is a security
notification (FIDO Metadata Service v3.1.1 §3.1.4.2). `BEFFROI_TENANT_PASSKEY_COMPROMISED_MODELS` admits one
under `direct` and `enterprise`, by the AAGUID of its authenticator, until a day written as `2027-03-31`, in UTC
and included: a passkey of that model enrols until then and is marked under alert, and the refusal returns the
day after.

**A person refused by the policy is told why** on the page that enrolled: "Only the keys your organisation gave
you are accepted." under `enterprise`, and "This model is under a security alert and is no longer accepted. Use
another one." for a model under alert. An attestation that does not verify is refused as any other passkey the
provider refuses. The page of the passkeys and `beffroi:user:show` say what each enrolment proved: the model
declared, verified by its attestation, or attested for the organisation with its serial number, and a model
admitted under alert.

**What the policy cannot read is refused** by the first request or command that reads the tenant: a name no
wired policy carries, naming the ones that are wired; `enterprise` with no root at all; a root that is not one
certificate in PEM, or the certificate of no certificate authority (RFC 5280 §4.2.1.9); roots under `none` or
`direct`, which read none; a model admitted under alert under `none`, which proves no model; an AAGUID that is
not one, or admitted twice; and a day written otherwise.

## Signing in with one

The login page asks the browser for a discoverable credential: no username and no list of allowed passkeys, so
the page says nothing of who holds one. The options are drawn for that browser and kept in its session until
the assertion comes back.

The assertion is verified against the passkey of the tenant its credential ID names, the signature first. Then,
so that a refusal costs what a wrong signature costs, the provider refuses a passkey of another tenant, an
assertion whose backup eligibility is not the one of the enrolment, a revoked passkey, a person of a federated
domain and a disabled person.

| What the assertion proves | When |
|---|---|
| `hwk` | Always, for a passkey bound to its authenticator |
| `swk` | Always, for a synced passkey |
| `user` | The authenticator tested the presence of the user, the UP flag of its authenticator data (§6.1) |
| `mfa` | The authenticator verified the user, with a PIN or a biometric it does not name, the UV flag (§6.1) |

Under a floor of `two_factors`, a passkey proves two factors only when the authenticator verified the user: a
security key without a PIN proves the possession of a key, one factor, and that login is refused.

**The counters are read, not trusted.** The sign count and the backup state of the assertion replace the stored
ones (§7.2, step 26). When either count is not zero, a count that did not grow is told, by the event
`passkey.used` that announces the login, and not refused, a synced passkey keeping its count at zero.

## Synced or bound

Whether a passkey may be synced to other devices is the backup eligibility flag its authenticator set when it was
created, which WebAuthn Level 3 §6.1.3 forbids to change. The flag recorded at the enrolment is the one the
provider reads for the rest of the life of that passkey: it decides whether a login with it proves `swk` or
`hwk`, and so, under the default policy, whether the session answers `phr` or `phrh`. An assertion that carries
another flag is refused, as a revoked passkey is, rather than rewriting the record.

## A first passkey from a ticket

A person created on a tenant that signs its people in by passkey has nothing to sign in with, and no password to
be given. An operator issues them a ticket instead:

``` bash
bin/console beffroi:user:enrolment-ticket alice
```

The command prints a link, `/enrol/{ticket}/{value}` under the issuer, once, with the instant it opens until, and
the row keeps a hash of what the link carries, so a store read by somebody else opens nothing. Whoever issued it
hands it over. An administrator issues one through the administration API as well, which answers the link and
that instant once, and the terminal client of the administration shows the link as a QR code the device that
will hold the passkey scans. A ticket opens the enrolment of a passkey whether the person holds one already or
not, so it also serves a person who lost theirs.

- **It opens one enrolment, once.** The page asks the browser for a passkey, and the ticket is spent only when the
  passkey is in the rows: a ceremony that could not finish leaves the person their link.
- **For seventy-two hours**, which covers a weekend between the day it is issued and the day somebody starts.
  What is not used in three days is issued again.
- **One at a time.** Issuing a ticket forgets the unspent ones of that person, so a link forgotten in a mailbox
  stops opening anything the day another is issued. A disabled account gets none.
- **It proves no login.** Once the passkey is posed, the browser is sent to the account, which sends it to sign in
  with that passkey: the session comes from the passkey, never from possession of the link.

A link that opens nothing, an identifier nobody issued, a wrong value, a ticket spent, out of time or of a
disabled person, is answered by the same page with the status `404`, and each of them costs one hash, so neither
the answer nor its time says which it was. An identifier that is not a UUID is no ticket at all, and is answered
`404` without a hash. The passkey the ticket poses is enrolled under the same rules as any
other, the floor of the tenant included. The page needs a browser that can hold a passkey, and says so to one that
cannot. Issuing a ticket is an act of the journal of that person, `enrolment_ticket.issued`, which names the
administrator when one issued it. A [password](passwords.md#setting-one) and an [authenticator
application](totp.md#from-a-ticket) have tickets of their own, which open the same way: once, for seventy-two
hours, one at a time.

## Renaming and revoking

A person renames a passkey in its line on the page of their passkeys, 1 to 255 characters once the whitespace
around it is trimmed, and the event `credential.renamed` carries the name it had. A revoked passkey is a record of what was: its line offers no
field to rename it.

Revoking one is asked for a proof made in the last five minutes, since it is the gesture that can leave somebody
with no way in at all. The passkey never authenticates again and its line stays, listed as revoked with its date;
the sessions it opened are left as they are. An operator revokes one with `beffroi:user:revoke-credential`, and an
administrator through the administration API, which [credentials](index.md#revoked-and-forgotten) describes.

## Not for the people of an organisation

A person whose address is of a domain an [upstream identity provider](../../saml/federated-sign-in.md)
answers for signs in there, and is posed no passkey here: the pages of the account offer them no form, an
enrolment, a ticket's included, is refused, and a passkey they held before their domain was federated is refused
at the login.

## The FIDO metadata

The metadata of the FIDO Alliance say, authenticator by authenticator, what it is and whether it was found
compromised. Two commands store them in `var/webauthn` of the application, a directory no variable moves, and
nothing refreshes them on its own:

``` bash
bin/console beffroi:webauthn:mds-refresh
bin/console beffroi:webauthn:mds-import vendor-statement.json
```

| Command | What it stores |
|---|---|
| `beffroi:webauthn:mds-refresh` | The Metadata BLOB of `https://mds.fidoalliance.org/`, or of each `--url` given, verified before anything is kept: one signature, made by the first certificate of its chain, the chain leading to the root it pins, `GlobalSign Root R46` shipped with the application unless `--root` names another, as a PEM or DER file or an `https` URL. No redirect is followed, and a refused blob keeps nothing |
| `beffroi:webauthn:mds-import` | Metadata statements a manufacturer publishes for keys the service does not list, or that the FIDO conformance tools ship, one authenticator per file, unsigned and trusted as the file is |

The enrolment reads them under the policies that ask for an attestation. Under `direct`, a full attestation of
an AAGUID the metadata know is checked up to the root its statement names and its model is verified, and any
other attestation leaves the model declared, an AAGUID the metadata do not know included. Under `direct` and
`enterprise`, a model under a security alert is refused, save one the tenant admits until a day it names. A
deployment that never ran either command enrols passkeys all the same. The endpoints the FIDO conformance tools
drive keep the rules of the library, the metadata and the status reports included, and never read the policy
of the tenant.
