"""
Command line interface for the password manager.
"""
import sys
import os
import getpass
from typing import List, Optional

import click

from ..core import PasswordEntry, PasswordStorage, PasswordGenerator
from ..core.validators import InputValidator
from ..exceptions import ValidationError, AuthenticationError, StorageError
from ..logger import log_audit, get_logger


# Create a storage instance
storage = PasswordStorage()


def get_master_password(confirm: bool = False) -> str:
    """
    Prompt the user for the master password.

    Args:
        confirm: Whether to ask for confirmation

    Returns:
        The entered master password
    """
    password = getpass.getpass("Enter master password: ")
    if confirm:
        confirm_password = getpass.getpass("Confirm master password: ")
        if password != confirm_password:
            click.secho("Passwords do not match.", fg="red", bold=True)
            sys.exit(1)
    return password


def handle_error(message: str, exception: Exception = None):
    """
    Handle and display errors consistently.

    Args:
        message: Error message to display
        exception: Optional exception for logging
    """
    click.secho(f"Error: {message}", fg="red", bold=True)
    if exception:
        get_logger().exception(f"CLI Error: {message}")
    else:
        get_logger().error(f"CLI Error: {message}")


@click.group()
def cli():
    """Password Manager CLI."""
    pass


@cli.command()
def init():
    """Initialize the password manager."""
    if storage.file_exists():
        click.secho("Password manager already initialized.", fg="yellow")
        if not click.confirm("Do you want to reset? This will delete all stored passwords!"):
            return

    click.secho("Initializing password manager...", fg="blue")

    # Prompt for master password
    master_password = get_master_password(confirm=True)

    # Validate master password strength
    try:
        InputValidator.validate_master_password(master_password)
    except ValidationError as e:
        handle_error(str(e), e)
        sys.exit(1)

    # Initialize the password file
    try:
        storage.initialize(master_password)
        log_audit("INIT", {"action": "initialize"})
        click.secho("Password manager initialized successfully.", fg="green", bold=True)
    except Exception as e:
        handle_error(f"Failed to initialize: {str(e)}", e)
        sys.exit(1)


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry (e.g., website or app name)")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--password", "-p", help="Password (if not provided, will be prompted)")
@click.option("--notes", help="Additional notes")
@click.option("--auto-generate-password", "-g", is_flag=True, help="Auto-generate a password")
@click.option("--password-length", default=16, help="Length of auto-generated password")
@click.option("--include-symbols", is_flag=True, default=True, help="Include symbols in generated password")
@click.option("--check-strength", is_flag=True, help="Show password strength analysis")
def add(name: str, username: str, password: Optional[str], notes: Optional[str],
        auto_generate_password: bool, password_length: int, include_symbols: bool,
        check_strength: bool):
    """Add a new password entry."""
    # Validate inputs
    try:
        name = InputValidator.validate_name(name)
        username = InputValidator.validate_username(username)
        InputValidator.validate_password_length(password_length)
    except ValidationError as e:
        handle_error(str(e), e)
        sys.exit(1)

    # Get master password
    master_password = get_master_password()

    # Load existing entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    # Check if entry with this name already exists
    if any(entry.name.lower() == name.lower() for entry in entries):
        click.secho(f"Entry with name '{name}' already exists.", fg="yellow")
        if not click.confirm("Do you want to overwrite?"):
            return
        # Remove existing entry
        entries = [entry for entry in entries if entry.name.lower() != name.lower()]

    # Generate or prompt for password
    if auto_generate_password:
        try:
            password = PasswordGenerator.generate(
                length=password_length,
                include_symbols=include_symbols
            )
        except ValueError as e:
            handle_error(str(e), e)
            sys.exit(1)
        click.secho("Generated password: ", fg="blue", nl=False)
        click.secho(password, fg="bright_blue")
    elif not password:
        password = getpass.getpass("Enter password: ")

    # Validate password
    try:
        password = InputValidator.validate_password(password)
    except ValidationError as e:
        handle_error(str(e), e)
        sys.exit(1)

    # Show password strength if requested
    if check_strength:
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)
        color = "green" if strength >= 4 else "yellow" if strength >= 3 else "red"
        click.secho(f"Password strength: {label}", fg=color)
        if suggestions:
            click.secho("Suggestions:", fg="yellow")
            for suggestion in suggestions:
                click.secho(f"  - {suggestion}", fg="yellow")

    # Create and add new entry
    new_entry = PasswordEntry(
        name=name,
        username=username,
        password=password,
        notes=notes
    )

    entries.append(new_entry)

    # Save entries
    try:
        storage.save(entries, master_password)
        log_audit("ADD_ENTRY", {"name": name, "username": username})
        click.secho(f"Password entry '{name}' added successfully.", fg="green")
    except Exception as e:
        handle_error(f"Failed to save entry: {str(e)}", e)
        sys.exit(1)


