import datetime
import os
import getpass

def main():
    # Obtenir le nom de la machine
    machine_name = os.getenv('COMPUTERNAME')
    
    # Obtenir le nom de l'utilisateur
    user_name = getpass.getuser()
    
    with open(r"R:\pipeline\pipe\windows\workerCheck\log.txt", "a") as log_file:
        log_file.write(f"Script execute a : {datetime.datetime.now()} par {user_name} sur {machine_name}\n")

if __name__ == "__main__":
    main()
