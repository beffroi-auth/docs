---
title: Authorization details
description: Asking for what a scope cannot say, RFC 9396: the types a deployment wires, how a request is judged, what the person reads and what the token carries.
---

# Authorization details

A scope says what kind of thing a client may do; `authorization_details` says what it may do, to what, and
how much (RFC 9396 §2): pay this invoice, up to this amount, from this account. It is a JSON array of
objects, each naming its type in `type`, and it is the one thing an authorization carries that a person has
to be able to read before agreeing to it, rather than recognise.

## A type is a class of the deployment

The bundle wires no type. A type says what a client may do to what in the words of one domain, so no type is
universal, and a deployment that serves rich authorization requests wires the one its domain needs. A
provider wired with none refuses every `authorization_details` of a request that reads one, and announces
nothing. The requests that read one are an authorization request, a pushed request and a token request of
the `authorization_code` or `refresh_token` grant; every other request ignores it, as it ignores any
parameter it does not read.

A type implements `Beffroi\Oidc\Domain\AuthorizationDetails\AuthorizationDetailTypeInterface`, names itself,
and validates its own members: it is the only place that knows what a detail of its kind means. It returns
the detail it accepted, building the members it keeps in an order of its own, so that two requests asking for
the same thing in a different order produce the same detail, and the parameters the consent page renders it
with. A detail it refuses, it refuses by throwing `Beffroi\Oidc\Exception\InvalidArgumentException`.

``` php title="src/AuthorizationDetails/AccountAccessType.php"
<?php

declare(strict_types=1);

namespace App\AuthorizationDetails;

use Beffroi\Oidc\Domain\AuthorizationDetails\AuthorizationDetail;
use Beffroi\Oidc\Domain\AuthorizationDetails\AuthorizationDetailTypeInterface;
use Beffroi\Oidc\Exception\InvalidArgumentException;
use Symfony\Component\DependencyInjection\Attribute\AutoconfigureTag;

#[AutoconfigureTag('beffroi.oidc.authorization_detail_type')]
final readonly class AccountAccessType implements AuthorizationDetailTypeInterface
{
    public function type(): string
    {
        return 'account_access';
    }

    public function of(array $members): AuthorizationDetail
    {
        $account = $members['account'] ?? null;
        if (! is_string($account) || preg_match('/^[A-Za-z0-9-]{1,64}$/D', $account) !== 1) {
            throw new InvalidArgumentException('A detail of the type "account_access" names its account in "account".');
        }
        $actions = $members['actions'] ?? null;
        if (! is_array($actions) || ! array_is_list($actions) || $actions === []) {
            throw new InvalidArgumentException('A detail of the type "account_access" lists its actions in "actions".');
        }
        foreach ($actions as $action) {
            if (! in_array($action, ['read', 'write'], true)) {
                throw new InvalidArgumentException('The actions of a detail of the type "account_access" are read and write.');
            }
        }
        $actions = array_values(array_unique($actions));
        sort($actions);

        return new AuthorizationDetail(
            'account_access',
            ['account' => $account, 'actions' => $actions],
            ['account' => $account, 'actions' => implode(', ', $actions)],
        );
    }
}
```

The third argument is what the page says of the detail: the parameters of the message
`authorization_details.<type>` of the `beffroi` domain, which the deployment writes in its own catalogue
([translations](../symfony-bundle/translations.md)):

``` xml title="translations/beffroi+intl-icu.en.xlf"
<trans-unit id="authorization_details.account_access" resname="authorization_details.account_access">
    <source>authorization_details.account_access</source>
    <target>Account {account}: {actions}</target>
</trans-unit>
```

What is wired is what a client may register, what a request may name and what the discovery document
announces in `authorization_details_types_supported` (RFC 9396 §10). Two classes that answer for one `type`
are a wiring the provider refuses to read. The standalone application wires one type, `invoice_payment`,
whose detail names an invoice, the actions asked of it among `read` and `pay`, the locations where it is
used and the most that may be moved.

## Registering the types

``` yaml title="config/packages/beffroi.yaml"
beffroi:
    clients:
        billing:
            # ...
            authorization_details_types: ['account_access']
```

`authorization_details_types` is the closed list of the types a client may ask for, among the ones wired, and
a client that registers none asks for none. A name nothing serves is refused when the client is read, the
refusal listing the types that are wired. A client that registers itself may send the member as well.

## Asking

`authorization_details` is read at the authorization endpoint and at the [pushed authorization request
endpoint](pushed-authorization-requests.md), as the JSON of the array, URL-encoded, and in a [request
object](request-objects.md) as the array itself:

``` json
[
    {
        "type": "account_access",
        "account": "acct-4711",
        "actions": ["read"]
    }
]
```

Each element is an object naming its type, of a type the provider serves and the client registered, holding
what that type accepts. A malformed array, an element that is not an object, an object that names no type, a
member whose name is a number, a type nobody serves, a type the client did not register and a detail its type
refuses are one refusal, `invalid_authorization_details` (RFC 9396 §5), at the redirect URI of an
authorization request and in JSON at the pushed request endpoint. The description names neither the type nor
what the client registered. A detail asked for twice counts once.

The device authorization endpoint and the backchannel authentication endpoint read no
`authorization_details`, and ignore one they are sent.

## What the person reads

The [consent page](consent.md) shows, under the scopes, "*the client* also asks to be allowed to:" and one
line per detail, the message of its type rendered with the parameters the type chose. A consent covers a
detail when it holds an identical one, the same type with the same members: RFC 9396 §7 leaves the comparison
to whoever defines the type, and equality is the one answer that can never grant more than was agreed to. A
request that changes anything in a detail asks again, and a request that asks for no detail is covered by a
consent that holds its scopes. A new agreement adds its details to the ones the consent already held. The
page of the account that lists the applications a person allowed renders the details the same way.

## What the token carries

The code carries the details agreed to, and the token endpoint serves them:

- the token response lists in `authorization_details` the ones it granted, as each type built them, and
  leaves the member out when it granted none (RFC 9396 §7);
- a self-contained access token carries them in its `authorization_details` claim, and the
  [introspection](introspection-and-revocation.md) of an access token, of either shape, describes them in the
  same member (RFC 9396 §9);
- a token request may ask, in `authorization_details`, for a subset of the details of the authorization it
  spends, for `authorization_code` and `refresh_token`: the access token of that response carries the
  subset, and the refresh token stays bound to every detail agreed to, so a later refresh may ask for one the
  narrowed token did not carry. A detail the authorization does not carry is `invalid_authorization_details`.

[:beffroi-arrow-right: Consent](consent.md) and [access tokens](tokens/access-tokens.md)
