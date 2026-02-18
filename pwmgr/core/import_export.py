"""
Import and export functionality for the password manager.
"""
import os
import json
import csv
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .models import PasswordEntry
from ..exceptions import ValidationError
from ..logger import log_audit
from ..crypto import EncryptionService


class ImportError(Exception):
    """Exception raised for import errors."""
    pass


class ExportError(Exception):
    """Exception raised for export errors."""
    pass


class DataImporter:
    """Handles importing password data from various formats."""

    @staticmethod
    def from_json(file_path: str) -> List[PasswordEntry]:
        """
        Import password entries from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            List of imported password entries

        Raises:
            ImportError: If import fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entries = []

            # Support different JSON formats
            if isinstance(data, list):
                entries_data = data
            elif isinstance(data, dict) and "entries" in data:
                entries_data = data["entries"]
            else:
                raise ImportError("Invalid JSON format: expected list or object with 'entries' key")

            for entry_dict in entries_data:
                try:
                    entry = PasswordEntry.from_dict(entry_dict)
                    entries.append(entry)
                except (KeyError, TypeError) as e:
                    # Skip invalid entries but continue
                    continue

            log_audit("IMPORT_JSON", {"path": file_path, "entries_count": len(entries)})
            return entries

        except json.JSONDecodeError as e:
            raise ImportError(f"Invalid JSON file: {str(e)}")
        except FileNotFoundError:
            raise ImportError(f"File not found: {file_path}")
        except Exception as e:
            raise ImportError(f"Import failed: {str(e)}")

    @staticmethod
    def from_csv(file_path: str) -> List[PasswordEntry]:
        """
        Import password entries from a CSV file.

        Expected columns: name, username, password, notes (optional)

        Args:
            file_path: Path to the CSV file

        Returns:
            List of imported password entries

        Raises:
            ImportError: If import fails
        """
        try:
            entries = []

            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)

                # Validate required columns
                if not reader.fieldnames:
                    raise ImportError("CSV file has no headers")

                required_columns = {'name', 'username', 'password'}
                if not required_columns.issubset(set(reader.fieldnames)):
                    raise ImportError(f"CSV must have columns: {required_columns}")

                for row in reader:
                    try:
                        entry = PasswordEntry(
                            name=row['name'].strip(),
                            username=row['username'].strip(),
                            password=row['password'],
                            notes=row.get('notes', '').strip() or None
                        )
                        entries.append(entry)
                    except Exception:
                        # Skip invalid entries but continue
                        continue

            log_audit("IMPORT_CSV", {"path": file_path, "entries_count": len(entries)})
            return entries

        except FileNotFoundError:
            raise ImportError(f"File not found: {file_path}")
        except Exception as e:
            raise ImportError(f"Import failed: {str(e)}")

    @staticmethod
    def from_encrypted(file_path: str, master_password: str) -> List[PasswordEntry]:
        """
        Import password entries from an encrypted backup file.

        Args:
            file_path: Path to the encrypted file
            master_password: Master password for decryption

        Returns:
            List of imported password entries

        Raises:
            ImportError: If import fails
        """
        try:
            with open(file_path, 'r') as f:
                encrypted_data = f.read()

            json_data = EncryptionService.decrypt_password_data(encrypted_data, master_password)
            if json_data is None:
                raise ImportError("Failed to decrypt file. Wrong password?")

            data = json.loads(json_data)

            if isinstance(data, dict) and "entries" in data:
                entries_data = data["entries"]
            elif isinstance(data, list):
                entries_data = data
            else:
                raise ImportError("Invalid encrypted file format")

            entries = [PasswordEntry.from_dict(entry_dict) for entry_dict in entries_data]

            log_audit("IMPORT_ENCRYPTED", {"path": file_path, "entries_count": len(entries)})
            return entries

        except ImportError:
            raise
        except FileNotFoundError:
            raise ImportError(f"File not found: {file_path}")
        except Exception as e:
            raise ImportError(f"Import failed: {str(e)}")


class DataExporter:
    """Handles exporting password data to various formats."""

    @staticmethod
    def to_json(entries: List[PasswordEntry], file_path: str) -> None:
        """
        Export password entries to a JSON file (unencrypted!).

        WARNING: This exports data in plaintext. Use with caution.

        Args:
            entries: List of password entries to export
            file_path: Path to the output file

        Raises:
            ExportError: If export fails
        """
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "entries_count": len(entries),
                "entries": [entry.to_dict() for entry in entries]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            log_audit("EXPORT_JSON", {"path": file_path, "entries_count": len(entries)})

        except Exception as e:
            raise ExportError(f"Export failed: {str(e)}")

    @staticmethod
    def to_csv(entries: List[PasswordEntry], file_path: str) -> None:
        """
        Export password entries to a CSV file (unencrypted!).

        WARNING: This exports data in plaintext. Use with caution.

        Args:
            entries: List of password entries to export
            file_path: Path to the output file

        Raises:
            ExportError: If export fails
        """
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['name', 'username', 'password', 'notes', 'created_at', 'updated_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for entry in entries:
                    writer.writerow({
                        'name': entry.name,
                        'username': entry.username,
                        'password': entry.password,
                        'notes': entry.notes or '',
                        'created_at': entry.created_at,
                        'updated_at': entry.updated_at
                    })

            log_audit("EXPORT_CSV", {"path": file_path, "entries_count": len(entries)})

        except Exception as e:
            raise ExportError(f"Export failed: {str(e)}")

    @staticmethod
    def to_encrypted(entries: List[PasswordEntry], file_path: str, master_password: str) -> None:
        """
        Export password entries to an encrypted file.

        Args:
            entries: List of password entries to export
            file_path: Path to the output file
            master_password: Master password for encryption

        Raises:
            ExportError: If export fails
        """
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "entries_count": len(entries),
                "entries": [entry.to_dict() for entry in entries]
            }

            json_data = json.dumps(data)
            encrypted_data = EncryptionService.encrypt_password_data(json_data, master_password)

            with open(file_path, 'w') as f:
                f.write(encrypted_data)

            log_audit("EXPORT_ENCRYPTED", {"path": file_path, "entries_count": len(entries)})

        except Exception as e:
            raise ExportError(f"Export failed: {str(e)}")
