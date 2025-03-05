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

    intro = click.style("""
    ██████╗  █████╗ ███████╗███████╗███╗   ███╗ ██████╗ ██████╗
    ██╔══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║██╔════╝ ██╔══██╗
    ██████╔╝███████║███████╗███████╗██╔████╔██║██║  ███╗██████╔╝
    ██╔═══╝ ██╔══██║╚════██║╚════██║██║╚██╔╝██║██║   ██║██╔══██╗
    ██║     ██║  ██║███████║███████║██║ ╚═╝ ██║╚██████╔╝██║  ██║
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝

    Interactive Password Manager Shell
    """, fg="bright_blue") + click.style("""
    Type 'help' for available commands.
    Type 'exit' to exit.
    """, fg="cyan")

    prompt = click.style("pwmgr> ", fg="green", bold=True)

    def __init__(self):
        super().__init__()
        self.storage = PasswordStorage()
        self.master_password = None
        self.runner = CliRunner()
        self.entries = None

    def preloop(self):
        """Ask for master password before starting the loop."""
        if not self.storage.file_exists():
            click.secho("Password storage not initialized. Please run 'init' first.", fg="yellow")
            return

        self.master_password = get_master_password()
        self.entries = self.storage.load(self.master_password)

        if self.entries is None:
            click.secho("Invalid master password.", fg="red", bold=True)
            self.master_password = None
            return

        click.secho(f"Successfully loaded {len(self.entries)} password entries.", fg="green")

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_exit(self, arg):
        """Exit the interactive shell."""
        click.secho("Goodbye!", fg="bright_blue")
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
            click.secho("No password entries found.", fg="yellow")
            return

        # Sort entries by name
        sorted_entries = sorted(filtered_entries, key=lambda e: e.name.lower())

        # Calculate column widths for better formatting
        id_width = 8  # Fixed width for ID (shortened UUID)
        name_width = max(len("NAME"), max(len(entry.name) for entry in sorted_entries))
        username_width = max(len("USERNAME"), max(len(entry.username) for entry in sorted_entries))

        # Print header
        click.secho("\nPassword Entries:", fg="bright_blue", bold=True)
        click.secho("-" * (id_width + name_width + username_width + 10), fg="blue")
        header_format = f"| {{:<{id_width}}} | {{:<{name_width}}} | {{:<{username_width}}} |"
        click.secho(header_format.format("ID", "NAME", "USERNAME"), fg="cyan")
        click.secho("-" * (id_width + name_width + username_width + 10), fg="blue")

        # Print entries
        row_format = f"| {{:<{id_width}}} | {{:<{name_width}}} | {{:<{username_width}}} |"
        for i, entry in enumerate(sorted_entries):
            short_id = entry.id[:6]  # Show only first 6 chars of UUID
            # Alternate row colors for better readability
            color = "bright_white" if i % 2 == 0 else "white"
            click.secho(row_format.format(short_id, entry.name, entry.username), fg=color)

        click.secho("-" * (id_width + name_width + username_width + 10), fg="blue")
        click.secho(f"Total: {len(sorted_entries)} entries", fg="green")

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
            click.secho("Please provide a name with --name.", fg="yellow")
            return

        # Find entry
        entry = next((e for e in self.entries if e.name.lower() == name.lower()), None)
        if not entry:
            click.secho(f"No entry found with name '{name}'.", fg="yellow")
            return

        # Display entry
        click.secho("\nPassword Entry Details:", fg="bright_blue", bold=True)
        click.secho("-" * 50, fg="blue")
        click.secho(f"Name: ", fg="cyan", nl=False)
        click.secho(entry.name, fg="white")
        click.secho(f"Username: ", fg="cyan", nl=False)
        click.secho(entry.username, fg="white")

        if show_password:
            click.secho(f"Password: ", fg="cyan", nl=False)
            click.secho(entry.password, fg="bright_green")
        else:
            hidden_pw = "*" * min(len(entry.password), 10)
            click.secho(f"Password: ", fg="cyan", nl=False)
            click.secho(f"{hidden_pw} ", fg="yellow", nl=False)
            click.secho("(use --show-password to reveal)", fg="bright_black")

        if entry.notes:
            click.secho(f"Notes: ", fg="cyan", nl=False)
            click.secho(entry.notes, fg="white")

        click.secho(f"Created: ", fg="cyan", nl=False)
        click.secho(entry.created_at, fg="bright_black")
        click.secho(f"Updated: ", fg="cyan", nl=False)
        click.secho(entry.updated_at, fg="bright_black")
        click.secho("-" * 50, fg="blue")

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
                    click.secho(f"Invalid password length: {args[i + 1]}", fg="red")
                    return
                i += 2
            elif args[i] in ['--include-symbols']:
                params['include_symbols'] = True
                i += 1
            else:
                click.secho(f"Unknown argument: {args[i]}", fg="red")
                return

        # Check for required params
        if 'name' not in params:
            click.secho("Name is required. Use --name.", fg="yellow")
            return

        if 'username' not in params:
            click.secho("Username is required. Use --username.", fg="yellow")
            return

        from ..core.models import PasswordEntry

        # Check if entry with this name already exists
        if any(entry.name == params['name'] for entry in self.entries):
            click.secho(f"Entry with name '{params['name']}' already exists.", fg="yellow")
            choice = input(click.style("Overwrite? (y/n): ", fg="yellow"))
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
            click.secho("Generated password: ", fg="blue", nl=False)
            click.secho(password, fg="bright_blue")
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

        click.secho(f"Password entry '{params['name']}' added successfully.", fg="green")

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
            click.secho("Please provide a name with --name.", fg="yellow")
            return

        # Check if entry exists
        if not any(entry.name.lower() == name.lower() for entry in self.entries):
            click.secho(f"No entry found with name '{name}'.", fg="yellow")
            return

        # Confirm deletion
        click.secho(f"Are you sure you want to delete entry '{name}'? (y/n): ", fg="yellow", nl=False)
        confirm = input()
        if confirm.lower() != 'y':
            return

        # Remove entry
        self.entries = [entry for entry in self.entries if entry.name.lower() != name.lower()]

        # Save updated entries
        self.storage.save(self.entries, self.master_password)

        click.secho(f"Password entry '{name}' deleted successfully.", fg="green")

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
                    click.secho(f"Invalid length: {args[i + 1]}", fg="red")
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
                    click.secho(f"Invalid count: {args[i + 1]}", fg="red")
                    return
                i += 2
            else:
                click.secho(f"Unknown argument: {args[i]}", fg="red")
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
                click.secho(f"{i+1}. ", fg="blue", nl=False)
                click.secho(password, fg="bright_green")
            else:
                click.secho(password, fg="bright_green")

    def do_help(self, arg):
        """List available commands with help text."""
        if arg:
            # Get help on specific command
            super().do_help(arg)
        else:
            click.secho("\nAvailable commands:", fg="bright_blue", bold=True)
            click.secho("-" * 50, fg="blue")
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
                click.secho(f"{cmd:10}", fg="cyan", nl=False)
                click.secho(f" - {desc}", fg="white")
            click.secho("-" * 50, fg="blue")
            click.secho("For more details, type 'help <command>'", fg="bright_black")

    def _check_authenticated(self):
        """Check if the user is authenticated."""
        if self.master_password is None or self.entries is None:
            click.secho("Not authenticated. Please restart the shell.", fg="red")
            return False
        return True


def run_interactive_shell():
    """Run the interactive shell."""
    shell = PasswordManagerShell()
    shell.cmdloop()