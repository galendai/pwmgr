# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PassMgr is a secure local password manager CLI tool built with Python. It uses AES-256 encryption to store passwords locally and provides both standard CLI and interactive shell modes.

## Development Commands

### Running the Application
```bash
# Run the password manager
python -m pwmgr

# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

### Common CLI Commands for Testing
```bash
# Initialize password manager (first time setup)
python -m pwmgr init

# Add a password entry
python -m pwmgr add --name "GitHub" --username "user@example.com"

# List all password entries
python -m pwmgr list

# Show specific password details
python -m pwmgr show --name "GitHub" --show-password

# Generate a random password
python -m pwmgr generate --length 20 --include-symbols

# Start interactive shell mode
python -m pwmgr shell
```

### Testing
- No formal test suite currently exists in the project
- Manual testing can be done using the CLI commands above
- When adding tests, clean up test files and generated data after completion

## Architecture Overview

### Core Modules Structure

**pwmgr/core/** - Core business logic
- `models.py`: Contains `PasswordEntry` dataclass with UUID, timestamps, and serialization methods
- `storage.py`: `PasswordStorage` class handles encrypted file I/O using `~/.pwmgr/passwords.json.enc`
- `generator.py`: `PasswordGenerator` class creates secure random passwords with configurable character sets

**pwmgr/crypto/** - Security layer
- `encryption.py`: `EncryptionService` implements AES-256-CBC encryption with PBKDF2 key derivation (100,000 iterations)

**pwmgr/cli/** - User interface layer
- `commands.py`: Click-based CLI commands (init, add, list, show, delete, generate, shell)
- `interactive_shell.py`: Interactive shell using `cmd.Cmd` for multi-command sessions with single authentication

### Key Design Patterns

1. **Security-First Design**: Master password is never stored, only used for key derivation via PBKDF2
2. **Local Storage Only**: No external dependencies or network connections
3. **Modular Architecture**: Clear separation between crypto, core logic, and CLI layers
4. **Data Models**: `PasswordEntry` uses dataclasses with automatic UUID generation and ISO timestamp management

### Important Implementation Details

- **File Storage**: Encrypted data stored in base64-encoded format containing salt + IV + ciphertext
- **Authentication**: Every CLI command (except init/generate) requires master password entry
- **Interactive Mode**: Shell mode maintains decrypted entries in memory for multiple operations
- **Error Handling**: Failed decryption returns `None` rather than raising exceptions

### Entry Points

- Main entry: `pwmgr/__main__.py` → `pwmgr/cli/__init__.py:cli()`
- Console script: `pwmgr=pwmgr.cli:cli` (defined in setup.py)
- Interactive shell: `pwmgr/cli/interactive_shell.py:PasswordManagerShell`

## Security Considerations

- All sensitive data is encrypted using AES-256-CBC with PBKDF2 key derivation
- Master passwords are validated through decryption success/failure
- No sensitive data is logged or stored in plaintext
- Memory cleanup should be considered when handling sensitive data in future enhancements