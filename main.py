from datetime import datetime, timedelta, timezone
from tkinter import BOTH, END, LEFT, Tk, PhotoImage, Toplevel, Text, Listbox
from tkinter import ttk as tk
from tkinter import filedialog as fd
from tkinter import simpledialog as sd
from tkinter import messagebox as tkmessage
from typing import Dict, List
from youtube import build_service, load_credentials, service, get_authenticated_service
from scheduler import PostScheduler, datetime_from_hour, TZ

import locale
import os
import json

locale.setlocale(locale.LC_ALL, "es_ES")

YOUTUBE_ACCEPTED_FILETYPES = [
    "*.avi",
    "*.mp4",
    "*.webm",
    "*.ogg",
    "*.wmv",
    "*.mov"
]

SAVE_FILENAME = "videos.json"
SCHEDULER_FILENAME = "scheduler.json"
POST_HOURS = [6, 13, 20]

videos: List[Dict[str, str]] = []
scheduler: PostScheduler


if os.path.isfile(SAVE_FILENAME):
    with open(SAVE_FILENAME) as file:
        videos = json.load(file)


if os.path.isfile(SCHEDULER_FILENAME):
    with open(SCHEDULER_FILENAME) as file:
        scheduler = PostScheduler.from_json(file, videos)
else:
    next_post = datetime_from_hour(POST_HOURS[0])
    scheduler = PostScheduler(0, datetime.fromtimestamp(0, tz=TZ), next_post, POST_HOURS, videos)
    
    with open(SCHEDULER_FILENAME, "w") as file:
        json.dump(scheduler.to_json(), file)

def Video(title: str, description: str, filepath: str, tags: List[str]) -> Dict[str, str]:
    return {
        "title": title,
        "description": description,
        "filepath": filepath,
        "tags": ",".join(tags)
    }

def save_videos():
    with open(SAVE_FILENAME, "w") as file:
        json.dump(videos, file)

def connections_frame(tabs: tk.Notebook):
    global ytlogo, instagram_logo, tiktok_logo, last_upload_label, next_upload_label, scheduler
    connections = tk.Frame(tabs)
    tabs.add(connections, text="Conexiones")

    ytlogo = PhotoImage(file="./res/youtube.png")
    tk.Label(connections, image=ytlogo).grid(row=0, column=0, rowspan=2, padx=10, pady=10)
    yt_status_label = tk.Label(connections)
    credentials = load_credentials()

    if credentials:
        build_service(credentials)
        yt_status_label.config(text="Online", foreground="green2")
    else:
        yt_status_label.config(text="Offline", foreground="red2")
        
    yt_status_label.grid(row=0, column=1, padx=10)

    def yt_auth():
        try:
            get_authenticated_service()
            yt_status_label.config(text="Online", foreground="green2")
        except:
            yt_status_label.config(text="Offline", foreground="red2")
            tkmessage.showerror("Error", "Ha ocurrido un error al iniciar sesión")

    tk.Button(connections, text="Iniciar Sesión", command=yt_auth).grid(row=1, column=1, padx=10)

    instagram_logo = PhotoImage(file="./res/instagram.png")
    tk.Label(connections, image=instagram_logo).grid(row=2, column=0, rowspan=2, padx=10, pady=10)
    instagram_status_label = tk.Label(connections, text="Offline", foreground="red2")
    instagram_status_label.grid(row=2, column=1, padx=10)

    def todo():
        tkmessage.showerror("Error", "Pendiente por implementar")

    tk.Button(connections, text="Iniciar Sesión", command=todo).grid(row=3, column=1, padx=10)

    tiktok_logo = PhotoImage(file="./res/tiktok.png")
    tk.Label(connections, image=tiktok_logo).grid(row=4, column=0, rowspan=2, padx=10, pady=10)
    tiktok_status_label = tk.Label(connections, text="Offline", foreground="red2")
    tiktok_status_label.grid(row=4, column=1, padx=10)
    tk.Button(connections, text="Iniciar Sesión", command=todo).grid(row=5, column=1, padx=10)

    last_post = "Nunca" if scheduler.last_post.timestamp() < 10000 else scheduler.last_post.strftime("%c")
    
    last_upload_label = tk.Label(connections, text=f"Último post: {last_post}")
    last_upload_label.grid(row=7, column=0, columnspan=4, padx=10, pady=10)
    
    next_upload_label = tk.Label(connections, text=f"Siguiente post: {scheduler.next_post.strftime('%c')}")
    next_upload_label.grid(row=7, column=5, columnspan=4, padx=10, pady=10)

