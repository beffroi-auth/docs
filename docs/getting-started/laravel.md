---
title: Add sign-in to a Laravel application
description: 'Let people sign in to your Laravel application with Beffroi OP, using Laravel Socialite and the socialiteproviders/openidconnect driver.'
---

# Add sign-in to a Laravel application

This guide adds sign-in with Beffroi OP to a Laravel application. It uses Laravel Socialite with the community
driver `socialiteproviders/openidconnect`, since Socialite has no generic OpenID Connect driver of its own.

When you are done, a visitor of your application is sent to Beffroi to sign in, comes back signed in, and can
sign out again.

## What you need

- A Beffroi OP served over HTTPS, and access to its console (`bin/console`).
- A Laravel 13 or higher application, with sessions and a `users` table, as the default skeleton has them.
- The address Beffroi will send people back to, for instance `https://app.example.com/auth/callback`.

## 1. Register your application in Beffroi

Your application registers itself as a client of Beffroi, with a one-time token you issue on the provider.

1. Allow registration with a token: set `BEFFROI_REGISTRATION_MODE=initial_access_token` in the environment of
   the provider.
2. Issue a token that allows one registration:

    ``` bash
    bin/console beffroi:client:token:issue 'laravel' --registrations=1 --days=30
    ```

    The token is printed once. Copy it.

3. Register the application with that token:

    ``` bash
    curl -X POST https://op.example.com/register \
      -H "Authorization: Bearer $INITIAL_ACCESS_TOKEN" -H 'Content-Type: application/json' \
      -d '{
        "client_name": "My Laravel app",
        "redirect_uris": ["https://app.example.com/auth/callback"],
        "post_logout_redirect_uris": ["https://app.example.com/"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": "openid profile email offline_access"
      }'
    # the answer carries client_id and client_secret, shown once
    ```

    A refused registration spends the token as well. Issue a new one before trying again.

4. Keep the `client_id` and the `client_secret` of the answer. The secret is never shown again.

A few values of this request matter:

- **`redirect_uris`** must be exactly the address your application uses. A trailing `/` is enough for Beffroi
  to refuse the sign-in.
- **`post_logout_redirect_uris`** is where people land after signing out. A sign-out that asks to come back
  to an address not listed here is refused.
- **`client_secret_basic`** is the method the driver picks, since Beffroi offers it. Keep it, and do not set
  `token_auth_method` in the driver.
- **`scope`** lists every scope your application will ask for. Any other is refused.

Beffroi deletes a client that registered itself when nobody uses it for ninety days, or within seven days when
it is never used.

