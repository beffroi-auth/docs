---
title: Pages
description: The pages a person reads, what each one shows, and how an application gives them its look without breaking what they post.
---

# Pages

The bundle ships the pages a person reads as Twig templates in the `@Beffroi` namespace, translated, and
overridable like any template of any bundle. They carry the structure and the words, never a stylesheet: an
application gives them their look by overriding one file, and any page it wants otherwise by its name. The
scripts they load are the bundle's own, served by the bundle under the path of its routes, so a deployment has
nothing to build for them; the pages that post a form carry one line of script of their own, named by its
hash.

## Making them yours

A template of the bundle is overridden by a file of the same name under `templates/bundles/BeffroiBundle/` of
the application. Every page extends `layout.html.twig` but the four that carry a step of the protocol, so
overriding that one file gives every page its look, and the pages come with it untouched:

``` twig title="templates/bundles/BeffroiBundle/layout.html.twig"
<!DOCTYPE html>
<html lang="{{ app.request.locale|replace({'_': '-'}) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="{{ asset('styles/app.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
    {% block brand %}{% include '@Beffroi/_brand.html.twig' %}{% endblock %}
    {% block body %}
        <main>
            <h1>{% block heading %}{{ block('title') }}{% endblock %}</h1>
            {% block action %}{% endblock %}
            {% block content %}{% endblock %}
        </main>
    {% endblock %}
    {% block locale %}{% include '@Beffroi/_locale_switcher.html.twig' %}{% endblock %}
</body>
</html>
```

| Block | What the pages put in it |
|---|---|
| `title` | The title of the page, which `heading` repeats unless a page says otherwise |
| `head` | The script of the bundle a page needs: `passkey.js` on the login page, the page of passkeys and the enrolment by ticket, `push.js` on the page of notifications, `copy.js` where a value is handed over to copy, `password-strength.js` on the page of the password |
| `brand` | The logo of the tenant, from `_brand.html.twig` |
| `heading` | The heading of the page |
| `action` | The one action a page offers beside its title, when it offers one |
| `content` | The page itself |
| `locale` | The choice of a language, from `_locale_switcher.html.twig` |

A stylesheet goes outside `head`, as above: a page that loads a script fills that block, and its own block
replaces the layout's. The standalone application draws the pages with Tailwind and DaisyUI this way, from a
layout that picks one of two skeletons by the route, one for the pages of an interaction and one for the
pages of the account. The error page sets `beffroi_refusal`, so a layout tells a refusal served on a route of
the account from a page of the account.

The functions and filters the templates read are the bundle's, for a page an application rewrites:

| Twig | What it gives |
|---|---|
| `beffroi_tenant()` | What the page shows of its tenant: `name`, `logoUri`, `primaryColor`, `primaryContentColor`, or nothing when the row of the tenant is missing or disagrees with the configuration |
| `beffroi_locales()` | The languages the deployment serves, the default one first |
| `beffroi_locale_choice()` | The same list, or none when the record of a signed-in person decided the language of the page |
| `beffroi_moment` | A date, on the clock of the person, in the words of the language of the page, the zone always named |
| `beffroi_place`, `beffroi_device` | Where a request came from, and the browser it named |

[:beffroi-arrow-right: Translations](translations.md)

## What a tenant shows of itself

The logo the tenant declared is on every page that keeps the `brand` block, with the name of the tenant as
the text that stands in for it, so a reader who does not see the image is told who they came for. It is loaded
by the browser of the visitor, never by the provider, and with no referrer. A tenant that declares no logo
renders nothing there.

The two colours the tenant declares, the one the buttons and the links are drawn in and the one of what is
written on them, are read by the layout of the application, since the look of the pages is the
application's: the bundle applies no colour. The standalone application writes them as two custom properties
of a `style` element carrying the nonce of the response.

The consent page shows the logo of the asking client beside the one of the tenant, and adds the origins both
are served from to the `img-src` of the policy its answer carries. Every other page is served under the
policy of the deployment alone, so that policy allows the origin the logo of the tenant is served from: the
standalone application serves it from its own origin, which its `img-src 'self'` allows.