@cli.command()
@click.option("--name", "-n", help="Filter by name (case-insensitive substring match)")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def list(name: Optional[str], json_output: bool):
    """List all password entries."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    # Filter entries if name is provided
    if name:
        entries = [entry for entry in entries if name.lower() in entry.name.lower()]

    # Display entries
    if not entries:
        click.secho("No password entries found.", fg="yellow")
        return

    # JSON output
    if json_output:
        import json as json_module
        output = [entry.to_dict() for entry in entries]
        click.echo(json_module.dumps(output, indent=2))
        return

    # Sort entries by name
    sorted_entries = sorted(entries, key=lambda e: e.name.lower())

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


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry to show")
@click.option("--show-password", "-p", is_flag=True, help="Show the password")
@click.option("--check-strength", is_flag=True, help="Show password strength analysis")
def show(name: str, show_password: bool, check_strength: bool):
    """Show details of a specific password entry."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    # Find entry
    entry = next((e for e in entries if e.name.lower() == name.lower()), None)
    if not entry:
        click.secho(f"No entry found with name '{name}'.", fg="yellow")
        return

    log_audit("SHOW_ENTRY", {"name": name})

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


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry to delete")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def delete(name: str, force: bool):
    """Delete a password entry."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    # Check if entry exists
    if not any(entry.name.lower() == name.lower() for entry in entries):
        click.secho(f"No entry found with name '{name}'.", fg="yellow")
        return

    # Confirm deletion
    if not force and not click.confirm(click.style(f"Are you sure you want to delete entry '{name}'?", fg="yellow", bold=True)):
        return

    # Remove entry
    entries = [entry for entry in entries if entry.name.lower() != name.lower()]

    # Save updated entries
    try:
        storage.save(entries, master_password)
        log_audit("DELETE_ENTRY", {"name": name})
        click.secho(f"Password entry '{name}' deleted successfully.", fg="green")
    except Exception as e:
        handle_error(f"Failed to delete entry: {str(e)}", e)
        sys.exit(1)


@cli.command()
@click.option("--length", "-l", default=16, help="Length of the password")
@click.option("--include-lowercase/--no-lowercase", default=True, help="Include lowercase letters")
@click.option("--include-uppercase/--no-uppercase", default=True, help="Include uppercase letters")
@click.option("--include-digits/--no-digits", default=True, help="Include digits")
@click.option("--include-symbols/--no-symbols", default=True, help="Include symbols")
@click.option("--count", "-c", default=1, help="Number of passwords to generate")
@click.option("--check-strength", is_flag=True, help="Show password strength analysis")
def generate(length: int, include_lowercase: bool, include_uppercase: bool,
             include_digits: bool, include_symbols: bool, count: int, check_strength: bool):
    """Generate random password(s)."""
    # Validate length
    try:
        InputValidator.validate_password_length(length)
    except ValidationError as e:
        handle_error(str(e), e)
        sys.exit(1)

    for i in range(count):
        try:
            password = PasswordGenerator.generate(
                length=length,
                include_lowercase=include_lowercase,
                include_uppercase=include_uppercase,
                include_digits=include_digits,
                include_symbols=include_symbols
            )
        except ValueError as e:
            handle_error(str(e), e)
            sys.exit(1)

        if count > 1:
            click.secho(f"{i+1}. ", fg="blue", nl=False)
            click.secho(password, fg="bright_green")
        else:
            click.secho(password, fg="bright_green")

        # Show password strength if requested
        if check_strength:
            strength, label, suggestions = PasswordGenerator.check_password_strength(password)
            color = "green" if strength >= 4 else "yellow" if strength >= 3 else "red"
            click.secho(f"   Strength: {label}", fg=color)


@cli.command()
def shell():
    """Start an interactive shell session."""
    from .interactive_shell import run_interactive_shell

    log_audit("START_SHELL", {})
    # Run the interactive shell
    run_interactive_shell()


@cli.command()
def security():
    """Check security status and show warnings."""
    warnings = storage.get_security_warnings()

    click.secho("\nSecurity Status:", fg="bright_blue", bold=True)
    click.secho("-" * 50, fg="blue")

    if warnings:
        click.secho("Warnings:", fg="yellow")
        for warning in warnings:
            click.secho(f"  - {warning}", fg="yellow")
    else:
        click.secho("No security warnings.", fg="green")

    click.secho("-" * 50, fg="blue")


@cli.command()
@click.option("--name", "-n", help="Backup name (default: timestamp-based)")
@click.option("--output", "-o", help="Output directory (default: ~/.pwmgr/backups)")
def backup(name: Optional[str], output: Optional[str]):
    """Create a backup of all password entries."""
    from ..core.backup import BackupManager

    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    # Create backup
    backup_manager = BackupManager(backup_dir=output)
    try:
        backup_path = backup_manager.create_backup(entries, master_password, name=name)
        click.secho(f"Backup created successfully.", fg="green")
        click.secho(f"Path: {backup_path}", fg="bright_black")
        click.secho(f"Entries backed up: {len(entries)}", fg="blue")
    except Exception as e:
        handle_error(f"Backup failed: {str(e)}", e)
        sys.exit(1)


@cli.command()
@click.option("--file", "-f", "backup_file", required=True, help="Backup file to restore")
@click.option("--merge", is_flag=True, help="Merge with existing entries instead of replacing")
def restore(backup_file: str, merge: bool):
    """Restore password entries from a backup."""
    from ..core.backup import BackupManager

    # Get master password
    master_password = get_master_password()

    # Restore backup
    backup_manager = BackupManager()
    try:
        restored_entries = backup_manager.restore_backup(backup_file, master_password)
    except Exception as e:
        handle_error(f"Restore failed: {str(e)}", e)
        sys.exit(1)

    if merge:
        # Load existing entries
        existing_entries = storage.load(master_password)
        if existing_entries is None:
            handle_error("Invalid master password.")
            sys.exit(1)

        # Merge entries (prefer restored entries for duplicates)
        existing_names = {e.name.lower() for e in existing_entries}
        merged = [e for e in existing_entries if e.name.lower() not in {r.name.lower() for r in restored_entries}]
        merged.extend(restored_entries)
        entries_to_save = merged

        click.secho(f"Merged {len(restored_entries)} entries from backup.", fg="blue")
        click.secho(f"Total entries: {len(entries_to_save)}", fg="blue")
    else:
        entries_to_save = restored_entries
        click.secho(f"Restored {len(restored_entries)} entries from backup.", fg="blue")

    # Confirm restore
    if not click.confirm(click.style("Do you want to proceed with the restore?", fg="yellow", bold=True)):
        click.secho("Restore cancelled.", fg="yellow")
        return

    # Save restored entries
    try:
        storage.save(entries_to_save, master_password)
        click.secho("Restore completed successfully.", fg="green", bold=True)
    except Exception as e:
        handle_error(f"Failed to save restored entries: {str(e)}", e)
        sys.exit(1)


@cli.command("list-backups")
def list_backups():
    """List all available backups."""
    from ..core.backup import BackupManager

    backup_manager = BackupManager()
    backups = backup_manager.list_backups()

    if not backups:
        click.secho("No backups found.", fg="yellow")
        return

    click.secho("\nAvailable Backups:", fg="bright_blue", bold=True)
    click.secho("-" * 70, fg="blue")

    for backup in backups:
        size_kb = backup["size"] / 1024
        click.secho(f"  {backup['filename']}", fg="white")
        click.secho(f"    Created: {backup['created_at']}", fg="bright_black")
        click.secho(f"    Size: {size_kb:.1f} KB", fg="bright_black")
        click.secho(f"    Path: {backup['path']}", fg="bright_black")
        click.secho("")

    click.secho(f"Total: {len(backups)} backup(s)", fg="green")


@cli.command()
@click.option("--file", "-f", "import_file", required=True, help="File to import")
@click.option("--format", type=click.Choice(['json', 'csv', 'encrypted']), required=True, help="Import format")
@click.option("--merge", is_flag=True, help="Merge with existing entries instead of replacing")
def import_data(import_file: str, format: str, merge: bool):
    """Import password entries from a file."""
    from ..core.import_export import DataImporter, ImportError

    # Import entries
    try:
        if format == 'json':
            imported_entries = DataImporter.from_json(import_file)
        elif format == 'csv':
            imported_entries = DataImporter.from_csv(import_file)
        elif format == 'encrypted':
            master_password = get_master_password()
            imported_entries = DataImporter.from_encrypted(import_file, master_password)
    except ImportError as e:
        handle_error(str(e), e)
        sys.exit(1)

    click.secho(f"Found {len(imported_entries)} entries to import.", fg="blue")

    # Get master password for saving
    master_password = get_master_password()

    if merge:
        # Load existing entries
        existing_entries = storage.load(master_password)
        if existing_entries is None:
            handle_error("Invalid master password.")
            sys.exit(1)

        # Merge entries
        merged = [e for e in existing_entries if e.name.lower() not in {i.name.lower() for i in imported_entries}]
        merged.extend(imported_entries)
        entries_to_save = merged

        click.secho(f"Merged {len(imported_entries)} new entries.", fg="blue")
    else:
        entries_to_save = imported_entries

    # Confirm import
    if not click.confirm(click.style("Do you want to proceed with the import?", fg="yellow", bold=True)):
        click.secho("Import cancelled.", fg="yellow")
        return

    # Save imported entries
    try:
        storage.save(entries_to_save, master_password)
        click.secho(f"Successfully imported {len(imported_entries)} entries.", fg="green", bold=True)
    except Exception as e:
        handle_error(f"Failed to save imported entries: {str(e)}", e)
        sys.exit(1)


@cli.command()
@click.option("--file", "-f", "export_file", required=True, help="Output file path")
@click.option("--format", type=click.Choice(['json', 'csv', 'encrypted']), required=True, help="Export format")
def export_data(export_file: str, format: str):
    """Export password entries to a file."""
    from ..core.import_export import DataExporter, ExportError

    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        handle_error("Invalid master password.")
        sys.exit(1)

    if not entries:
        click.secho("No entries to export.", fg="yellow")
        return

    # Warn for unencrypted formats
    if format in ['json', 'csv']:
        click.secho("WARNING: Exporting to unencrypted format!", fg="red", bold=True)
        click.secho("Your passwords will be stored in plaintext.", fg="red")
        if not click.confirm(click.style("Are you sure you want to continue?", fg="yellow", bold=True)):
            click.secho("Export cancelled.", fg="yellow")
            return

    # Export entries
    try:
        if format == 'json':
            DataExporter.to_json(entries, export_file)
        elif format == 'csv':
            DataExporter.to_csv(entries, export_file)
        elif format == 'encrypted':
            DataExporter.to_encrypted(entries, export_file, master_password)
    except ExportError as e:
        handle_error(str(e), e)
        sys.exit(1)

    click.secho(f"Successfully exported {len(entries)} entries.", fg="green", bold=True)
    click.secho(f"File: {export_file}", fg="bright_black")


if __name__ == "__main__":
    cli()