def videos_frame(tabs: tk.Notebook):
    vids_frame = tk.Frame(tabs)
    tabs.add(vids_frame, text="Videos")

    tree = tk.Treeview(vids_frame, columns=["title", "description", "path", "tags"], show='headings')
    tree.heading("title", text="Título")
    tree.heading("description", text="Descripción")
    tree.heading("path", text="Ruta al archivo")
    tree.heading("tags", text="Etiquetas")

    for video in videos:
        tree.insert("", END, values=[video["title"], video["description"], video["filepath"], video["tags"]])

    def show_add_dialog(default_title: str = "", default_description: str = "", default_filepath: str = "", default_tags: str = ""):
        global root

        add_dialog = Toplevel(root)
        add_dialog.title("Bots")
        add_dialog.iconbitmap("res/trollface.ico")
        add_dialog.grab_set()

        tk.Label(add_dialog, text="Título").grid(row=0, column=0)
        tk.Label(add_dialog, text="Descripción").grid(row=1, column=0, sticky="n")
        tk.Label(add_dialog, text="Video").grid(row=2, column=0)
        tk.Label(add_dialog, text="Etiquetas").grid(row=3, column=0)
        
        title_entry = tk.Entry(add_dialog)
        title_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=10, columnspan=4)
        title_entry.insert(0, default_title)

        description_textbox = Text(add_dialog, width=40, height=6)
        description_textbox.grid(row=1, column=1, pady=5, padx=10, columnspan=4, sticky="ew")
        description_textbox.insert(END, default_description)

        filepath_label = tk.Label(add_dialog)
        filepath_label.grid(row=2, column=1, pady=5, padx=10, columnspan=3, sticky="w")

        if default_filepath == "":
            filepath_label.config(text="Sin seleccionar", foreground="red2")
        else:
            filepath_label.config(text=default_filepath, foreground="green2")

        def choose_file():
            filepath = fd.askopenfilename(filetypes=[("Archivos de video", YOUTUBE_ACCEPTED_FILETYPES)])

            if filepath is not None and filepath != "":
                filepath_label.config(text=filepath, foreground="green2")

        tk.Button(add_dialog, text="Browse", command=choose_file).grid(row=2, column=4, sticky="e", pady=5, padx=10)
        
        tags_list = Listbox(add_dialog, width=30, height=6)
        tags_list.grid(row=3, column=1, pady=5, padx=10, rowspan=2, columnspan=3, sticky="nsew")

        for tag in default_tags.split(","):
            if tag != "":
                tags_list.insert(END, tag)
        
        def add_tag():
            tag = sd.askstring("Etiqueta", "Ingrese la etiqueta a añadir")

            if tag is not None and tag != "":
                tags_list.insert(END, tag)

        def remove_tags():
            selection = tags_list.curselection()

            if len(selection) == 0:
                tkmessage.showerror("Error", "No se ha seleccionado ninguna etiqueta")
            else:
                for i in reversed(tags_list.curselection()):
                    tags_list.delete(i)
        
        tk.Button(add_dialog, text="Añadir Etiqueta", command=add_tag).grid(row=3, column=4, sticky="e", pady=5, padx=10)
        tk.Button(add_dialog, text="Eliminar Etiqueta", command=remove_tags).grid(row=4, column=4, sticky="e", pady=5, padx=10)

        def add_video():
            title = title_entry.get()
            description = description_textbox.get("1.0", "end-1c")
            filepath = filepath_label["text"]
            tags = tags_list.get(0, END)

            if title is None or title == "":
                tkmessage.showerror("Error", "Ingrese el título")
                return

            if description is None or description == "":
                tkmessage.showerror("Error", "Ingrese la descripción")
                return

            if filepath is None or filepath == "" or filepath == "Sin seleccionar":
                tkmessage.showerror("Error", "Seleccione un archivo de video")
                return

            global videos
            videos.append(Video(title, description, filepath, tags))
            tree.insert("", END, values=[title, description, filepath, tags])
            save_videos()
            add_dialog.destroy()

        tk.Button(add_dialog, text="Confirmar", command=add_video, width=20).grid(row=5, column=1, columnspan=2, pady=5, padx=10)
        tk.Button(add_dialog, text="Cancelar", command=add_dialog.destroy, width=20).grid(row=5, column=3, columnspan=2, pady=5, padx=10)

    def show_edit_dialog():
        selected_video = tree.item(tree.focus())

        if selected_video == "":
            tkmessage.showerror("Error", "Seleccione un video para editarlo")
        else:
            show_add_dialog(*selected_video["values"])

    def remove_video():
        selected_video = tree.focus()

        if selected_video == "":
            tkmessage.showerror("Error", "Seleccione un video para eliminarlo")
        else:
            i = tree.index(selected_video)
            tree.delete(selected_video)
            global videos
            videos.pop(i)
            save_videos()

    tk.Button(vids_frame, text="Añadir video", command=show_add_dialog).grid(row=0, column=0, padx=5, sticky="new")
    tk.Button(vids_frame, text="Editar video", command=show_edit_dialog).grid(row=1, column=0, padx=5, sticky="new")
    tk.Button(vids_frame, text="Eliminar video", command=remove_video).grid(row=2, column=0, padx=5, sticky="new")
    tree.grid(row=0, column=1, rowspan=40)
    scrollbar = tk.Scrollbar(vids_frame, orient ="vertical", command = tree.yview)
    scrollbar.grid(row=0, column=2, sticky="ns", rowspan=40)
    tree.configure(xscrollcommand = scrollbar.set)

if __name__ == '__main__':
    global root

    root = Tk()
    root.title("Bots")
    root.iconbitmap("res/trollface.ico")
    tabs = tk.Notebook(root)
    tabs.pack(fill=BOTH)
    connections_frame(tabs)
    videos_frame(tabs)

    def schedule_next():
        global scheduler, root, last_upload_label, next_upload_label
        scheduler.upload_next()

        last_post = "Nunca" if scheduler.last_post.timestamp() < 10000 else scheduler.last_post.strftime("%c")
        last_upload_label.config(text=f"Último post: {last_post}")
        next_upload_label.config(text=f"Siguiente post: {scheduler.next_post.strftime('%c')}")

        with open(SCHEDULER_FILENAME, "w") as file:
            json.dump(scheduler.to_json(), file)

        root.after(scheduler.pending(), schedule_next)

    root.after(scheduler.pending(), schedule_next)
    root.mainloop()