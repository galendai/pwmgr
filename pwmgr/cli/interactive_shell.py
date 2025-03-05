"""
Interactive shell for the password manager.
Allows using multiple commands with a single master password input.
"""
import os
import cmd
import shlex
from typing import Optional, List, Dict, Any

import click
from click.testing import CliRunner

from ..core import PasswordStorage, PasswordGenerator
from .commands import cli, get_master_password


class PasswordManagerShell(cmd.Cmd):
    """Interactive shell for the password manager."""

    intro = """
    ██████╗  █████╗ ███████╗███████╗███╗   ███╗ ██████╗ ██████╗
    ██╔══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║██╔════╝ ██╔══██╗
    ██████╔╝███████║███████╗███████╗██╔████╔██║██║  ███╗██████╔╝
    ██╔═══╝ ██╔══██║╚════██║╚════██║██║╚██╔╝██║██║   ██║██╔══██╗
    ██║     ██║  ██║███████║███████║██║ ╚═╝ ██║╚██████╔╝██║  ██║
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝

    Interactive Password Manager Shell
    Type 'help' for available commands.
    Type 'exit' to exit.
    """
    prompt = "pwmgr> "

    def __init__(self):
        super().__init__()
        self.storage = PasswordStorage()
        self.master_password = None
        self.runner = CliRunner()
        self.entries = None

    def preloop(self):
        """Ask for master password before starting the loop."""
        if not self.storage.file_exists():
            print("Password storage not initialized. Please run 'init' first.")
            return

        self.master_password = get_master_password()
        self.entries = self.storage.load(self.master_password)

        if self.entries is None:
            print("Invalid master password.")
            self.master_password = None
            return

        print(f"Successfully loaded {len(self.entries)} password entries.")

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_exit(self, arg):
        """Exit the interactive shell."""
        print("Goodbye!")
        return True

    do_quit = do_exit

    def do_list(self, arg):
        """List all password entries or filter by name."""
        if not self._check_authenticated():
            return

        args = shlex.split(arg) if arg else []
        name_filter = None

        if args:
            # Parse arguments
            for i, a in enumerate(args):
                if a in ['-n', '--name'] and i + 1 < len(args):
                    name_filter = args[i + 1]
                    break

        if name_filter:
            filtered_entries = [entry for entry in self.entries
                               if name_filter.lower() in entry.name.lower()]
        else:
            filtered_entries = self.entries

        # Display entries
        if not filtered_entries:
            print("No password entries found.")
            return

        # Sort entries by name
        sorted_entries = sorted(filtered_entries, key=lambda e: e.name.lower())

        # Calculate column widths for better formatting
        id_width = 8  # Fixed width for ID (shortened UUID)
        name_width = max(len("NAME"), max(len(entry.name) for entry in sorted_entries))
        username_width = max(len("USERNAME"), max(len(entry.username) for entry in sorted_entries))

        # Print header
        print("\nPassword Entries:")
        print("-" * (id_width + name_width + username_width + 10))  # +10 for spacing and borders
        header_format = f"| {{:<{id_width}}} | {{:<{name_width}}} | {{:<{username_width}}} |"
        print(header_format.format("ID", "NAME", "USERNAME"))
        print("-" * (id_width + name_width + username_width + 10))

        # Print entries
        row_format = f"| {{:<{id_width}}} | {{:<{name_width}}} | {{:<{username_width}}} |"
        for entry in sorted_entries:
            short_id = entry.id[:6]  # Show only first 6 chars of UUID
            print(row_format.format(short_id, entry.name, entry.username))

        print("-" * (id_width + name_width + username_width + 10))
        print(f"Total: {len(sorted_entries)} entries")

    def do_show(self, arg):
        """Show details of a specific password entry."""
        if not self._check_authenticated():
            return

        args = shlex.split(arg) if arg else []
        name = None
        show_password = False

        # Parse arguments
        for i, a in enumerate(args):
            if a in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]
            elif a in ['-p', '--show-password']:
                show_password = True

        if not name:
            print("Please provide a name with --name.")
            return

        # Find entry
        entry = next((e for e in self.entries if e.name.lower() == name.lower()), None)
        if not entry:
            print(f"No entry found with name '{name}'.")
            return

        # Display entry
        print("\nPassword Entry Details:")
        print("-" * 50)
        print(f"Name: {entry.name}")
        print(f"Username: {entry.username}")

        if show_password:
            print(f"Password: {entry.password}")
        else:
            hidden_pw = "*" * min(len(entry.password), 10)
            print(f"Password: {hidden_pw} (use --show-password to reveal)")

        if entry.notes:
            print(f"Notes: {entry.notes}")

        print(f"Created: {entry.created_at}")
        print(f"Updated: {entry.updated_at}")
        print("-" * 50)

    def do_add(self, arg):
        """Add a new password entry."""
        if not self._check_authenticated():
            return

        args = shlex.split(arg) if arg else []
        params = {}

        # Parse arguments
        i = 0
        while i < len(args):
            if args[i] in ['-n', '--name'] and i + 1 < len(args):
                params['name'] = args[i + 1]
                i += 2
            elif args[i] in ['-u', '--username'] and i + 1 < len(args):
                params['username'] = args[i + 1]
                i += 2
            elif args[i] in ['-p', '--password'] and i + 1 < len(args):
                params['password'] = args[i + 1]
                i += 2
            elif args[i] == '--notes' and i + 1 < len(args):
                params['notes'] = args[i + 1]
                i += 2
            elif args[i] in ['-g', '--auto-generate-password']:
                params['auto_generate_password'] = True
                i += 1
            elif args[i] == '--password-length' and i + 1 < len(args):
                try:
                    params['password_length'] = int(args[i + 1])
                except ValueError:
                    print(f"Invalid password length: {args[i + 1]}")
                    return
                i += 2
            elif args[i] in ['--include-symbols']:
                params['include_symbols'] = True
                i += 1
            else:
                print(f"Unknown argument: {args[i]}")
                return

        # Check for required params
        if 'name' not in params:
            print("Name is required. Use --name.")
            return

        if 'username' not in params:
            print("Username is required. Use --username.")
            return

        from ..core.models import PasswordEntry

        # Check if entry with this name already exists
        if any(entry.name == params['name'] for entry in self.entries):
            choice = input(f"Entry with name '{params['name']}' already exists. Overwrite? (y/n): ")
            if choice.lower() != 'y':
                return
            # Remove existing entry
            self.entries = [entry for entry in self.entries if entry.name != params['name']]

        # Generate or prompt for password
        if params.get('auto_generate_password'):
            length = params.get('password_length', 16)
            include_symbols = params.get('include_symbols', True)
            password = PasswordGenerator.generate(
                length=length,
                include_symbols=include_symbols
            )
            print(f"Generated password: {password}")
        elif 'password' not in params:
            import getpass
            password = getpass.getpass("Enter password: ")
        else:
            password = params['password']

        # Create and add new entry
        new_entry = PasswordEntry(
            name=params['name'],
            username=params['username'],
            password=password,
            notes=params.get('notes')
        )

        self.entries.append(new_entry)

        # Save entries
        self.storage.save(self.entries, self.master_password)

        print(f"Password entry '{params['name']}' added successfully.")

    def do_delete(self, arg):
        """Delete a password entry."""
        if not self._check_authenticated():
            return

        args = shlex.split(arg) if arg else []
        name = None

        # Parse arguments
        for i, a in enumerate(args):
            if a in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]
                break

        if not name:
            print("Please provide a name with --name.")
            return

        # Check if entry exists
        if not any(entry.name.lower() == name.lower() for entry in self.entries):
            print(f"No entry found with name '{name}'.")
            return

        # Confirm deletion
        confirm = input(f"Are you sure you want to delete entry '{name}'? (y/n): ")
        if confirm.lower() != 'y':
            return

        # Remove entry
        self.entries = [entry for entry in self.entries if entry.name.lower() != name.lower()]

        # Save updated entries
        self.storage.save(self.entries, self.master_password)

        print(f"Password entry '{name}' deleted successfully.")

    def do_generate(self, arg):
        """Generate random password(s)."""
        args = shlex.split(arg) if arg else []
        params = {
            'length': 16,
            'include_lowercase': True,
            'include_uppercase': True,
            'include_digits': True,
            'include_symbols': True,
            'count': 1
        }

        # Parse arguments
        i = 0
        while i < len(args):
            if args[i] in ['-l', '--length'] and i + 1 < len(args):
                try:
                    params['length'] = int(args[i + 1])
                except ValueError:
                    print(f"Invalid length: {args[i + 1]}")
                    return
                i += 2
            elif args[i] == '--no-lowercase':
                params['include_lowercase'] = False
                i += 1
            elif args[i] == '--no-uppercase':
                params['include_uppercase'] = False
                i += 1
            elif args[i] == '--no-digits':
                params['include_digits'] = False
                i += 1
            elif args[i] == '--no-symbols':
                params['include_symbols'] = False
                i += 1
            elif args[i] in ['-c', '--count'] and i + 1 < len(args):
                try:
                    params['count'] = int(args[i + 1])
                except ValueError:
                    print(f"Invalid count: {args[i + 1]}")
                    return
                i += 2
            else:
                print(f"Unknown argument: {args[i]}")
                return

        for i in range(params['count']):
            password = PasswordGenerator.generate(
                length=params['length'],
                include_lowercase=params['include_lowercase'],
                include_uppercase=params['include_uppercase'],
                include_digits=params['include_digits'],
                include_symbols=params['include_symbols']
            )
            if params['count'] > 1:
                print(f"{i+1}. {password}")
            else:
                print(password)

    def do_help(self, arg):
        """List available commands with help text."""
        if arg:
            # Get help on specific command
            super().do_help(arg)
        else:
            print("\nAvailable commands:")
            print("-" * 50)
            commands = {
                'list': 'List all password entries (options: --name)',
                'show': 'Show password details (options: --name, --show-password)',
                'add': 'Add a new password (options: --name, --username, --password, --notes, --auto-generate-password)',
                'delete': 'Delete a password (options: --name)',
                'generate': 'Generate random password (options: --length, --count, --no-lowercase, --no-uppercase, etc)',
                'exit': 'Exit the interactive shell',
                'help': 'Show this help message',
            }

            for cmd, desc in commands.items():
                print(f"{cmd:10} - {desc}")
            print("-" * 50)
            print("For more details, type 'help <command>'")

    def _check_authenticated(self):
        """Check if the user is authenticated."""
        if self.master_password is None or self.entries is None:
            print("Not authenticated. Please restart the shell.")
            return False
        return True


def run_interactive_shell():
    """Run the interactive shell."""
    shell = PasswordManagerShell()
    shell.cmdloop()