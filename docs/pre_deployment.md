## Stax API Token

Access to Stax Api's via Stax SDK requires an API token (access key and secret) populated in your account for use with Stax Orchestrator application.

Follow Stax's [guide](https://support.stax.io/hc/en-us/articles/4447111085583-Create-an-API-Token) to create the API token. After you create the token, populate the following SSM parameters into your AWS Account,

* `/orchestrator/stax/access/key` - Stax Access Key
* `/orchestrator/stax/access/key/secret` - Stax Access Key Secret
