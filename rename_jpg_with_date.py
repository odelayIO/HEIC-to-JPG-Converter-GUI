#############################################################################################
#############################################################################################
#
#   The MIT License (MIT)
#   
#   Copyright (c) 2023 http://odelay.io 
#   
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#   
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#   
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#   
#   Contact : <everett@odelay.io>
#  
#   Description : This script renames the JPG file based on the meta date/time
#                 in the JPG file.  
#
#   Version History:
#   
#       Date        Description
#     -----------   -----------------------------------------------------------------------
#      2025-10-18    Original Creation
#
###########################################################################################



import os
import exifread
from datetime import datetime

def rename_jpg_from_exif(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f)
                try:
                    date_taken = str(tags['EXIF DateTimeOriginal'])
                    date_obj = datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
                    new_filename = date_obj.strftime('Date_%Y-%m-%d__Time_%H.%M.%S') + os.path.splitext(filename)[1].lower()
                    new_filepath = os.path.join(directory, new_filename)
                    os.rename(filepath, new_filepath)
                    print(f"'{date_taken}' : Renamed '{filename}' to '{new_filename}'")
                except KeyError:
                    print(f"No EXIF date found in '{filename}', skipped.")
                except ValueError:
                    print(f"Invalid date format in '{filename}', skipped.")


if __name__ == "__main__":
    target_directory = "./"  # Replace with the actual directory
    rename_jpg_from_exif(target_directory)
