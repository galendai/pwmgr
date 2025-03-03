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
            click.echo("Passwords do not match.")
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
        click.echo("Password manager already initialized.")
        if not click.confirm("Do you want to reset? This will delete all stored passwords!"):
            return
    
    click.echo("Initializing password manager...")
    
    # Prompt for master password
    master_password = get_master_password(confirm=True)
    
    # Initialize the password file
    storage.initialize(master_password)
    
    click.echo("Password manager initialized successfully.")


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
        click.echo("Invalid master password.")
        sys.exit(1)
    
    # Check if entry with this name already exists
    if any(entry.name == name for entry in entries):
        click.echo(f"Entry with name '{name}' already exists.")
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
        click.echo(f"Generated password: {password}")
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
    
    click.echo(f"Password entry '{name}' added successfully.")


@cli.command()
@click.option("--name", "-n", help="Filter by name (case-insensitive substring match)")
def list(name: Optional[str]):
    """List all password entries."""
    # Get master password
    master_password = get_master_password()
    
    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        click.echo("Invalid master password.")
        sys.exit(1)
    
    # Filter entries if name is provided
    if name:
        entries = [entry for entry in entries if name.lower() in entry.name.lower()]
    
    # Display entries
    if not entries:
        click.echo("No password entries found.")
        return
    
    click.echo("\nPassword Entries:")
    click.echo("-" * 50)
    for entry in sorted(entries, key=lambda e: e.name.lower()):
        click.echo(f"- {entry.name} ({entry.username})")
    click.echo("-" * 50)
    click.echo(f"Total: {len(entries)} entries")


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
        click.echo("Invalid master password.")
        sys.exit(1)
    
    # Find entry
    entry = next((e for e in entries if e.name.lower() == name.lower()), None)
    if not entry:
        click.echo(f"No entry found with name '{name}'.")
        return
    
    # Display entry
    click.echo("\nPassword Entry Details:")
    click.echo("-" * 50)
    click.echo(f"Name: {entry.name}")
    click.echo(f"Username: {entry.username}")
    
    if show_password:
        click.echo(f"Password: {entry.password}")
    else:
        hidden_pw = "*" * min(len(entry.password), 10)
        click.echo(f"Password: {hidden_pw} (use --show-password to reveal)")
    
    if entry.notes:
        click.echo(f"Notes: {entry.notes}")
    
    click.echo(f"Created: {entry.created_at}")
    click.echo(f"Updated: {entry.updated_at}")
    click.echo("-" * 50)


@cli.command()
@click.option("--name", "-n", required=True, help="Name of the entry to delete")
def delete(name: str):
    """Delete a password entry."""
    # Get master password
    master_password = get_master_password()
    
    # Load entries
    entries = storage.load(master_password)
    if entries is None:
        click.echo("Invalid master password.")
        sys.exit(1)
    
    # Check if entry exists
    if not any(entry.name.lower() == name.lower() for entry in entries):
        click.echo(f"No entry found with name '{name}'.")
        return
    
    # Confirm deletion
    if not click.confirm(f"Are you sure you want to delete entry '{name}'?"):
        return
    
    # Remove entry
    entries = [entry for entry in entries if entry.name.lower() != name.lower()]
    
    # Save updated entries
    storage.save(entries, master_password)
    
    click.echo(f"Password entry '{name}' deleted successfully.")


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
            click.echo(f"{i+1}. {password}")
        else:
            click.echo(password)


if __name__ == "__main__":
    cli() 