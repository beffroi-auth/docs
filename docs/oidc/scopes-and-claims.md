---
title: Scopes and claims
description: The scopes a client may ask for, the claims each one stands for, the claims parameter, and where a claim is read from.
---

# Scopes and claims

A scope is a name for what a client may obtain, and a claim is one thing it learns about a person: a scope of
OpenID Connect stands for a set of claims (OIDC Core §5.4), and the `claims` parameter asks for claims one by
one (OIDC Core §5.5). What a client receives is what its request asked for and the provider holds a value
of: the claims of the scopes the client registered and the person agreed to, and the claims it named in
`claims`. A claim named in `claims` is served whichever scopes the client registered or the person agreed
to, and the [consent page](consent.md) lists scopes and authorization details, not the claims named this way.

## Scopes

| Scope | What it stands for |
|---|---|
| `openid` | That the request is an OpenID Connect authentication. Every authorization request carries it, or is refused with `invalid_scope` |
| `profile` | `name`, `family_name`, `given_name`, `middle_name`, `nickname`, `preferred_username`, `profile`, `picture`, `website`, `gender`, `birthdate`, `zoneinfo`, `locale`, `updated_at` |
| `email` | `email`, `email_verified` |
| `address` | `address` |
| `phone` | `phone_number`, `phone_number_verified` |
| `offline_access` | A refresh token (OIDC Core §11). [Refresh tokens](tokens/refresh-tokens.md) say when one is issued without it |
| Any other | Nothing the provider serves: a scope a client registered, which travels in the `scope` of the access token for the resource server that reads it |

**A client asks for what it registered.** `scope` is a list of scope tokens separated by single spaces
(RFC 6749 §3.3), each made of visible ASCII other than `"` and `\`, and a scope named twice counts once. The
`scope` a client registered is the closed list of what it may ask for: scopes are compared byte for byte, and
a request that names one outside the list is refused with `invalid_scope`.

**The document says what the tenant hands out.** `scopes_supported` lists `openid` first, then the scopes the
wired claims providers stand for, then every scope a client of the tenant registered, then `offline_access`
when a wired grant issues a refresh token and a wired grant spends one. A scope that stands for no claim
exists because a client registered it, so a typing mistake in a registration shows in the document rather
than being granted in silence. A client that [registers itself](dynamic-registration.md) is held to that
list: a scope the tenant does not hand out is refused at its registration.

## Where a claim goes

| Document | What it carries about the person |
|---|---|
| The ID token | `sub`, the claims of the protocol (`auth_time`, `acr`, `amr`, `sid` and the others), and the claims the request asked for by name in `claims.id_token`. Nothing a scope stands for |
| The UserInfo answer | `sub`, the claims the scopes of the access token stand for, and the claims the request asked for by name in `claims.userinfo`, whatever their scope |

So a client reads the claims of `profile` or `email` at UserInfo, and in its ID token only the ones it asked
for by name. The names asked in `claims.userinfo` travel with the access token, in its private claim
`userinfo_claims` for the self-contained shape, so UserInfo knows them when the token comes back. In the ID
token, the claims of the protocol win over a claim of the same name a provider of claims returns; in the
UserInfo answer, `sub` does.

## The claims parameter

``` json
{
    "id_token": {
        "email": null,
        "acr": { "essential": true, "values": ["phr", "2"] }
    },
    "userinfo": {
        "phone_number": null
    }
}
```

`claims` is a JSON object, URL-encoded in the request, whose members `id_token` and `userinfo` each map a
claim name to `null` or to an object with `essential`, a JSON boolean, `value`, a string, a number or a
boolean, and `values`, a non-empty array of those (OIDC Core §5.5.1). A member other than the two is ignored.
A name made of digits, a member of another shape, a document nested deeper than a request needs or anything
that is not JSON is refused with `invalid_request` at the redirect URI. `claims_parameter_supported` is `true`.

What is asked for is served by name, with or without its scope, when the person has a value for it.
`essential`, `value` and `values` say nothing to the provider of claims; the one claim they decide is `acr`,
whose `values` name the classes of authentication a client accepts and whose `essential` makes the request
binding ([interactions](interactions.md)).

## Where a claim is read from

The claims of OIDC Core §5.1 are read from the account of the person in the core ([users](../core/users.md)):

| Claim | Read from |
|---|---|
| `name`, `given_name`, `family_name`, `middle_name`, `nickname`, `preferred_username`, `profile`, `picture`, `website`, `gender`, `birthdate`, `zoneinfo`, `locale` | The profile of the account, one field each |
| `email`, `email_verified` | The address of the account, and whether it was verified |
| `phone_number`, `phone_number_verified` | The phone number of the account, and whether it was verified |
| `address` | The postal address of the account, as an object of the members it holds among `formatted`, `street_address`, `locality`, `region`, `postal_code` and `country` (OIDC Core §5.1.1) |
| `updated_at` | When the account last changed, in seconds since the epoch |

A claim the account holds no value for is left out, its verification flag with it; a flag beside a value is a
JSON boolean, `true` or `false`, never a string. `sub` is not among them: it comes from the kind of subject
the client registered ([pairwise subjects](pairwise-subjects.md)). `claims_supported` lists `sub` and every
claim above.

## Claims of your own

A deployment that serves claims the core does not hold, and the scope that stands for them, adds a class
beside the one that serves the claims of §5.1, implementing `Beffroi\Oidc\Port\ClaimsProviderInterface` and
tagged `beffroi.oidc.claims_provider`:

``` php title="src/Claims/EmployeeClaims.php"
<?php

declare(strict_types=1);

namespace App\Claims;

use Beffroi\Core\Domain\Identity\User;
use Beffroi\Oidc\Domain\Scope\Scope;
use Beffroi\Oidc\Domain\Scope\Scopes;
use Beffroi\Oidc\Port\ClaimsProviderInterface;
use Symfony\Component\DependencyInjection\Attribute\AutoconfigureTag;

#[AutoconfigureTag('beffroi.oidc.claims_provider')]
final readonly class EmployeeClaims implements ClaimsProviderInterface
{
    /**
     * @param EmployeeDirectory $directory where this deployment keeps its employee numbers
     */
    public function __construct(
        private EmployeeDirectory $directory,
    ) {
    }

    public function claims(User $user, ?Scopes $scopes, array $requested): array
    {
        $due = isset($requested['employee_number']) || ($scopes?->has(new Scope('employee')) ?? false);
        $number = $due ? $this->directory->numberOf($user->subject->value) : null;

        return $number === null ? [] : ['employee_number' => $number];
    }

    public function supportedScopes(): array
    {
        return [new Scope('employee')];
    }

    public function supportedClaims(): array
    {
        return ['employee_number'];
    }
}
```

`$scopes` is `null` when the document is an ID token, which carries what was asked for by name and nothing a
scope stands for, and `$requested` holds the names asked for by the request, for the document being written.
A claim without a value is left out of what the method returns. What the class serves is announced in
`scopes_supported` and `claims_supported`, and a client registers the scope as it registers any other. Two
providers that both return a value for one claim are refused when they meet; two that stand for the same scope
are not, a scope being a name for a set of claims.

[:beffroi-arrow-right: UserInfo](userinfo.md) and [ID tokens](tokens/id-tokens.md)
