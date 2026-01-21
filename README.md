# Balance Project
Using AirPods to detect balance changes.

## Building the App Locally

### Requirements:
* macOs with Xcode installed
* iPhone running iOS 18.6 or later (connected to Mac via cable)
* AirPods Pro 2 or 3 (connected to iPhone via Bluetooth)
* Apple Developer account

### Build Steps: 
1. Clone the repository from GitHub.
2. Open the project in Xcode.
3. Select your connected iPhone as run destination (top middle of window): \
`Balance Project > Your iPhone`
4. Select project in navigator (left sidebar), then find **Targets → Signing & Capabilities**
5. Check automatically manage signing, and click **Team → Add an Account** and add your Apple account as a team. \
If necessary, change your bundle identifier to be unique.
6. Run app (`Cmd + R`) to build the app on your iPhone
7. On your iPhone, navigate to **Settings → General → VPN & Device Management** and trust the developer account.

