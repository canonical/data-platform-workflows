Workflow file: [mattermost_alert.yaml](mattermost_alert.yaml)

## Example Output
![](screenshots/mattermost_alert.png)

## Usage
### Basic Example
```yaml
notify-failure:
  name: Notify Failure to Mattermost
  runs-on: ubuntu-latest
  needs:
    - integration-test  # whatever jobs you'd like to ensure runs first
  steps:
    - name: Notify Failure To Mattermost
      uses: canonical/data-platform-workflows/.github/workflows/mattermost_alert.yaml
      with:
        channel-id: data-platform-alerts  # required
        mention-users: @bob,@alice
      secrets:
        mattermost-token: ${{ secrets.MATTERMOST_TOKEN }}  # required
```

### Inputs + Secrets
```yaml
inputs:
  server:
    description: The Mattermost address to post to
    required: false
    default: "chat.canonical.com"
  channel-id:
    description: The Mattermost channel ID to post to
    required: true
  mention-users:
    description: The Mattermost usernames you want to mention
    required: false
    default: ""
secrets:
  mattermost-token:
    description: The Mattermost bot token to post using
    required: true
```
