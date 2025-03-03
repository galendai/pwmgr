# PassMgr - Secure Local Password Manager

PassMgr is a simple yet secure command-line password management tool focused on core functionality and secure encryption, running entirely locally without relying on any external services.

## Features

- **Secure Password Storage**: All passwords are stored locally using AES-256 encryption
- **Password Entry Management**: Easily add, view, update, and delete password entries
- **Password Generation**: Generate high-strength random passwords
- **Simple to Use**: Intuitive command-line interface with no complex setup

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pwmgr.git
cd pwmgr

# Install dependencies
pip install -r requirements.txt
```

## Usage

Initialize (first run):
```bash
python -m pwmgr init
```

Add a new password:
```bash
python -m pwmgr add --name "GitHub" --username "user@example.com"
```

List passwords:
```bash
python -m pwmgr list
```

View specific password details:
```bash
python -m pwmgr show --name "GitHub"
```

Generate a random password:
```bash
python -m pwmgr generate --length 20 --include-symbols
```

## Security Notes

- All passwords are stored using AES-256 encryption
- Master password is never saved, only used to derive encryption keys
- All sensitive data is only decrypted in memory and cleared immediately after use
