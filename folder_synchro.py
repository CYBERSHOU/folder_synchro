from hashlib import md5
import errno
import os
import re
import shutil
import sys
import asyncio

SOURCE_FOLDER_PATH = ""
REPLICA_FOLDER_PATH = ""
SYNCHRO_DELAY = 0.0
LOG_FILE_PATH = ""

def main():
    if (sys.argv.__len__() != 5):
        print("The number of args was {count}, but it is expected to be 5.".format(count=sys.argv.__len__()))
        sys.exit(1)
        
    global SOURCE_FOLDER_PATH 
    global REPLICA_FOLDER_PATH
    global SYNCHRO_DELAY
    global LOG_FILE_PATH
    
    SOURCE_FOLDER_PATH = str(sys.argv[1])
    REPLICA_FOLDER_PATH = str(sys.argv[2])
    SYNCHRO_DELAY = float(sys.argv[3])
    LOG_FILE_PATH = str(sys.argv[4])

    if not os.path.isdir(SOURCE_FOLDER_PATH):
        print("The path provided for Source Folder does not exist, check again.")
        sys.exit(1)
        
    if not os.path.isdir(REPLICA_FOLDER_PATH):
        print("The path provided for Replica Folder does not exist, check again.")
        sys.exit(1)
        
    if not os.path.isfile(LOG_FILE_PATH):
        temp_input = input("The directory/file for Log File does not exist. Do you want it to be create it? (Y/n) ")
        pattern = re.compile("^([YyNn])")
        while not pattern.match(temp_input):
            temp_input = input(" (Y/n) ")
        if re.compile("^([Yy])").match(temp_input):
            try:
                dir_path = os.path.split(LOG_FILE_PATH)[0]
                os.makedirs(dir_path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
                    pass
                else: raise
            with open(LOG_FILE_PATH, "w") as f:
                f.write("")
        else: 
            sys.exit(1)

    if os.path.abspath(SOURCE_FOLDER_PATH) == os.path.abspath(REPLICA_FOLDER_PATH):
        print("The path provided for Source and Replica folders can't be the same.")
        sys.exit(1)

    if os.path.commonprefix([SOURCE_FOLDER_PATH, LOG_FILE_PATH]) == SOURCE_FOLDER_PATH:
        print("The Log File can't be in the Source Folder.")
        sys.exit(1)

    if os.path.commonprefix([REPLICA_FOLDER_PATH, LOG_FILE_PATH]) == REPLICA_FOLDER_PATH:
        print("The Log File can't be in the Replica Folder.")
        sys.exit(1)

    loop = asyncio.new_event_loop()
    loop.call_soon(folder_synchro, loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
    finally:
        loop.close()   

def folder_synchro(loop: asyncio.AbstractEventLoop):
    # verify changes in source folder and update in the replica folder, creating files and folders when needed
    for root, _, files in os.walk(SOURCE_FOLDER_PATH):
        for file in files:
            file_path = os.path.join(root,file)
            sub_path = os.path.dirname(file_path).replace(SOURCE_FOLDER_PATH.removesuffix("\\"), "", 1)
        replica_path = os.path.realpath(os.path.normpath(os.path.join(REPLICA_FOLDER_PATH + sub_path, file)))
        if os.path.isfile(replica_path):
            copy_file(file_path, replica_path)
        else:            
            create_file(file_path, replica_path)

    # remove files that are no longer in the source folder
    for root, dirs, files in os.walk(REPLICA_FOLDER_PATH):
        # if current directory (root) is empty in the replica folder then remove it
        if files.__len__() == 0 and dirs.__len__() == 0:
            os.rmdir(root)
            log_msg = "Removed empty directory from Replica Folder -> {dir}".format(dir=root)
            print(log_msg)
            write_to_log_file(log_msg)
        for file in files:
            os.path
            replica_path = os.path.join(root,file)
            sub_path = os.path.dirname(replica_path).replace(REPLICA_FOLDER_PATH.removesuffix("\\"), "", 1)
        file_path = os.path.normpath(os.path.join(SOURCE_FOLDER_PATH + sub_path, file))
        if not os.path.isfile(file_path):
            remove_file(replica_path)

    if int(loop.time()) % 2 == 0:
        print("Running...")
    # loop.stop() // Uncomment to only run once
    # schedules a call to run folder_synchro function again (repeatedly)
    loop.call_later(SYNCHRO_DELAY, folder_synchro, loop) 

def copy_file(file_path: str, replica_path: str):
    file_obj = open(file_path, "rb")
    file_hash = md5(file_obj.read())
    file_obj.close()
    replica_obj = open(replica_path, "rb")
    replica_Hash = md5(replica_obj.read())
    replica_obj.close()
    if (file_hash.hexdigest() != replica_Hash.hexdigest()):
        shutil.copyfile(file_path, replica_path)
        log_msg = "Copied/Updated contents of file {file} into Replica -> {replica}".format(file=file_path, replica=replica_path)
        print(log_msg)
        write_to_log_file(log_msg)

def create_file(file_path: str, replica_path: str):
    try:
        dir_path = os.path.split(replica_path)[0]
        os.makedirs(dir_path)
        log_msg = "Created a new folder in Replica Folder -> {folder}".format(folder=dir_path)
        print(log_msg)
        write_to_log_file(log_msg)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else: raise
    shutil.copyfile(file_path, replica_path)
    log_msg = "Copied/Created file {file} in Replica folder as {replica}".format(file=file_path, replica=replica_path)
    print(log_msg)
    write_to_log_file(log_msg)


def remove_file(replica_path: str):
    os.remove(replica_path)
    log_msg = "Deleted file '{replica_path}' in Replica folder as it no longer exists in Source.".format(replica_path=replica_path)
    print(log_msg)
    write_to_log_file(log_msg)

def write_to_log_file(log_msg: str):
    with open(LOG_FILE_PATH, "a") as f:
        f.write(log_msg + "\n")

main()