[:beffroi-arrow-right: What the configuration says of a tenant](../core/tenants.md#what-the-configuration-says)

## The pages

| Template | Served at | What it is |
|---|---|---|
| `login.html.twig` | `/login` | Where a person proves who they are |
| `login_address.html.twig` | `/login` | The address asked first, on a tenant that federates domains |
| `code.html.twig` | `/login/code` | The second step: a code of the authenticator application, or a backup code |
| `consent.html.twig` | `/consent` | What a client asks for, and the answer |
| `logout.html.twig` | `/logout` | The confirmation of a logout the request did not prove it may make |
| `logged_out.html.twig` | `/logout`, and after the end of a session | Signed out, or still signed in after choosing to stay |
| `device.html.twig`, `device_approval.html.twig`, `device_answered.html.twig` | `/device` | The code a device shows, what it asks for, and the answer given |
| `approvals.html.twig`, `approval_answered.html.twig` | `/account/approvals` | What somebody waits on an answer for, and the answer given |
| `enrolment_ticket.html.twig` | `/enrol/{ticket}/{value}` | The first passkey of a person, posed without a session |
| `error.html.twig` | Wherever a request stops | The refusal, when nothing may be sent back to a client |
| `account/*.html.twig` | `/account` and below | [The account pages](account.md) |
| `form_post.html.twig`, `saml_post.html.twig`, `post_again.html.twig` | Wherever an answer goes back in a form: an authorization response, a SAML message, a post from another site | A form the browser posts on its own |
| `front_channel_logout.html.twig` | The end of a session whose clients registered a front-channel logout URI | The frames of Front-Channel Logout 1.0 §3 |

`scopes.html.twig` and `authorization_details.html.twig` write the scopes and the details of a request the
same way on the consent page and on the pages of the account; `_brand.html.twig` and
`_locale_switcher.html.twig` are included by the layout.

### The login page

**It offers what the tenant admits.** It shows the logins the firewall wires that the [floor of the
tenant](../core/tenants.md#the-floor-of-its-logins) accepts: a tenant that signs its people in by passkey
shows no password field and no username, the passkey naming its own user. A tenant that federates domains to
[upstream identity providers](../saml/federated-sign-in.md#the-login-page-asks-for-the-address-first) asks for
the address first, one field and nothing else, and sends an address of those domains to its provider.

The password form comes first. The passkey form is hidden until the script finds a browser that can hold a
passkey, then shows a button, and the username field offers the passkeys the browser holds when it can
(`autocomplete="username webauthn"`). A refused login shows one message, whatever the reason. On a step-up
the page names the classes the client accepts and says which kinds of credential the person holds would
reach one. A login asked for by a page of the provider names no client.

### The consent page

Who is asking is what the client registered of itself: its name, its logo, and the pages a person may read
before deciding, `policy_uri`, `tos_uri` and `client_uri` in that order, each opened with no referrer. Then
the person signed in, every scope of the request, the standard scopes of OIDC Core §5.4 in words and any
other by its value, and what the request asks for beyond its scopes (RFC 9396 §2) in the words of its type.
Allowing ends with the code carried to the client, so the page adds the origin of its redirection URI to the
`form-action` of its policy.

### The logout pages

The logout asks for a confirmation when the request did not prove it is about the session the browser holds
(OIDC RP-Initiated Logout 1.0 §2), and the form posts the same parameters back with the answer. After it, the
page says the person is signed out, or still signed in when they chose to stay. When clients of the session
registered a front-channel logout URI, the page that loads them in frames is served once the session has
ended, and goes on to where the logout was going.

[:beffroi-arrow-right: Logout](../oidc/logout.md)

### The device pages

The first page asks for the code a device shows, one field and nothing else, and one message when the code
names no request awaiting an answer, whatever the reason. The second says what the code names: the provider
that is asking, the person signed in, the client that asked and the code, where the device asked from, every
scope of the request, and a warning that somebody who started nothing refuses. Nothing is approved on a
`GET`: the answer is a post of that page.

### The pages that post a form

Three pages carry a message of the protocol rather than a page of the product: the answer of the
authorization endpoint in `response_mode=form_post` (OAuth 2.0 Form Post Response Mode §2), a SAML message to a
peer, and a form another site posted without the session cookie, posted again from the provider's own origin.
None of them extends the layout. Each carries the policy `default-src 'none'` and submits itself with the one
script that policy names by its hash, and keeps a button for a browser that runs no script; their words are
translated like every other page's. The page of the front-channel logout is built the same way, its policy
naming the frames it opens.

!!! warning "The script of these pages is their policy"

    They can be overridden like any other, as long as the script is kept exactly as it is given: the hash in
    the `Content-Security-Policy` is the hash of that script, and a script that differs by a character does
    not run.

## The headers of a page

Every page the bundle renders on the interaction plane carries these, and the pages that post a form carry
their own policy in place of the floor:

| Header | Value |
|---|---|
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | `frame-ancestors 'none'` |
| `Referrer-Policy` | `no-referrer` |
| `Cache-Control` | `no-store`; `no-cache, no-store`, with `Pragma: no-cache`, on the page that posts a SAML message and on the page that posts a form again |

`frame-ancestors 'none'` is a floor: it restricts framing and nothing else, and a deployment that wants a
whole policy on these pages writes it, as the standalone application does. A page that has something to say
about the request it answers never writes a policy of its own: it adds what it needs to whichever policy the
answer carries, the enforced one and the one that only reports, once that policy is written.

- The login page, the code page and the consent page add the origin of the redirection URI of the client to
  `form-action`, since a browser checks that directive over the whole chain of redirections of a submission,
  the last of which carries the code to the client. The logout confirmation adds the origin of the
  post-logout redirection URI, and the origin of the single logout service of each SAML service provider the
  logout goes through.
- The consent page adds the origins of the two logos it shows to `img-src`.

A policy that names no `form-action` is left alone, that directive falling back to no other; a policy that
names `default-src` and no `img-src` gets an `img-src` written out of it, with the origins added.

The scripts are served with `Cache-Control: public` for an hour and an `ETag`:

| Path | Read by |
|---|---|
| `/passkey.js` | The login page, the enrolment of a passkey on the account and by ticket |
| `/push.js`, `/push-worker.js` | The page of notifications, and the service worker it registers |
| `/copy.js` | The pages that hand over a value to copy, the key of an authenticator application and the backup codes |
| `/password-strength.js` | The page of the password |

## What an override keeps

A page is free to move, reword or restyle anything, and three things are read by something else. **The
fields of a form**, which a controller or an authenticator reads by name. **The form tokens**, each rendered
under its identifier with `csrf_token()`. **The `data-*` attributes the scripts read**, and the `?interaction=`
the actions carry, or the `interaction` field of the consent form, which is how a post finds its
interaction.

| Form | Fields | Token |
|---|---|---|
| Password login | `_username`, `_password` | `_csrf_token`, `authenticate` |
| Passkey login | `_passkey`, in a form marked `data-passkey="login"` naming its options in `data-options-url`, with a `data-passkey-button` and a `data-passkey-error` | `_csrf_token`, `authenticate` |
| Second step | `_code` | `_csrf_token`, `authenticate` |
| Address first | `_address` | `_token`, `beffroi_login_address` |
| Consent | `interaction`, `answer` with `allow` or `deny` | `_token`, `beffroi_consent` |
| Logout | The parameters of the request, `confirm` with `yes` or `no` | `_token`, `beffroi_logout` |
| Device | `user_code`, and `answer` with `allow` or `deny` on the second page | `_token`, `beffroi_device` |
| Language | `locale`, `target`, and `interaction` when there is one | `_token`, `beffroi_locale` |

[:beffroi-arrow-right: Security](security.md#form-tokens)
