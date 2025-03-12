import frappe
import os
from flask import Response
from frappe.utils.backups import BackupGenerator
from frappe import _
frappe.utils.logger.set_log_level("DEBUG")

@frappe.whitelist()
def download_backup(filename):
    """Stream the backup file to the client."""
    try:
        backup = BackupGenerator(
                db_name=frappe.conf.db_name,
                user=frappe.conf.db_name,
                password=frappe.conf.db_password,
                db_host=frappe.conf.db_host or "127.0.0.1",
                db_port=frappe.conf.db_port or "3306",
                db_type="mariadb"
            )
        backup.get_backup()
        frappe.logger("api").info(f"Backup generated: {backup.backup_path_db}")
        frappe.logger("api").info(f"Backup generated: {backup.backup_path_files}")
        frappe.logger("api").info(f"Backup generated: {backup.backup_path_private_files}")
        # Define the path to the backup files directory
        if filename == "database.sql.gz":
            file_path = backup.backup_path_db
        elif filename == "files.tar":
            file_path = backup.backup_path_files
        elif filename == "private-files.tar":
            file_path = backup.backup_path_private_files
        else:
            frappe.throw(_("Invalid filename requested"))

        # Check if the file exists
        if not os.path.exists(file_path):
            frappe.throw(_("File not found"), frappe.DoesNotExistError)

        # Stream the file using a generator
        def generate():
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk

        return Response(generate(), mimetype='application/octet-stream', headers={"Content-Disposition": f"attachment;filename={os.path.basename(file_path)}"})

    except Exception as e:
        frappe.logger("api").error(f"Error during file streaming: {str(e)}")
        frappe.throw(_("An error occurred during file streaming"))

@frappe.whitelist()
def upload_backup():
    """Generate a new backup and upload it to the local server"""
    try:
        if frappe.request.method == "GET":
            # Generate the backup
            frappe.logger("api").info("Starting backup generation")
            backup = BackupGenerator(
                db_name=frappe.conf.db_name,
                user=frappe.conf.db_name,
                password=frappe.conf.db_password,
                db_host=frappe.conf.db_host or "127.0.0.1",
                db_port=frappe.conf.db_port or "3306",
                db_type="mariadb"
            )
            backup.get_backup()
            frappe.logger("api").info(f"Backup generated: {backup.backup_path_db}")
            frappe.logger("api").info(f"Backup generated: {backup.backup_path_files}")
            frappe.logger("api").info(f"Backup generated: {backup.backup_path_private_files}")

            # Prepare response with backup and tar files
            with open(backup.backup_path_db, 'rb') as f:
                backup_content = f.read()
                frappe.logger("api").info(f"Backup size: {len(backup_content)} bytes")

            with open(backup.backup_path_files, 'rb') as f:
                public_files_content = f.read()
                frappe.logger("api").info(f"Backup size: {len(public_files_content)} bytes")

            with open(backup.backup_path_private_files, 'rb') as f:
                private_files_content = f.read()
                frappe.logger("api").info(f"Backup size: {len(private_files_content)} bytes")

            return {
                'backup': {
                    'filename': os.path.basename(backup.backup_path_db),
                    'content': backup_content.decode('latin1')
                },
                'public_files': {
                    'filename': os.path.basename(backup.backup_path_files),
                    'content': public_files_content.decode('latin1')
                },
                'private_files': {
                    'filename': os.path.basename(backup.backup_path_private_files),
                    'content': private_files_content.decode('latin1')
                }
            }
        else:
            frappe.throw(_("Invalid request method"))
    except Exception as e:
        frappe.logger("api").error(f"Error during backup: {str(e)}")
        frappe.throw(_("An error occurred during backup generation"))