# munros

Aggregating the bagging.

## Mechanism

### Authentication

#### Overview

I followed [these instructions](https://developers.strava.com/docs/getting-started/) to register an API application for
Strava. [These docs](https://developers.strava.com/docs/authentication/) helped me to understand the OAuth 2.0 flow with
Strava.

Signed in, I grabbed my client ID and secret from [this page](https://www.strava.com/settings/api). Annoyingly, like a
lot of other implementations of OAuth 2.0 flows, Strava requires a bit of a workaround to generate access and refresh
tokens for the first time if you are building an API-driven application. After I have stored an initial refresh token, I
am able to programmatically get a new, refreshed access token before each batch of Strava API requests.

Note that the default access and refresh tokens provided by Strava (which can be grabbed from the "My API Application"
page) only have `read` scope which is not sufficient for getting detailed information about an activity.

#### Getting initial refresh token

I pasted the following into my browser (note the `read_all` scope):

```shell
https://www.strava.com/oauth/authorize?client_id=17865&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all
```

Clicked "Authorize" when prompted.

Was taken to something like:

```shell
https://localhost/exchange_token?state=&code=152aae17e171b3d122e240198f4b965ccf5f6463&scope=read,activity:read_all
```

Extracted the authorization code (`152aae17e171b3d122e240198f4b965ccf5f6463`, in this case).

Exchanged the code for an access (and refresh) token using my client secret:

```shell
curl -X POST https://www.strava.com/oauth/token -F client_id=17865 -F client_secret=${my client secret} -F code=152aae17e171b3d122e240198f4b965ccf5f6463 -F grant_type=authorization_code
```

From the response, I grabbed the `refresh_token`.

I used the AWS CLI to upload the initial refresh token to AWS Secrets Manager. For example:

```shell
aws secretsmanager update-secret --secret-id strava-refresh-token --secret-string d4e8ee7a4103a7eedbbc9346f86aca0ab1c67aeb
```

Subsequent refresh tokens will be programmatically fetched (from Strava's API) and stored (in AWS Secrets Manager) by
the Lambda function. Note that previous refresh tokens are immediately invalidated upon the successful issue of a new
one.

#### Business as usual

Strava access tokens expire after six hours. I intend for the Lambda function to execute at most once per day, so I have
designed the function to always fetch new tokens before trying to make a request to the Strava API.

The [relevant Strava documentation](https://developers.strava.com/docs/authentication/#refreshingexpiredaccesstokens)
says:

> To refresh an access token, applications should call the POST https://www.strava.com/oauth/token endpoint, specifying grant_type: refresh_token and including the application’s refresh token for the user as an additional parameter. If the application has an access token for the user that expires in more than one hour, the existing access token will be returned. If the application’s access tokens for the user are expired or will expire in one hour (3,600 seconds) or less, a new access token will be returned. In this case, both the newer and older access tokens can be used until they expire.
>
> A refresh token is issued back to the application after all successful requests to the POST https://www.strava.com/oauth/token endpoint. The refresh token may or may not be the same refresh token used to make the request. Applications should persist the refresh token contained in the response, and always use the most recent refresh token for subsequent requests to obtain a new access token. Once a new refresh token is returned, the older refresh token is invalidated immediately.

### Strava

- Loop through pages of activities (from the `/athlete` API) until they are exhausted
- Make a list of activity IDs that have `#munros` in the name
- Use the `/activities` API to get detailed information about each activity

### S3

- Check for the existence of a `munros.json` in the bucket
- If it exists, copy it and suffix it with a timestamp
- Over/write `munros.json` with the latest Munro-related activities from Strava
