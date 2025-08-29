"""
File service for handling document uploads and text extraction
"""
import logging
import os
from datetime import datetime

import PyPDF2
from docx import Document
from flask import current_app, request
from werkzeug.utils import secure_filename

# import textract  # Removed due to deprecation warnings
from app import db
from app.models.contract import Contract

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file operations and text extraction"""

    # Supported file extensions with text extraction capabilities
    # PDF: PyPDF2, DOCX/DOC: python-docx, TXT: built-in, RTF: regex-based extraction
    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "rtf"}

    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in FileService.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def secure_filename_with_timestamp(filename):
        """Create secure filename with timestamp to handle duplicates"""
        try:
            # Get base name and extension
            name, ext = os.path.splitext(filename)

            # Create timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

            # Create secure filename
            secure_name = secure_filename(name)

            # Combine with timestamp
            final_filename = f"{secure_name}_{timestamp}{ext}"

            return final_filename

        except Exception as e:
            logger.error(f"Error creating secure filename: {e}")
            raise

    @staticmethod
    def create_upload_directory_structure():
        """Create organized directory structure for uploads"""
        try:
            base_path = current_app.config["UPLOAD_FOLDER"]
            current_year = datetime.now().year
            current_month = datetime.now().month

            # Create year directory
            year_path = os.path.join(base_path, str(current_year))
            if not os.path.exists(year_path):
                os.makedirs(year_path)

            # Create month directory
            month_path = os.path.join(year_path, f"{current_month:02d}")
            if not os.path.exists(month_path):
                os.makedirs(month_path)

            return month_path

        except Exception as e:
            logger.error(f"Error creating upload directory structure: {e}")
            raise

    @staticmethod
    def save_uploaded_file(file, contract_id=None):
        """Save uploaded file to organized directory structure"""
        try:
            if not file or file.filename == "":
                raise ValueError("No file selected")

            if not FileService.allowed_file(file.filename):
                raise ValueError(
                    f"File type not allowed. Allowed types: {', '.join(FileService.ALLOWED_EXTENSIONS)}"
                )

            # Create directory structure
            upload_path = FileService.create_upload_directory_structure()

            # Create secure filename with timestamp
            filename = FileService.secure_filename_with_timestamp(file.filename)
            file_path = os.path.join(upload_path, filename)

            # Save file
            file.save(file_path)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Get MIME type
            mime_type = file.content_type or "application/octet-stream"

            logger.info(f"File saved successfully: {filename} ({file_size} bytes)")

            return {
                "filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type,
            }

        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise

    @staticmethod
    def extract_text_from_file(file_path, mime_type):
        """Extract text from uploaded document"""
        try:
            text = ""
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == ".pdf":
                text = FileService._extract_pdf_text(file_path)
            elif file_extension in [".docx", ".doc"]:
                text = FileService._extract_word_text(file_path)
            elif file_extension == ".txt":
                text = FileService._extract_text_text(file_path)
            elif file_extension == ".rtf":
                text = FileService._extract_rtf_text(file_path)
            else:
                # Fallback to built-in Python libraries for other formats
                text = FileService._extract_with_fallback(file_path)

            logger.info(
                f"Text extracted successfully from {file_path}: {len(text)} characters"
            )
            return text

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            # Return empty string on error, but log the issue
            return ""

    @staticmethod
    def _extract_pdf_text(file_path):
        """Extract text from PDF using PyPDF2"""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                return text.strip()

        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

    @staticmethod
    def _extract_word_text(file_path):
        """Extract text from Word documents using python-docx"""
        try:
            doc = Document(file_path)
            text = ""

            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"

            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting Word text: {e}")
            raise

    @staticmethod
    def _extract_text_text(file_path):
        """Extract text from plain text files"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    return file.read().strip()
            except Exception as e:
                logger.error(f"Error reading text file with latin-1 encoding: {e}")
                raise
        except Exception as e:
            logger.error(f"Error extracting text from text file: {e}")
            raise

    @staticmethod
    def _extract_rtf_text(file_path):
        """Extract text from RTF files using built-in Python libraries"""
        try:
            # Use built-in Python libraries for RTF processing
            import re

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                # Simple RTF text extraction - remove RTF markup
                # Remove RTF control words and braces
                text = re.sub(r"\\[a-z]+\d*", "", content)
                text = re.sub(r"[{}]", "", text)
                # Remove extra whitespace
                text = re.sub(r"\s+", " ", text).strip()
                return text
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    content = file.read()
                    import re

                    text = re.sub(r"\\[a-z]+\d*", "", content)
                    text = re.sub(r"[{}]", "", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    return text
            except Exception as e:
                logger.error(f"Error reading RTF file with latin-1 encoding: {e}")
                raise
        except Exception as e:
            logger.error(f"Error extracting RTF text: {e}")
            raise

    @staticmethod
    def _extract_with_fallback(file_path):
        """Fallback text extraction using built-in Python libraries"""
        try:
            # Try to read as plain text with different encodings
            encodings = ["utf-8", "latin-1", "cp1252"]
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, return empty string
            logger.warning(f"Could not extract text from {file_path} with any encoding")
            return ""

        except Exception as e:
            logger.error(f"Error in fallback text extraction: {e}")
            return ""

    @staticmethod
    def delete_file(file_path):
        """Delete file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted successfully: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise

    @staticmethod
    def move_to_deleted_folder(file_path, filename):
        """Move file to deleted folder for 30-day retention"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found for deletion: {file_path}")
                return False

            # Create deleted folder structure
            base_path = current_app.config["UPLOAD_FOLDER"]
            deleted_path = os.path.join(base_path, "deleted")
            if not os.path.exists(deleted_path):
                os.makedirs(deleted_path)

            # Create timestamped filename for deleted folder
            timestamp = datetime.now().strftime("%Y-%m-%d")
            deleted_filename = f"{timestamp}_{filename}"
            deleted_file_path = os.path.join(deleted_path, deleted_filename)

            # Move file
            os.rename(file_path, deleted_file_path)

            logger.info(
                f"File moved to deleted folder: {filename} -> {deleted_filename}"
            )
            return deleted_file_path

        except Exception as e:
            logger.error(f"Error moving file to deleted folder: {e}")
            raise

    @staticmethod
    def cleanup_expired_deleted_files():
        """Clean up files in deleted folder older than 30 days"""
        try:
            from datetime import datetime, timedelta

            base_path = current_app.config["UPLOAD_FOLDER"]
            deleted_path = os.path.join(base_path, "deleted")

            if not os.path.exists(deleted_path):
                return 0

            cutoff_date = datetime.now() - timedelta(days=30)
            deleted_count = 0

            for filename in os.listdir(deleted_path):
                file_path = os.path.join(deleted_path, filename)

                # Check if file is older than 30 days
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Expired deleted file removed: {filename}")
                    except Exception as e:
                        logger.error(
                            f"Error removing expired deleted file {filename}: {e}"
                        )

            logger.info(f"Cleanup completed: {deleted_count} expired files removed")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during deleted files cleanup: {e}")
            raise

    @staticmethod
    def get_file_info(file_path):
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)

            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "accessed": datetime.fromtimestamp(stat.st_atime),
            }

        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
