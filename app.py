import customtkinter as ctk
import threading
import re
import os
from datetime import datetime
from youtube_func import get_youtube_playlist, list_videos_from_channel, get_youtube_captions_from_one_video, get_youtube_video_title
import sys
import tkinter.filedialog as fd

# Set your API key here or load from a config
api_key='AIzaSyBWgU_1YFk9DzLLk0A_ooV_YFRjutGbCXk'

class YoutubeCaptionsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Captions Extractor")
        self.geometry("700x550")
        self.resizable(False, False)

        self.save_folder = os.path.join(os.path.expanduser("~"), "Downloads")  # Default to Downloads

        # Widgets
        self.url_label = ctk.CTkLabel(self, text="Paste YouTube URLs (one per line):")
        self.url_label.pack(pady=(20, 5))

        self.url_textbox = ctk.CTkTextbox(self, width=650, height=180)
        self.url_textbox.pack()

        self.progress = ctk.CTkProgressBar(self, width=650)
        self.progress.set(0)
        self.progress.pack(pady=(15, 5))

        self.status_label = ctk.CTkLabel(self, text="Status: Waiting for input.", wraplength=650)
        self.status_label.pack(pady=(5, 5))

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=(10, 5))

        self.extract_button = ctk.CTkButton(self.button_frame, text="Extract Captions", command=self.start_extraction)
        self.extract_button.grid(row=0, column=0, padx=10)

        self.clear_button = ctk.CTkButton(self.button_frame, text="Clear List", command=self.clear_list)
        self.clear_button.grid(row=0, column=1, padx=10)

        self.folder_button = ctk.CTkButton(self.button_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.grid(row=0, column=2, padx=10)

        self.folder_label = ctk.CTkLabel(self, text=f"Save to: {self.save_folder}", wraplength=650)
        self.folder_label.pack(pady=(5, 5))

        self.download_label = ctk.CTkLabel(self, text="", wraplength=650)
        self.download_label.pack(pady=(10, 5))

    def select_folder(self):
        folder = fd.askdirectory(title="Select folder to save captions")
        if folder:
            self.save_folder = folder
            self.folder_label.configure(text=f"Save to: {self.save_folder}")

    def clear_list(self):
        self.url_textbox.delete("1.0", "end")
        self.status_label.configure(text="Status: Waiting for input.")
        self.progress.set(0)
        self.download_label.configure(text="")

    def start_extraction(self):
        self.extract_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")
        self.status_label.configure(text="Status: Processing...")
        self.download_label.configure(text="")
        threading.Thread(target=self.extract_captions, daemon=True).start()

    def extract_captions(self):
        urls = self.url_textbox.get("1.0", "end").strip().splitlines()
        urls = [u.strip() for u in urls if u.strip()]
        if not urls:
            self.status_label.configure(text="Error: No URLs provided.")
            self.extract_button.configure(state="normal")
            self.clear_button.configure(state="normal")
            self.folder_button.configure(state="normal")
            return

        all_captions = []
        total = len(urls)
        processed = 0

        for url in urls:
            try:
                if "list=" in url:
                    # Playlist
                    videos = get_youtube_playlist(url, api_key)
                    for video in videos:
                        caption = get_youtube_captions_from_one_video(video['url'])
                        if caption:
                            all_captions.append(f"Title: {video['title']}\n{caption}\n")
                        processed += 1
                        self.progress.set(processed / (total * max(1, len(videos))))
                        self.update_idletasks()
                elif re.search(r"youtube\\.com/(user|channel|@)", url):
                    # Channel
                    videos = list_videos_from_channel(url, api_key, max_results=10)
                    for video in videos:
                        caption = get_youtube_captions_from_one_video(video['url'])
                        if caption:
                            all_captions.append(f"Title: {video['title']}\n{caption}\n")
                        processed += 1
                        self.progress.set(processed / (total * max(1, len(videos))))
                        self.update_idletasks()
                elif "youtu" in url:
                    # Single video
                    title = get_youtube_video_title(url, api_key)
                    caption = get_youtube_captions_from_one_video(url)
                    if caption:
                        all_captions.append(f"Title: {title}\n{caption}\n")
                    processed += 1
                    self.progress.set(processed / total)
                    self.update_idletasks()
                else:
                    self.status_label.configure(text=f"Warning: Unrecognized URL format: {url}")
            except Exception as e:
                self.status_label.configure(text=f"Error processing {url}: {e}")

        if all_captions:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Captions_{now}.txt"
            output_path = os.path.join(self.save_folder, filename)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(all_captions))
                self.status_label.configure(text="Status: Done!")
                self.download_label.configure(text=f"File saved: {output_path}")
            except Exception as e:
                self.status_label.configure(text=f"Error saving file: {e}")
        else:
            self.status_label.configure(text="No captions found for the provided URLs.")

        self.extract_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.folder_button.configure(state="normal")
        self.progress.set(1)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = YoutubeCaptionsApp()
    app.mainloop()