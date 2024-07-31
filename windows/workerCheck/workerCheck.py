import tkinter as tk
from tkinter import ttk
import subprocess
import psutil
import os
import time

# Chemin du fichier de verrouillage
# lock_file_path = r"C:\ILLOGIC_APP\workerCheck.lock"
documents_path = os.path.join(os.path.expanduser("~"), "Documents")
lock_file_path = os.path.join(documents_path, "workerCheckUi.lock")

class WorkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion du Worker")
        self.root.geometry("800x700")  # Définir la taille de la fenêtre

        # Forcer la fenêtre à s'afficher au premier plan
        self.root.attributes("-topmost", True)
        # Désactiver l'attribut "topmost" après 2 secondes
        # self.root.after(2000, lambda: self.root.attributes("-topmost", False))

        # Définir l'icône de la fenêtre (assurez-vous d'avoir une icône .ico dans le même répertoire ou spécifiez le chemin complet)
        self.root.iconbitmap(r"C:\ILLOGIC_APP\Prism\icons\Deadline_Worker_start.ico")  # Remplacez par le chemin vers votre fichier .ico

        # Définir les couleurs
        main_bg_color = "#313338"
        button_bg_color = "#383a40"
        button_fg_color = "#313338"
        text_fg_color = "white"
        self.message_fg_color = "orange"
        self.message_success_color = "green"

        # Configuration du style
        style = ttk.Style()
        style.theme_use("vista")

        # Définir la couleur de fond de la fenêtre principale
        self.root.configure(bg=main_bg_color)

        # Description
        self.description = tk.Label(
            self.root,
            text="Votre worker est en train de travailler, voulez-vous l'éteindre?",
            bg=main_bg_color, fg=text_fg_color, font=("Helvetica", 32),
            wraplength=760, justify="center"
        )
        self.description.pack(pady=10, padx=20)

        # Créer un Label pour l'image
        self.image_label = tk.Label(self.root, bg=main_bg_color)
        self.image_label.pack(pady=20)

        self.display_image(self.image_label, r"R:\pipeline\pipe\windows\workerCheck\image.png")

        # Frame pour contenir les boutons
        self.button_frame = ttk.Frame(self.root, style="Custom.TFrame")
        self.button_frame.pack(side=tk.BOTTOM, pady=20, padx=20)

        # Configuration du style pour le frame
        style.configure("Custom.TFrame", background=main_bg_color)

        # Style pour les boutons avec une taille plus grande
        style.configure("TButton", background=button_bg_color, foreground=button_fg_color,
                        padding=20, relief="flat", font=("Helvetica", 32))
        style.map("TButton",
                  background=[('active', button_bg_color)],
                  foreground=[('active', button_fg_color)])

        # Bouton "Non, fermer la fenêtre"
        self.btn_non = ttk.Button(self.button_frame, text="Non", command=self.fermer_fenetre)
        self.btn_non.pack(side=tk.RIGHT, padx=10)

        # Bouton "Oui"
        self.btn_oui = ttk.Button(self.button_frame, text="Oui", command=self.eteindre_worker)
        self.btn_oui.pack(side=tk.RIGHT, padx=10)

        # Label pour le message de fermeture
        self.message_label = tk.Label(self.root, text="", bg=main_bg_color,
                                      fg=self.message_fg_color, font=("Helvetica", 24))
        self.message_label.pack(pady=10)

        # Assurez-vous que le fichier de verrouillage est supprimé à la fermeture de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.fermer_fenetre)

    def eteindre_worker(self):
        print("Le worker a été éteint.")
        # Afficher le message de fermeture en cours
        self.message_label.config(text="Fermeture en cours", fg="orange")
        self.root.update_idletasks()  # Mettre à jour l'interface utilisateur

        # Exécuter la commande
        command = r'"C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe" RemoteControl %COMPUTERNAME% StopSlave'
        subprocess.run(command, shell=True)

        # Mettre à jour le message de fermeture avec succès
        self.message_label.config(text="Worker fermé! Fermeture de la fenêtre...", fg="green")
        self.root.update_idletasks()  # Mettre à jour l'interface utilisateur

        # Fermer la fenêtre après 3 secondes
        self.root.after(3000, self.fermer_fenetre)

    def fermer_fenetre(self):
        # Supprimer le fichier de verrouillage
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
        self.root.destroy()

    # Fonction pour afficher l'image
    def display_image(self, label, image_path):
        image = tk.PhotoImage(file=image_path)
        label.configure(image=image)
        label.image = image  # Garder une référence à l'image

def is_deadlineworker_running():
    # Parcourir tous les processus en cours
    for process in psutil.process_iter(['pid', 'name']):
        # Vérifier si le processus s'appelle 'deadlineworker.exe'
        if process.info['name'] == 'deadlineworker.exe':
            return True
    return False

def delete_lock_file_if_old(lock_file_path, max_age_hours=18):
    """Supprime le fichier de verrouillage s'il existe depuis plus de max_age_hours heures."""
    if os.path.exists(lock_file_path):
        file_age = time.time() - os.path.getmtime(lock_file_path)
        max_age_seconds = max_age_hours * 3600
        if file_age > max_age_seconds:
            os.remove(lock_file_path)
            print(f"Le fichier de verrouillage existait depuis plus de {max_age_hours} heures et a été supprimé.")

# Exemple d'utilisation
if __name__ == "__main__":
    delete_lock_file_if_old(lock_file_path)
    if os.path.exists(lock_file_path):
        print("Une instance de l'application est déjà en cours d'exécution.")
    else:
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write("lock")

        if is_deadlineworker_running():
            print("Le processus 'deadlineworker.exe' est en cours d'exécution.")
            root = tk.Tk()
            app = WorkerApp(root)
            root.mainloop()
        else:
            print("Le processus 'deadlineworker.exe' n'est pas en cours d'exécution.")

        # Assurez-vous que le fichier de verrouillage est supprimé lorsque le programme se termine
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
