"""
Command line interface for the password manager.
"""
import sys
import os
import getpass
from typing import List, Optional

import click

from ..core import PasswordEntry, PasswordStorage, PasswordGenerator


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

    # Initialize the password file
    storage.initialize(master_password)

    click.secho("Password manager initialized successfully.", fg="green", bold=True)


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry (e.g., website or app name)")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--password", "-p", help="Password (if not provided, will be prompted)")
@click.option("--notes", help="Additional notes")
@click.option("--auto-generate-password", "-g", is_flag=True, help="Auto-generate a password")
@click.option("--password-length", default=16, help="Length of auto-generated password")
@click.option("--include-symbols", is_flag=True, default=True, help="Include symbols in generated password")
def add(name: str, username: str, password: Optional[str], notes: Optional[str],
        auto_generate_password: bool, password_length: int, include_symbols: bool):
    """Add a new password entry."""
    # Get master password
    master_password = get_master_password()

    # Load existing entries
    entries = storage.load(master_password)
    if entries is None:
        click.secho("Invalid master password.", fg="red", bold=True)
        sys.exit(1)

    # Check if entry with this name already exists
    if any(entry.name == name for entry in entries):
        click.secho(f"Entry with name '{name}' already exists.", fg="yellow")
        if not click.confirm("Do you want to overwrite?"):
            return
        # Remove existing entry
        entries = [entry for entry in entries if entry.name != name]

    # Generate or prompt for password
    if auto_generate_password:
        password = PasswordGenerator.generate(
            length=password_length,
            include_symbols=include_symbols
        )
        click.secho("Generated password: ", fg="blue", nl=False)
        click.secho(password, fg="bright_blue")
    elif not password:
        password = getpass.getpass("Enter password: ")

    # Create and add new entry
    new_entry = PasswordEntry(
        name=name,
        username=username,
        password=password,
        notes=notes
    )

    entries.append(new_entry)

    # Save entries
    storage.save(entries, master_password)

    click.secho(f"Password entry '{name}' added successfully.", fg="green")


@cli.command()
@click.option("--name", "-n", help="Filter by name (case-insensitive substring match)")
def list(name: Optional[str]):
    """List all password entries."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        click.secho("Invalid master password.", fg="red", bold=True)
        sys.exit(1)

    # Filter entries if name is provided
    if name:
        entries = [entry for entry in entries if name.lower() in entry.name.lower()]

    # Display entries
    if not entries:
        click.secho("No password entries found.", fg="yellow")
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
def show(name: str, show_password: bool):
    """Show details of a specific password entry."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        click.secho("Invalid master password.", fg="red", bold=True)
        sys.exit(1)

    # Find entry
    entry = next((e for e in entries if e.name.lower() == name.lower()), None)
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


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry to delete")
def delete(name: str):
    """Delete a password entry."""
    # Get master password
    master_password = get_master_password()

    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        click.secho("Invalid master password.", fg="red", bold=True)
        sys.exit(1)

    # Check if entry exists
    if not any(entry.name.lower() == name.lower() for entry in entries):
        click.secho(f"No entry found with name '{name}'.", fg="yellow")
        return

    # Confirm deletion
    if not click.confirm(click.style(f"Are you sure you want to delete entry '{name}'?", fg="yellow", bold=True)):
        return

    # Remove entry
    entries = [entry for entry in entries if entry.name.lower() != name.lower()]

    # Save updated entries
    storage.save(entries, master_password)

    click.secho(f"Password entry '{name}' deleted successfully.", fg="green")


@cli.command()
@click.option("--length", "-l", default=16, help="Length of the password")
@click.option("--include-lowercase/--no-lowercase", default=True, help="Include lowercase letters")
@click.option("--include-uppercase/--no-uppercase", default=True, help="Include uppercase letters")
@click.option("--include-digits/--no-digits", default=True, help="Include digits")
@click.option("--include-symbols/--no-symbols", default=True, help="Include symbols")
@click.option("--count", "-c", default=1, help="Number of passwords to generate")
def generate(length: int, include_lowercase: bool, include_uppercase: bool,
             include_digits: bool, include_symbols: bool, count: int):
    """Generate random password(s)."""
    for i in range(count):
        password = PasswordGenerator.generate(
            length=length,
            include_lowercase=include_lowercase,
            include_uppercase=include_uppercase,
            include_digits=include_digits,
            include_symbols=include_symbols
        )
        if count > 1:
            click.secho(f"{i+1}. ", fg="blue", nl=False)
            click.secho(password, fg="bright_green")
        else:
            click.secho(password, fg="bright_green")


@cli.command()
def shell():
    """Start an interactive shell session."""
    from .interactive_shell import run_interactive_shell
    
    # Run the interactive shell
    run_interactive_shell()


if __name__ == "__main__":
    cli()