[:beffroi-arrow-right: Registration, in detail](../oidc/dynamic-registration.md#the-three-modes)

## 2. Install Socialite and the driver

``` bash
composer require laravel/socialite:^5.0 socialiteproviders/openidconnect
```

The package registers the `openidconnect` driver on its own. You do not need to add an event listener.

## 3. Configure the driver

Add the driver to `config/services.php`:

``` php title="config/services.php"
'openidconnect' => [
    'base_url' => env('OIDC_ISSUER'),        // for instance https://op.example.com
    'client_id' => env('OIDC_CLIENT_ID'),
    'client_secret' => env('OIDC_CLIENT_SECRET'),
    'redirect' => env('OIDC_REDIRECT_URI'),  // exactly as registered at the provider
    'scopes' => ['openid', 'profile', 'email', 'offline_access'],
],
```

Then fill in the values in `.env`:

``` bash title=".env"
OIDC_ISSUER=https://op.example.com
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_REDIRECT_URI=https://app.example.com/auth/callback
```

`OIDC_ISSUER` is the address of Beffroi, exactly as it announces itself. The driver finds everything else from
there.

!!! tip "A certificate from a private authority"

    If the certificate of Beffroi is signed by an authority of your own, add
    `'guzzle' => ['verify' => '/path/ca.crt']` to the same block of `config/services.php`. A certificate from a
    public authority needs nothing.

## 4. Add the sign-in routes

Two routes are enough: one sends the visitor to Beffroi, the other receives them when they come back.

``` php title="routes/web.php"
Route::get('/auth/redirect', fn () => Socialite::driver('openidconnect')->redirect());

Route::get('/auth/callback', function (Request $request) {
    if ($request->filled('error')) {                      // access_denied, invalid_scope...
        abort(403, $request->query('error_description', $request->query('error')));
    }

    $oidc = Socialite::driver('openidconnect')->user();   // checks state and the ID token

    $user = User::updateOrCreate(
        ['email' => $oidc->getEmail()],
        ['name' => $oidc->getName() ?? $oidc->getEmail(), 'password' => Str::random(40)],
    );

    Auth::login($user);
    $request->session()->regenerate();

    return redirect('/dashboard');
});
```

The callback creates the user the first time, finds them again the next times, and opens their session.

!!! warning "Keep the error check"

    When a person refuses to share their data, or something in the request is wrong, Beffroi sends them back
    with an `error` parameter instead of a code. Without the first check of the callback, Laravel answers with
    a `500` error page.

!!! tip "Find your users by their identifier"

    The example finds a user by their email address to stay short. An address can change; the identifier
    Beffroi gives a person, `$oidc->getId()`, does not. Store it and look users up by it.

## 5. Try it

1. Open `https://app.example.com/auth/redirect`. Your browser goes to Beffroi.
2. Sign in. The first time, Beffroi asks you to agree to share your profile and email address with the
   application.
3. Beffroi sends you back to the callback, which signs you in and redirects you to `/dashboard`. That page is
   yours to write, or change the redirect to a page you have.
4. Sign in a second time: the same user is found, and no consent is asked again.

## Sign out

Sending the person to Beffroi signs them out there too:

``` php
return Socialite::driver('openidconnect')->logout($idToken, $postLogoutRedirectUri);
```

- `$idToken` is the ID token your application received at sign-in.
- `$postLogoutRedirectUri` is one of the `post_logout_redirect_uris` you registered, written exactly the same
  way.

Beffroi ends its session and sends the browser back to that address. The refresh token stops working, and so
does the access token wherever Beffroi checks it, at UserInfo and introspection. On that page, `validateLogoutState()` confirms the visitor really comes back from this sign-out.

[:beffroi-arrow-right: Logout](../oidc/logout.md)

## Renew the access token

An access token works for ten minutes by default. Renew it with the refresh token:

``` php
$tokens = Socialite::driver('openidconnect')->refreshToken($refreshToken);
```

`refreshToken()` returns the answer of Beffroi as an array: a new access token and a new ID token, which the
driver does not check. Keep the refresh token you have, since Beffroi does not replace it. It works until
thirty days after the sign-in by default, however often it is used, and stops working when the person signs
out.

[:beffroi-arrow-right: Refresh tokens](../oidc/tokens/refresh-tokens.md)

## Troubleshooting

| What you see | Why | What to do |
|---|---|---|
| Beffroi shows "Request refused", the `redirect_uri` is not registered | The address your application sends differs from the registered one, even by a trailing `/` | Make `OIDC_REDIRECT_URI` exactly one of the `redirect_uris` |
| A `500` error, and `Callback: IdP returned error` in the log of Laravel | Beffroi answered with an `error`, and the callback does not check for it | Keep the error check of [step 4](#4-add-the-sign-in-routes) |
| `error=invalid_scope` | The application asks for a scope it did not register | Register it, or remove it from `scopes` |
| A `500` error, and a `ClientException` with `401 invalid_client` in the log | The secret is wrong, or the application sends it in a way other than the registered one | Check `OIDC_CLIENT_SECRET`, and register `client_secret_basic` |
| The email and the name are empty | The application asks for `openid` alone | Ask for `profile` and `email` too |
| A `500` error, and `Callback: invalid state.` in the log | The callback was reached without the session that started the sign-in | Start every sign-in from `/auth/redirect` |
| Sign-out is refused, the `post_logout_redirect_uri` is not registered | The address differs from the registered ones | Register it in `post_logout_redirect_uris` |

## How it works

You do not need this section to follow the guide. It lists what the driver and Beffroi do without being told.

| The driver | Beffroi |
|---|---|
| Protects the sign-in with PKCE (`S256`), a `state` and a `nonce` | Requires PKCE, accepts `S256` only, and checks the verifier |
| Sends the secret in the `Authorization` header, `client_secret_basic`, since Beffroi offers it | Accepts the method the application registered, and only that one |
| Checks the signature of the ID token, its issuer, audience, expiry and `nonce` | Signs the ID token with `RS256` by default |
| Reads the email and the name from the UserInfo endpoint | Puts the email and the profile in UserInfo, not in the ID token |
| Exposes `sub` as `getId()`, `email` as `getEmail()`, `name` as `getName()` | Answers with what the person agreed to share. `preferred_username` is in `getRaw()` |

!!! warning "Several providers in one application"

    Beffroi adds its address to every answer it sends to the callback, in an `iss` parameter (RFC 9207 §2). The
    driver does not check it. With Beffroi as the only provider of your application, this changes nothing.
    With several, compare `iss` with the address of the provider the visitor was sent to, before calling
    `user()`.

[:beffroi-arrow-right: Where a claim goes](../oidc/scopes-and-claims.md#where-a-claim-goes)

## Without the community driver

A provider you write yourself on Socialite's `AbstractProvider` also signs people in. It behaves differently in
four ways:

- it sends no PKCE unless you call `enablePKCE()`, and Beffroi refuses a request without it;
- it sends the secret in the body of the request, so register the client with
  `token_endpoint_auth_method: client_secret_post`;
- it neither reads nor checks the ID token;
- it sends no `nonce`.

## What was not tested

- The other community driver, `kovah/laravel-socialite-oidc`, and Passport, Fortify, Breeze or Filament.
- Beffroi behind a proxy that terminates TLS (`TLS_TERMINATION=proxy`), and Laravel behind a proxy or on
  several servers.
- A rotation of the signing keys of Beffroi.
- ID tokens signed with an algorithm other than `RS256`, encrypted ID tokens, signed or encrypted UserInfo.
- A rejected issuer, audience, `nonce` or `at_hash` in the ID token: only a wrong signature was tried.
- The actual expiry of the access token and of the refresh token.
- Back-channel and front-channel logout, and the `prompt`, `max_age`, `acr_values` and `login_hint` parameters.
- Public clients, `private_key_jwt`, pushed authorization requests, DPoP, request objects and pairwise
  identifiers.
- The `open` and `software_statement` registration modes, and updating the client through its configuration
  endpoint (RFC 7592).
- Signing in from a real browser: the pages of Beffroi were driven by a script.
- A Laravel application served over HTTPS: the callback was `http://localhost:8000/auth/callback`.
- A Laravel application with its configuration cached for production. Only `APP_DEBUG=false` was tried.
