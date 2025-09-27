import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple
from config import config

class FileManager:
    @staticmethod
    def extract_zip_to_directory(zip_path: str, target_directory: str) -> Tuple[bool, str]:
        try:
            Path(target_directory).mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_directory)
            
            # when zip opens, it creates a folder with the same name as the zip fil
           
            FileManager._fix_directory_structure(target_directory)
            FileManager._set_permissions(target_directory)
            
            return True, "Extraction successful"
            
        except Exception as e:
            if os.path.exists(target_directory):
                shutil.rmtree(target_directory)
            return False, f"Extraction failed: {str(e)}"
    
    @staticmethod
    def delete_directory(directory_path: str) -> Tuple[bool, str]:
        try:
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path)
                return True, "Directory deleted successfully"
            return True, "Directory does not exist"
        except Exception as e:
            return False, f"Failed to delete directory: {str(e)}"
    
    @staticmethod
    def move_directory(source_path: str, target_path: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(source_path):
                return False, "Source directory does not exist"
            
            if os.path.exists(target_path):
                return False, "Target directory already exists"
            
            shutil.move(source_path, target_path)
            FileManager._set_permissions(target_path)
            
            return True, "Directory moved successfully"
            
        except Exception as e:
            return False, f"Failed to move directory: {str(e)}"
    
    @staticmethod
    def get_directory_size(directory_path: str) -> int:
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
    
    @staticmethod
    def get_file_count(directory_path: str) -> int:
        file_count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory_path):
                file_count += len(filenames)
        except Exception:
            pass
        return file_count
    
    @staticmethod
    def cleanup_temp_files(temp_directory: str = None):
        if temp_directory is None:
            temp_directory = config.UPLOAD_FOLDER
        
        try:
            for filename in os.listdir(temp_directory):
                file_path = os.path.join(temp_directory, filename)
                if os.path.isfile(file_path):
                    file_age = os.path.getctime(file_path)
                    import time
                    if time.time() - file_age > 3600:
                        os.unlink(file_path)
        except Exception:
            pass
    
    @staticmethod
    def _set_permissions(directory_path: str):
        try:
            import pwd
            import grp
            
            try:
                husniddin_uid = pwd.getpwnam('husniddin').pw_uid
                www_data_gid = grp.getgrnam('www-data').gr_gid
            except KeyError:
                husniddin_uid = os.getuid()
                www_data_gid = grp.getgrnam('www-data').gr_gid
            
            # Set ownership and permissions
            for root, dirs, files in os.walk(directory_path):
                os.chown(root, husniddin_uid, www_data_gid)
                os.chmod(root, 0o775)
                
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    os.chown(dir_path, husniddin_uid, www_data_gid)
                    os.chmod(dir_path, 0o775)
                    
                for f in files:
                    file_path = os.path.join(root, f)
                    os.chown(file_path, husniddin_uid, www_data_gid)
                    os.chmod(file_path, 0o664)
                    
        except Exception as e:
            # Fallback to basic permissions if ownership change fails
            try:
                for root, dirs, files in os.walk(directory_path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
            except Exception:
                pass
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def _fix_directory_structure(target_directory: str):
        """
        
        """
        try:
            index_files = ['index.html', 'index.htm', 'default.html', 'home.html']
            root_has_index = any(
                os.path.exists(os.path.join(target_directory, idx)) 
                for idx in index_files
            )
            
            if root_has_index:
                return  
            
            macosx_path = os.path.join(target_directory, '__MACOSX')
            if os.path.exists(macosx_path):
                shutil.rmtree(macosx_path)
            
            html_files = []
            for root, dirs, files in os.walk(target_directory):
                dirs[:] = [d for d in dirs if d != '__MACOSX']
                
                for file in files:
                    if file.lower().endswith(('.html', '.htm')):
                        html_files.append(os.path.join(root, file))
            
            if not html_files:
                return 
            
            best_index = None
            
            for html_file in html_files:
                basename = os.path.basename(html_file).lower()
                if basename in index_files:
                    best_index = html_file
                    break
            
            if not best_index and html_files:
                best_index = html_files[0]
            
            if best_index:
                target_index = os.path.join(target_directory, 'index.html')
                
                source_dir = os.path.dirname(best_index)
                if source_dir != target_directory:
                    for item in os.listdir(source_dir):
                        source_item = os.path.join(source_dir, item)
                        target_item = os.path.join(target_directory, item)
                        
                        if os.path.isfile(source_item):
                            if not os.path.exists(target_item):
                                shutil.copy2(source_item, target_item)
                        elif os.path.isdir(source_item):
                            if not os.path.exists(target_item):
                                shutil.copytree(source_item, target_item)
                
                if not os.path.exists(target_index):
                    shutil.copy2(best_index, target_index)
                    
        except Exception as e:
            import logging
            logging.warning(f"Directory structure fix failed: {str(e)}")
    
    @staticmethod
    def is_safe_path(base_path: str, target_path: str) -> bool:
        try:
            base_path = os.path.abspath(base_path)
            target_path = os.path.abspath(target_path)
            return target_path.startswith(base_path)
        except Exception:
            return False