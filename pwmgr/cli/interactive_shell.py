"""
Interactive shell for the password manager.
Allows using multiple commands with a single master password input.
"""
import os
import sys
import cmd
import shlex
import fnmatch
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher

import click
from click.testing import CliRunner

from ..core import PasswordStorage, PasswordGenerator
from .commands import cli, get_master_password

# Try to import readline for command history and completion
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


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

    # Available commands for autocompletion
    COMMANDS = ['list', 'show', 'add', 'delete', 'generate', 'search', 'backup', 'restore', 'security', 'help', 'exit', 'quit']

    def __init__(self):
        super().__init__()
        self.storage = PasswordStorage()
        self.master_password = None
        self.runner = CliRunner()
        self.entries = None
        self._setup_readline()

    def _setup_readline(self):
        """Set up readline for command history and completion."""
        if not HAS_READLINE:
            return

        # History file
        history_file = os.path.expanduser("~/.pwmgr/.shell_history")
        history_dir = os.path.dirname(history_file)

        # Ensure directory exists
        if not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)

        # Load history if exists
        if os.path.exists(history_file):
            try:
                readline.read_history_file(history_file)
            except Exception:
                pass

        # Set history size
        readline.set_history_length(1000)

        # Save history on exit
        self._history_file = history_file

        # Enable tab completion
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")

    def _completer(self, text: str, state: int) -> Optional[str]:
        """
        Custom completer for tab completion.

        Args:
            text: Current text being completed
            state: State index for iteration

        Returns:
            Next completion or None
        """
        # Get the current line buffer
        line_buffer = readline.get_line_buffer() if HAS_READLINE else ""

        # Parse command and arguments
        parts = line_buffer.lstrip().split()

        if not parts or len(parts) == 1:
            # Complete command names
            matches = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
        elif parts[0] in ['show', 'delete']:
            # Complete entry names for show/delete commands
            if self.entries:
                entry_names = [e.name for e in self.entries]
                matches = [name for name in entry_names if name.lower().startswith(text.lower())]
            else:
                matches = []
        elif parts[0] == 'list':
            # Complete options for list
            options = ['--name', '-n', '--json']
            matches = [opt for opt in options if opt.startswith(text)]
        else:
            matches = []

        if state < len(matches):
            return matches[state]
        return None

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

    def postloop(self):
        """Save command history on exit."""
        if HAS_READLINE and hasattr(self, '_history_file'):
            try:
                readline.write_history_file(self._history_file)
            except Exception:
                pass

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_exit(self, arg):
        """Exit the interactive shell."""
        click.secho("Goodbye!", fg="bright_blue")
        return True

    do_quit = do_exit

    def do_search(self, arg):
        """
        Search for password entries with fuzzy matching.

        Usage: search <query> [--threshold 0.5]

        Options:
            --threshold  Minimum similarity threshold (0.0-1.0, default: 0.5)
        """
        if not self._check_authenticated():
            return

        args = shlex.split(arg) if arg else []
        if not args:
            click.secho("Please provide a search query.", fg="yellow")
            return

        query = ""
        threshold = 0.5

        i = 0
        while i < len(args):
            if args[i] == '--threshold' and i + 1 < len(args):
                try:
                    threshold = float(args[i + 1])
                    threshold = max(0.0, min(1.0, threshold))
                except ValueError:
                    click.secho("Invalid threshold value.", fg="red")
                    return
                i += 2
            else:
                query += " " + args[i] if query else args[i]
                i += 1

        if not query:
            click.secho("Please provide a search query.", fg="yellow")
            return

        # Perform fuzzy search
        results = []
        for entry in self.entries:
            # Search in name, username, and notes
            name_score = SequenceMatcher(None, query.lower(), entry.name.lower()).ratio()
            username_score = SequenceMatcher(None, query.lower(), entry.username.lower()).ratio()
            notes_score = 0
            if entry.notes:
                notes_score = SequenceMatcher(None, query.lower(), entry.notes.lower()).ratio()

            max_score = max(name_score, username_score, notes_score)
            if max_score >= threshold:
                results.append((entry, max_score))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)

        if not results:
            click.secho(f"No entries found matching '{query}'.", fg="yellow")
            return

        click.secho(f"\nSearch Results for '{query}':", fg="bright_blue", bold=True)
        click.secho("-" * 70, fg="blue")

        for entry, score in results:
            score_pct = int(score * 100)
            score_color = "green" if score_pct >= 80 else "yellow" if score_pct >= 60 else "red"
            click.secho(f"  {entry.name}", fg="white", nl=False)
            click.secho(f" ({entry.username})", fg="bright_black", nl=False)
            click.secho(f" [{score_pct}%]", fg=score_color)

        click.secho("-" * 70, fg="blue")
        click.secho(f"Found {len(results)} matching entries.", fg="green")

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
        check_strength = False

        # Parse arguments
        for i, a in enumerate(args):
            if a in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]
            elif a in ['-p', '--show-password']:
                show_password = True
            elif a == '--check-strength':
                check_strength = True

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

            # Show password strength if requested
            if check_strength:
                strength, label, suggestions = PasswordGenerator.check_password_strength(entry.password)
                color = "green" if strength >= 4 else "yellow" if strength >= 3 else "red"
                click.secho(f"Password strength: {label}", fg=color)
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
            try:
                password = PasswordGenerator.generate(
                    length=length,
                    include_symbols=include_symbols
                )
            except ValueError as e:
                click.secho(str(e), fg="red")
                return
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
            'count': 1,
            'check_strength': False
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
            elif args[i] == '--check-strength':
                params['check_strength'] = True
                i += 1
            else:
                click.secho(f"Unknown argument: {args[i]}", fg="red")
                return

        for i in range(params['count']):
            try:
                password = PasswordGenerator.generate(
                    length=params['length'],
                    include_lowercase=params['include_lowercase'],
                    include_uppercase=params['include_uppercase'],
                    include_digits=params['include_digits'],
                    include_symbols=params['include_symbols']
                )
            except ValueError as e:
                click.secho(str(e), fg="red")
                return

            if params['count'] > 1:
                click.secho(f"{i+1}. ", fg="blue", nl=False)
                click.secho(password, fg="bright_green")
            else:
                click.secho(password, fg="bright_green")

            if params['check_strength']:
                strength, label, suggestions = PasswordGenerator.check_password_strength(password)
                color = "green" if strength >= 4 else "yellow" if strength >= 3 else "red"
                click.secho(f"   Strength: {label}", fg=color)

    def do_backup(self, arg):
        """Create a backup of all entries."""
        if not self._check_authenticated():
            return

        from ..core.backup import BackupManager
        import getpass

        args = shlex.split(arg) if arg else []
        name = None

        for i, a in enumerate(args):
            if a in ['-n', '--name'] and i + 1 < len(args):
                name = args[i + 1]

        backup_manager = BackupManager()
        try:
            backup_path = backup_manager.create_backup(self.entries, self.master_password, name=name)
            click.secho(f"Backup created: {backup_path}", fg="green")
        except Exception as e:
            click.secho(f"Backup failed: {str(e)}", fg="red")

    def do_restore(self, arg):
        """Restore entries from a backup file."""
        if not self._check_authenticated():
            return

        from ..core.backup import BackupManager

        args = shlex.split(arg) if arg else []
        backup_file = None
        merge = False

        i = 0
        while i < len(args):
            if args[i] in ['-f', '--file'] and i + 1 < len(args):
                backup_file = args[i + 1]
                i += 2
            elif args[i] == '--merge':
                merge = True
                i += 1
            else:
                i += 1

        if not backup_file:
            click.secho("Please provide a backup file with --file.", fg="yellow")
            return

        backup_manager = BackupManager()
        try:
            restored_entries = backup_manager.restore_backup(backup_file, self.master_password)

            if merge:
                existing_names = {e.name.lower() for e in self.entries}
                merged = [e for e in self.entries if e.name.lower() not in {r.name.lower() for r in restored_entries}]
                merged.extend(restored_entries)
                self.entries = merged
            else:
                self.entries = restored_entries

            self.storage.save(self.entries, self.master_password)
            click.secho(f"Restored {len(restored_entries)} entries.", fg="green")
        except Exception as e:
            click.secho(f"Restore failed: {str(e)}", fg="red")

    def do_security(self, arg):
        """Check security status."""
        warnings = self.storage.get_security_warnings()

        click.secho("\nSecurity Status:", fg="bright_blue", bold=True)
        click.secho("-" * 50, fg="blue")

        if warnings:
            click.secho("Warnings:", fg="yellow")
            for warning in warnings:
                click.secho(f"  - {warning}", fg="yellow")
        else:
            click.secho("No security warnings.", fg="green")

        click.secho("-" * 50, fg="blue")

    def do_help(self, arg):
        """List available commands with help text."""
        if arg:
            # Get help on specific command
            super().do_help(arg)
        else:
            click.secho("\nAvailable commands:", fg="bright_blue", bold=True)
            click.secho("-" * 60, fg="blue")
            commands = {
                'list': 'List all password entries (options: --name)',
                'show': 'Show password details (options: --name, --show-password, --check-strength)',
                'add': 'Add a new password (options: --name, --username, --password, --notes, --auto-generate-password)',
                'delete': 'Delete a password (options: --name)',
                'search': 'Search entries with fuzzy matching (options: --threshold)',
                'generate': 'Generate random password (options: --length, --count, --check-strength)',
                'backup': 'Create a backup (options: --name)',
                'restore': 'Restore from backup (options: --file, --merge)',
                'security': 'Check security status',
                'exit': 'Exit the interactive shell',
                'help': 'Show this help message',
            }

            for cmd_name, desc in commands.items():
                click.secho(f"{cmd_name:10}", fg="cyan", nl=False)
                click.secho(f" - {desc}", fg="white")
            click.secho("-" * 60, fg="blue")
            click.secho("Tip: Use Tab for command and entry name completion.", fg="bright_black")
            click.secho("For more details, type 'help <command>'", fg="bright_black")

    def complete_show(self, text, line, begidx, endidx):
        """Complete entry names for show command."""
        if not self.entries:
            return []
        return [e.name for e in self.entries if e.name.lower().startswith(text.lower())]

    def complete_delete(self, text, line, begidx, endidx):
        """Complete entry names for delete command."""
        if not self.entries:
            return []
        return [e.name for e in self.entries if e.name.lower().startswith(text.lower())]

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