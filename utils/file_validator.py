import zipfile
import os
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from config import config
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    ALLOWED_EXTENSIONS = {
        '.html', '.htm', '.css', '.js', '.json', '.txt', '.md', 
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
        '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.xml', '.map', '.webmanifest', '.pdf'
    }
    DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.php', '.py', '.rb', '.pl', '.jar', '.war'}
    MAX_FILES = 100
    MAX_DEPTH = 10
    
    @staticmethod
    def validate_zip_file(file_path: str) -> Tuple[bool, str, List[str]]:
        try:
            logger.info(f"Validating ZIP file: {file_path}")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                logger.info(f"Files in ZIP: {file_list}")
                
                if len(file_list) > FileValidator.MAX_FILES:
                    logger.error(f"Too many files: {len(file_list)} > {FileValidator.MAX_FILES}")
                    return False, f"Too many files in ZIP (max {FileValidator.MAX_FILES})", []
                
                errors = []
                valid_files = []
                
                for file_name in file_list:
                    logger.debug(f"Processing file: {file_name}")
                    
                    if file_name.endswith('/'):
                        logger.debug(f"Skipping directory: {file_name}")
                        continue
                    
                    if FileValidator._check_path_traversal(file_name):
                        error_msg = f"Path traversal detected: {file_name}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    if FileValidator._check_depth(file_name):
                        error_msg = f"Directory too deep: {file_name}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    file_ext = Path(file_name).suffix.lower()
                    logger.debug(f"File extension: {file_ext}")
                    
                    if file_ext in FileValidator.DANGEROUS_EXTENSIONS:
                        error_msg = f"Dangerous file type: {file_name}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    if file_ext not in FileValidator.ALLOWED_EXTENSIONS and file_ext != '':
                        error_msg = f"File type not allowed: {file_name} (extension: {file_ext})"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    try:
                        file_info = zip_ref.getinfo(file_name)
                        if file_info.file_size > 50 * 1024 * 1024:
                            error_msg = f"File too large: {file_name} ({file_info.file_size} bytes)"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            continue
                    except Exception as e:
                        error_msg = f"Cannot read file info: {file_name} - {str(e)}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    valid_files.append(file_name)
                    logger.debug(f"Valid file: {file_name}")
                
                logger.info(f"Valid files: {valid_files}")
                logger.info(f"Errors: {errors}")
                
                if errors:
                    error_summary = "; ".join(errors)
                    logger.error(f"ZIP validation failed: {error_summary}")
                    return False, error_summary, valid_files
                
                has_index = FileValidator._has_index_file(valid_files)
                logger.info(f"Has index file: {has_index}")
                
                if not has_index:
                    logger.error("No index.html or index.htm found")
                    return False, "No index.html or index.htm found", valid_files
                
                logger.info("ZIP validation successful")
                return True, "Valid ZIP file", valid_files
                
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP file: {str(e)}")
            return False, "Invalid ZIP file", []
        except Exception as e:
            logger.error(f"Error reading ZIP file: {str(e)}")
            return False, f"Error reading ZIP file: {str(e)}", []
    
    @staticmethod
    def _check_path_traversal(file_path: str) -> bool:
        return '..' in file_path or file_path.startswith('/')
    
    @staticmethod
    def _check_depth(file_path: str) -> bool:
        return len(Path(file_path).parts) > FileValidator.MAX_DEPTH
    
    @staticmethod
    def _has_index_file(file_list: List[str]) -> bool:
        logger.debug(f"Checking for index file in: {file_list}")
        
        # Acceptable index file names
        index_files = ['index.html', 'index.htm', 'default.html', 'home.html', 'main.html']
        
        for file_name in file_list:
            # Check both exact match and basename match
            basename = os.path.basename(file_name).lower()
            logger.debug(f"Checking file: {file_name}, basename: {basename}")
            if basename in index_files:
                logger.info(f"Found index file: {file_name}")
                return True
        
        # If no index file found, check if there's at least one HTML file
        html_files = [f for f in file_list if f.lower().endswith(('.html', '.htm'))]
        if html_files:
            logger.info(f"No index file found, but HTML files exist: {html_files}")
            return True
            
        logger.warning("No HTML files found in ZIP")
        return False
    
    @staticmethod
    def validate_file_size(file_size: int) -> Tuple[bool, str]:
        if file_size > config.MAX_FILE_SIZE:
            return False, f"File too large (max {config.MAX_FILE_SIZE // (1024*1024)}MB)"
        return True, "File size OK"
    
    @staticmethod
    def validate_file_type(filename: str) -> Tuple[bool, str]:
        if not filename.lower().endswith('.zip'):
            return False, "Only ZIP files are allowed"
        return True, "File type OK"