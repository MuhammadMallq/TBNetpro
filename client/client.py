import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu
from datetime import datetime
import json
import hashlib
import winsound
import uuid
import time

SERVER_IP = "127.0.0.1"  # Localhost - karena server dan client di komputer yang sama
PORT = 12345

# ==================== COLOR THEMES ====================
# Modern Color Palette - Premium Dark Theme
COLORS_DARK = {
    'bg_primary': '#0a0a0f',
    'bg_secondary': '#12121a',
    'bg_card': '#1a1a24',
    'bg_input': '#0f0f15',
    'bg_hover': '#252530',
    'accent_blue': '#3b82f6',
    'accent_purple': '#8b5cf6',
    'accent_pink': '#ec4899',
    'accent_green': '#22c55e',
    'accent_red': '#ef4444',
    'accent_yellow': '#eab308',
    'text_primary': '#ffffff',
    'text_secondary': '#a1a1aa',
    'text_muted': '#52525b',
    'border': '#27272a',
    'bubble_own': '#3b82f6',
    'bubble_other': '#27272a',
}

# Light Theme - Clean & Modern dengan warna yang lebih soft dan nyaman
COLORS_LIGHT = {
    # Background colors - Soft pastels untuk kenyamanan mata
    'bg_primary': '#fafbfc',        # Putih sangat soft untuk main background
    'bg_secondary': '#f5f7fa',      # Abu-abu sangat muda untuk sidebar
    'bg_card': '#ffffff',           # Pure white untuk cards
    'bg_input': '#ffffff',          # White untuk input (dengan border)
    'bg_hover': '#e8edf5',          # Soft blue-gray untuk hover state
    
    # Accent colors - Tetap vibrant untuk actions
    'accent_blue': '#4F8AF7',       # Sedikit lebih soft dari default blue
    'accent_purple': '#9370db',     # Medium purple yang lebih soft
    'accent_pink': '#f06595',       # Pink yang lebih lembut
    'accent_green': '#51cf66',      # Green yang lebih cerah dan fresh
    'accent_red': '#ff6b6b',        # Red yang lebih soft
    'accent_yellow': '#ffd43b',     # Yellow yang lebih cerah
    
    # Text colors - High contrast untuk readability
    'text_primary': '#2c3e50',      # Dark blue-gray (lebih soft dari pure black)
    'text_secondary': '#6c757d',    # Medium gray untuk secondary text
    'text_muted': '#95a5a6',        # Light gray untuk muted text
    
    # Borders - Subtle tapi visible
    'border': '#d1dce6',            # Soft blue-gray border
    
    # Message bubbles
    'bubble_own': '#E3F2FD',        # Light blue untuk own messages
    'bubble_other': '#f8f9fa',      # Very light gray untuk other messages
}

# Avatar colors untuk users
AVATAR_COLORS = [
    '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
    '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#06b6d4'
]

def get_user_color(username):
    """
    Generate consistent color berdasarkan username
    Menggunakan hash untuk konsistensi warna di semua client
    """
    hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
    return AVATAR_COLORS[hash_val % len(AVATAR_COLORS)]

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyRTC - Real-Time Chat")
        self.root.geometry("750x550")
        self.root.minsize(600, 450)
        self.center_window(800, 600)
        
        # State variables
        self.username = ""
        self.client = None
        self.online_users = []
        self.current_theme = "dark"  # Default tema
        self.COLORS = COLORS_DARK.copy()  # Color scheme aktif
        
        # Typing indicator state
        self.typing_timer = None  # Timer untuk auto-stop typing
        self.is_typing = False  # Status typing user sendiri
        self.typing_users_list = []  # List user yang sedang mengetik
        
        # Message reactions state
        # Format: {message_id: {emoji: count}}
        self.message_reactions = {}
        
        # Message status state
        # Format: {message_id: {'status': 'sent'/'delivered'/'read', 'widget': label_widget}}
        self.message_status = {}
        
        # Message ID mapping
        # Format: {message_id: text_widget_index} untuk tracking position
        self.message_positions = {}
        
        # FITUR BARU: Discord-style Rooms state
        self.current_room = "general"
        self.available_rooms = ["general"]
        self.room_displays = {}  # {room_name: scrolledtext_widget}
        
        # Track images to prevent garbage collection
        self.images = []
        
        # Apply theme to root
        self.root.configure(bg=self.COLORS['bg_primary'])
        
        # Fonts
        self.font_title = ("Segoe UI", 32, "bold")
        self.font_heading = ("Segoe UI", 14, "bold")
        self.font_body = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 10)
        self.font_tiny = ("Segoe UI", 9)
        self.font_emoji = ("Segoe UI Emoji", 12)
        
        self.create_login_screen()
        self.create_chat_screen()
    
    def center_window(self, w, h):
        """Center window pada layar"""
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
    
    # ==================== THEME SWITCHER ====================
    def toggle_theme(self):
        """
        Toggle antara dark dan light theme
        Update semua widget dengan color scheme baru
        """
        # Switch theme
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.COLORS = COLORS_LIGHT.copy()
            theme_icon = "☀️"
        else:
            self.current_theme = "dark"
            self.COLORS = COLORS_DARK.copy()
            theme_icon = "🌙"
        
        # Update theme toggle button jika ada
        if hasattr(self, 'theme_btn'):
            self.theme_btn.config(
                text=theme_icon,
                bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['text_primary'],
                activebackground=self.COLORS['bg_hover']
            )
        
        # Reapply tema ke semua widget
        self.apply_theme_to_widgets()
    
    def apply_theme_to_widgets(self):
        """
        Apply color scheme ke semua widget
        Dipanggil setiap kali theme berubah
        """
        self.root.configure(bg=self.COLORS['bg_primary'])
        
        # Update login screen if visible
        if hasattr(self, 'login_frame') and self.login_frame.winfo_exists():
            self.update_login_theme()
            
        # Update chat screen if visible
        if hasattr(self, 'chat_frame') and self.chat_frame.winfo_exists():
            self.update_chat_theme()
            self.update_room_list(self.available_rooms)  # Refresh room button colors

    # FITUR BARU: Discord-style Rooms Methods
    
    def update_room_list(self, rooms):
        """Update sidebar dengan daftar rooms"""
        self.available_rooms = rooms
        
        # Clear existing buttons
        for widget in self.room_list_frame.winfo_children():
            widget.destroy()
            
        # Add buttons for each room
        for room in rooms:
            is_active = (room == self.current_room)
            bg = self.COLORS['bg_hover'] if is_active else self.COLORS['bg_secondary']
            fg = self.COLORS['accent_blue'] if is_active else self.COLORS['text_primary']
            
            # Container for room item (to include delete button)
            room_item = tk.Frame(self.room_list_frame, bg=bg)
            room_item.pack(fill=tk.X, pady=1)
            
            btn = tk.Button(room_item, text=f"# {room}",
                           font=self.font_small if not is_active else ("Segoe UI", 10, "bold"),
                           bg=bg, fg=fg, activebackground=self.COLORS['bg_hover'],
                           activeforeground=fg, relief="flat", cursor="hand2",
                           anchor="w", padx=10, pady=5,
                           command=lambda r=room: self.switch_room(r))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Delete button for custom rooms
            if room != "general":
                del_btn = tk.Button(room_item, text="✕", font=("Segoe UI", 8),
                                   bg=bg, fg=self.COLORS['text_muted'],
                                   activebackground=self.COLORS['accent_red'],
                                   activeforeground="#ffffff", relief="flat", cursor="hand2",
                                   command=lambda r=room: self.delete_room(r))
                del_btn.pack(side=tk.RIGHT, padx=5)

    def delete_room(self, room_name):
        """Kirim request hapus room ke server"""
        if messagebox.askyesno("Delete Room", f"Apakah Anda yakin ingin menghapus room '#{room_name}'?"):
            if self.client:
                self.client.send(f"[DELETE_ROOM]{room_name}\n".encode())

    def switch_room(self, room_name):
        """Ganti room aktif"""
        if self.current_room == room_name:
            return
            
        self.current_room = room_name
        self.room_label.config(text=f"# {room_name}")
        
        # Kirim sinyal switch ke server
        if self.client:
            try:
                self.client.send(f"[SWITCH_ROOM]{room_name}\n".encode())
            except:
                pass
                
        # Sembunyikan semua chat displays
        for display in self.room_displays.values():
            display.pack_forget()
            
        # Tampilkan display untuk room terpilih
        new_display = self.get_or_create_room_display(room_name)
        new_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display = new_display # Set as active display for helper methods
        
        # Update room list icons
        self.update_room_list(self.available_rooms)

    def get_or_create_room_display(self, room_name):
        """Ambil widget chat display untuk room tertentu, buat jika belum ada"""
        if room_name not in self.room_displays:
            display = scrolledtext.ScrolledText(self.chat_container, wrap=tk.WORD,
                                              font=self.font_body,
                                              bg=self.COLORS['bg_primary'],
                                              fg=self.COLORS['text_primary'],
                                              relief="flat", padx=15, pady=15)
            
            # Setup tags untuk display baru
            display.tag_configure('msg_own', font=("Segoe UI", 11, "bold"))
            display.tag_configure('msg_other', font=("Segoe UI", 11, "bold"))
            display.tag_configure('time', font=self.font_tiny)
            display.tag_configure('system_join', foreground=self.COLORS['accent_green'])
            display.tag_configure('system_leave', foreground=self.COLORS['accent_red'])
            display.tag_configure('system_info', foreground=self.COLORS['accent_blue'])
            display.tag_configure('system_error', foreground=self.COLORS['accent_red'])
            display.tag_configure('image_header', foreground=self.COLORS['text_secondary'], font=self.font_tiny)
            display.tag_configure('file_header', foreground=self.COLORS['accent_blue'], font=self.font_tiny)
            
            # Bind right click for reactions
            display.bind("<Button-3>", self.show_reaction_menu)
            
            # Matikan edit
            display.configure(state='disabled')
            
            self.room_displays[room_name] = display
            
            # Beri pesan welcome
            self.add_message(f"--- Welcome to #{room_name} ---", "system_info", room=room_name)
            
            # FITUR BARU: Request history dari server jika display baru dibuat
            if self.client:
                try:
                    self.client.send(f"[GET_HISTORY]{room_name}\n".encode())
                except:
                    pass
            
        return self.room_displays[room_name]

    def create_room_dialog(self):
        """Tampilkan dialog untuk membuat room baru"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Room")
        dialog.geometry("300x180")
        dialog.configure(bg=self.COLORS['bg_card'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="Room Name", font=self.font_heading,
                bg=self.COLORS['bg_card'], fg=self.COLORS['text_primary']).pack(pady=(20, 10))
        
        entry = tk.Entry(dialog, font=self.font_body, bg=self.COLORS['bg_input'],
                        fg=self.COLORS['text_primary'], insertbackground=self.COLORS['text_primary'])
        entry.pack(padx=20, fill=tk.X)
        entry.focus_set()
        
        def on_create():
            name = entry.get().strip().lower()
            if name:
                if " " in name:
                    messagebox.showerror("Error", "Nama room tidak boleh ada spasi")
                    return
                if self.client:
                    self.client.send(f"[CREATE_ROOM]{name}\n".encode())
                dialog.destroy()
            
        btn = tk.Button(dialog, text="Create Room", font=self.font_small,
                       bg=self.COLORS['accent_blue'], fg="#ffffff",
                       activebackground=self.COLORS['accent_blue'],
                       activeforeground="#ffffff", relief="flat", cursor="hand2",
                       command=on_create)
        btn.pack(pady=20, padx=20, fill=tk.X)

    def show_about_dialog(self):
        """Tampilkan panduan penggunaan aplikasi"""
        about_win = tk.Toplevel(self.root)
        about_win.title("Tentang PyRTC")
        about_win.geometry("500x550")
        about_win.configure(bg=self.COLORS['bg_primary'])
        about_win.transient(self.root)
        about_win.grab_set()
        
        # Header
        header = tk.Frame(about_win, bg=self.COLORS['bg_secondary'], pady=20)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🚀 Selamat Datang di PyRTC", 
                 font=("Segoe UI", 16, "bold"), 
                 bg=self.COLORS['bg_secondary'], 
                 fg=self.COLORS['accent_blue']).pack()
        
        # Content
        content = tk.Frame(about_win, bg=self.COLORS['bg_primary'], padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        guide_text = [
            ("🏠 Multiple Rooms", "Buat channel kustom dan ganti room melalui sidebar. Setiap room memiliki history chat tersendiri."),
            ("📎 File Sharing", "Kirim gambar atau dokumen (max 5MB) dengan mengeklik ikon klip di sebelah input pesan."),
            ("🎭 Message Reactions", "Klik kanan pada pesan apa pun untuk menambahkan reaksi emoji (seperti di Discord)."),
            ("⌨️ Typing Indicator", "Anda bisa melihat siapa yang sedang mengetik pesan secara real-time."),
            ("🌓 Theme Switcher", "Klik ikon ☀️/🌙 di pojok kanan atas untuk berganti antara Mode Gelap dan Terang."),
            ("✅ Read Receipts", "Cek status pesan Anda: ✓ (Sent), ✓✓ (Delivered), ✓✓ (Read/Biru).")
        ]
        
        for title, desc in guide_text:
            f = tk.Frame(content, bg=self.COLORS['bg_primary'], pady=8)
            f.pack(fill=tk.X)
            tk.Label(f, text=title, font=("Segoe UI", 11, "bold"), 
                     bg=self.COLORS['bg_primary'], fg=self.COLORS['accent_purple']).pack(anchor="w")
            tk.Label(f, text=desc, font=("Segoe UI", 9), 
                     bg=self.COLORS['bg_primary'], fg=self.COLORS['text_secondary'], 
                     wraplength=420, justify="left").pack(anchor="w", padx=5)
        
        # Footer
        tk.Button(about_win, text="Saya Mengerti", 
                 font=("Segoe UI", 10, "bold"),
                 bg=self.COLORS['accent_blue'], fg="#ffffff",
                 padx=20, pady=8, relief="flat", cursor="hand2",
                 command=about_win.destroy).pack(pady=20)

    # FITUR BARU: Discord-style File Sharing Methods
    
    def send_file(self):
        """Pilih file dan kirim ke server"""
        from tkinter import filedialog
        import base64
        import os
        
        filepath = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("Documents", "*.pdf *.txt *.docx *.xlsx"),
                ("All Files", "*.*")
            ]
        )
        
        if not filepath:
            return
            
        # Limit ukuran 5MB
        file_size = os.path.getsize(filepath)
        if file_size > 5 * 1024 * 1024:
            messagebox.showerror("Error", "File terlalu besar! Maksimal 5MB.")
            return
            
        try:
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                file_data = f.read()
                b64_data = base64.b64encode(file_data).decode()
            
            # Format: [FILE]room:filename:size:base64
            msg = f"[FILE]{self.current_room}:{filename}:{file_size}:{b64_data}"
            if self.client:
                self.client.send((msg + "\n").encode())
                self.add_message(f"📤 Uploading {filename}...", "system_info")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim file: {e}")

    def display_file(self, room, file_id, filename, sender, size, b64_data):
        """Tampilkan file dalam chat"""
        import base64
        
        # Decode data
        try:
            file_bytes = base64.b64decode(b64_data)
            
            # Jika gambar, tampilkan preview
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.display_image(filename, sender, file_bytes)
            else:
                self.display_file_attachment(filename, sender, size, b64_data)
        except Exception as e:
            print(f"Error decoding file: {e}")

    def display_image(self, filename, sender, image_bytes, room=None):
        """Tampilkan preview gambar inline"""
        from PIL import Image, ImageTk
        import io
        
        target_room = room if room else self.current_room
        display = self.get_or_create_room_display(target_room)
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize agar tidak terlalu besar
            max_width = 300
            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_height = int(float(image.height) * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
            photo = ImageTk.PhotoImage(image)
            self.images.append(photo)  # Simpan reference
            
            display.configure(state='normal')
            
            # Message header
            color = get_user_color(sender)
            display.insert(tk.END, f"\n● {sender} shared an image:\n", ("image_header",))
            display.tag_add(f"color_{sender}", "end-2c linestart", "end-2c lineend")
            display.tag_configure(f"color_{sender}", foreground=color)
            
            # Insert image
            display.image_create(tk.END, image=photo)
            display.insert(tk.END, "\n")
            
            display.see(tk.END)
            display.configure(state='disabled')
        except Exception as e:
            self.add_message(f"Error loading image from {sender}: {filename}", "system_error", room=target_room)

    def display_file_attachment(self, filename, sender, size, b64_data, room=None):
        """Tampilkan file attachment dengan tombol download"""
        target_room = room if room else self.current_room
        display = self.get_or_create_room_display(target_room)
        size_kb = int(size) / 1024
        
        display.configure(state='normal')
        
        # File info
        color = get_user_color(sender)
        display.insert(tk.END, f"\n📎 {sender} shared a file: {filename} ({size_kb:.1f} KB)\n", ("file_header",))
        
        # Download button
        btn_frame = tk.Frame(display, bg=self.COLORS['bg_hover'], padx=10, pady=5)
        btn = tk.Button(btn_frame, text=f"⬇️ Download {filename}", 
                       bg=self.COLORS['accent_blue'], fg="#ffffff",
                       font=self.font_tiny, relief="flat", cursor="hand2",
                       command=lambda: self.download_file(filename, b64_data))
        btn.pack()
        
        display.window_create(tk.END, window=btn_frame)
        display.insert(tk.END, "\n")
        
        display.see(tk.END)
        display.configure(state='disabled')

    def download_file(self, filename, b64_data):
        """Simpan file ke komputer user"""
        from tkinter import filedialog
        import base64
        
        save_path = filedialog.asksaveasfilename(
            initialfile=filename,
            title="Save File",
            defaultextension=os.path.splitext(filename)[1]
        )
        
        if save_path:
            try:
                file_bytes = base64.b64decode(b64_data)
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                messagebox.showinfo("Success", f"File saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan file: {e}")
    
    def update_login_theme(self):
        """Update tema untuk login screen"""
        # Akan di-implement setelah login screen dibuat
        pass
    
    def update_chat_theme(self):
        """Update tema untuk chat screen secara komprehensif"""
        self.chat_frame.config(bg=self.COLORS['bg_primary'])
        self.main_container.config(bg=self.COLORS['bg_primary'])
        self.chat_area.config(bg=self.COLORS['bg_primary'])
        self.chat_container.config(bg=self.COLORS['bg_primary'])

        # Update sidebar components
        if hasattr(self, 'sidebar'):
            self.sidebar.config(bg=self.COLORS['bg_secondary'])
            self.rooms_container.config(bg=self.COLORS['bg_secondary'])
            self.rooms_title_label.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'])
            self.room_list_frame.config(bg=self.COLORS['bg_secondary'])
            self.create_room_btn.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['accent_blue'])
            self.sidebar_sep1.config(bg=self.COLORS['border'])
            self.sidebar_header.config(bg=self.COLORS['bg_secondary'])
            self.users_title_label.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'])
            self.user_count_label.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_muted'])
            self.sidebar_sep2.config(bg=self.COLORS['border'])
            self.user_list_frame.config(bg=self.COLORS['bg_secondary'])
            
            # Refresh user list to update frames/labels inside it
            if hasattr(self, 'last_users_data'):
                self.update_user_list(self.last_users_data)
        
        # Update chat header
        if hasattr(self, 'header'):
            self.header.config(bg=self.COLORS['bg_secondary'])
            self.header_left.config(bg=self.COLORS['bg_secondary'])
            self.header_icon.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'])
            self.room_label.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'])
            self.header_right.config(bg=self.COLORS['bg_secondary'])
            self.status_dot.config(bg=self.COLORS['bg_secondary'])
            self.status_text.config(bg=self.COLORS['bg_secondary'])
            self.theme_btn.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'],
                                activebackground=self.COLORS['bg_hover'])

        # Update user banner
        if hasattr(self, 'user_banner'):
            self.user_banner.config(bg=self.COLORS['bg_card'])
            self.user_label.config(bg=self.COLORS['bg_card'], fg=self.COLORS['text_secondary'])

        # Update all chat displays
        for room_name, display in self.room_displays.items():
            display.config(
                bg=self.COLORS['bg_primary'],
                fg=self.COLORS['text_primary']
            )
            # Re-configure tag colors
            display.tag_configure('system_join', foreground=self.COLORS['accent_green'])
            display.tag_configure('system_leave', foreground=self.COLORS['accent_red'])
            display.tag_configure('system_info', foreground=self.COLORS['accent_blue'])
            display.tag_configure('time', foreground=self.COLORS['text_muted'])
            display.tag_configure('image_header', foreground=self.COLORS['text_secondary'], font=self.font_tiny)
            display.tag_configure('file_header', foreground=self.COLORS['accent_blue'], font=self.font_tiny)
            
        # Update input area
        if hasattr(self, 'input_area'):
            self.input_area.config(bg=self.COLORS['bg_secondary'])
            self.typing_label.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_muted'])
            self.input_container.config(bg=self.COLORS['bg_secondary'])
            self.attach_btn.config(bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_secondary'],
                                 activebackground=self.COLORS['bg_hover'])
            self.input_border.config(bg=self.COLORS['border'])
            self.input_inner.config(bg=self.COLORS['bg_input'])
            self.msg_entry.config(
                bg=self.COLORS['bg_input'],
                fg=self.COLORS['text_primary'],
                insertbackground=self.COLORS['accent_blue']
            )
            self.send_btn.config(bg=self.COLORS['accent_blue'], fg=self.COLORS['text_primary'])

        # Update reaction menu
        if hasattr(self, 'reaction_menu'):
            self.reaction_menu.config(bg=self.COLORS['bg_card'], fg=self.COLORS['text_primary'],
                                    activebackground=self.COLORS['accent_blue'])
    
    # ==================== LOGIN SCREEN ====================
    def create_login_screen(self):
        """Buat UI untuk login screen"""
        self.login_frame = tk.Frame(self.root, bg=self.COLORS['bg_primary'])
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center container
        center = tk.Frame(self.login_frame, bg=self.COLORS['bg_primary'])
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        # Animated-style logo
        tk.Label(center, text="💬", font=("Segoe UI Emoji", 64),
                bg=self.COLORS['bg_primary']).pack()
        
        # Gradient title simulation
        tk.Label(center, text="PyRTC", font=self.font_title,
                bg=self.COLORS['bg_primary'], fg=self.COLORS['accent_blue']).pack(pady=(0,5))
        
        tk.Label(center, text="Sistem Komunikasi Real-Time Multi-User", 
                font=self.font_small, bg=self.COLORS['bg_primary'], 
                fg=self.COLORS['text_secondary']).pack(pady=(0,40))
        
        # Card
        card = tk.Frame(center, bg=self.COLORS['bg_card'], padx=40, pady=35)
        card.pack()
        
        # Server status
        status_frame = tk.Frame(card, bg=self.COLORS['bg_card'])
        status_frame.pack(fill=tk.X, pady=(0,20))
        tk.Label(status_frame, text="●", font=("Segoe UI", 10),
                bg=self.COLORS['bg_card'], fg=self.COLORS['accent_green']).pack(side=tk.LEFT)
        tk.Label(status_frame, text=f" Server: {SERVER_IP}:{PORT}",
                font=self.font_tiny, bg=self.COLORS['bg_card'], 
                fg=self.COLORS['text_muted']).pack(side=tk.LEFT)
        
        # Username field
        tk.Label(card, text="Username", font=self.font_body,
                bg=self.COLORS['bg_card'], fg=self.COLORS['text_secondary'],
                anchor="w").pack(fill=tk.X, pady=(0,8))
        
        # Styled input
        entry_container = tk.Frame(card, bg=self.COLORS['border'], padx=2, pady=2)
        entry_container.pack(fill=tk.X, pady=(0,25))
        
        entry_inner = tk.Frame(entry_container, bg=self.COLORS['bg_input'])
        entry_inner.pack(fill=tk.X)
        
        self.username_entry = tk.Entry(entry_inner, font=self.font_body,
                                       bg=self.COLORS['bg_input'], fg=self.COLORS['text_primary'],
                                       insertbackground=self.COLORS['accent_blue'],
                                       relief="flat", width=30)
        self.username_entry.pack(padx=15, pady=12)
        self.username_entry.bind("<Return>", lambda e: self.connect_server())
        self.username_entry.bind("<FocusIn>", lambda e: entry_container.config(bg=self.COLORS['accent_blue']))
        self.username_entry.bind("<FocusOut>", lambda e: entry_container.config(bg=self.COLORS['border']))
        self.username_entry.focus_set()
        
        # Join button
        self.join_btn = tk.Button(card, text="🚀  Masuk ke Chat Room",
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.COLORS['accent_blue'], fg=self.COLORS['text_primary'],
                                 activebackground=self.COLORS['accent_purple'],
                                 relief="flat", cursor="hand2",
                                 command=self.connect_server)
        self.join_btn.pack(fill=tk.X, ipady=12)
        self.join_btn.bind("<Enter>", lambda e: self.join_btn.config(bg=self.COLORS['accent_purple']))
        self.join_btn.bind("<Leave>", lambda e: self.join_btn.config(bg=self.COLORS['accent_blue']))
        
        # New: About Button
        about_btn = tk.Button(card, text="❔ Cara Kerja Aplikasi",
                             font=self.font_tiny, bg=self.COLORS['bg_card'],
                             fg=self.COLORS['accent_blue'], relief="flat",
                             cursor="hand2", command=self.show_about_dialog)
        about_btn.pack(pady=(15,0))
        
        # Footer
        tk.Label(center, text="Network Programming Project © 2025",
                font=self.font_tiny, bg=self.COLORS['bg_primary'],
                fg=self.COLORS['text_muted']).pack(pady=(30,0))
    
    # ==================== CHAT SCREEN ====================
    def create_chat_screen(self):
        """Buat UI untuk chat screen dengan semua fitur baru"""
        self.chat_frame = tk.Frame(self.root, bg=self.COLORS['bg_primary'])
        
        # Main container dengan sidebar
        self.main_container = tk.Frame(self.chat_frame, bg=self.COLORS['bg_primary'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # ===== SIDEBAR =====
        self.sidebar = tk.Frame(self.main_container, bg=self.COLORS['bg_secondary'], width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # FITUR BARU: Rooms Section (Discord-style)
        self.rooms_container = tk.Frame(self.sidebar, bg=self.COLORS['bg_secondary'], pady=15)
        self.rooms_container.pack(fill=tk.X)
        
        self.rooms_title_label = tk.Label(self.rooms_container, text="🏠 ROOMS",
                font=self.font_heading, bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['text_primary'])
        self.rooms_title_label.pack(padx=15, anchor="w")
        
        # Room list container
        self.room_list_frame = tk.Frame(self.sidebar, bg=self.COLORS['bg_secondary'])
        self.room_list_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create Room Button
        self.create_room_btn = tk.Button(self.sidebar, text="+ Create New Room",
                                        font=self.font_tiny, bg=self.COLORS['bg_secondary'],
                                        fg=self.COLORS['accent_blue'], relief="flat",
                                        cursor="hand2", command=self.create_room_dialog)
        self.create_room_btn.pack(padx=15, anchor="w")
        
        # Separator 1
        self.sidebar_sep1 = tk.Frame(self.sidebar, bg=self.COLORS['border'], height=1)
        self.sidebar_sep1.pack(fill=tk.X, pady=10)
        
        # Sidebar header (Online Users)
        self.sidebar_header = tk.Frame(self.sidebar, bg=self.COLORS['bg_secondary'], pady=5)
        self.sidebar_header.pack(fill=tk.X)
        
        self.users_title_label = tk.Label(self.sidebar_header, text="👥 Online Users",
                font=self.font_heading, bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['text_primary'])
        self.users_title_label.pack(padx=15, anchor="w")
        
        self.user_count_label = tk.Label(self.sidebar_header, text="0 users online",
                                         font=self.font_tiny, bg=self.COLORS['bg_secondary'],
                                         fg=self.COLORS['text_muted'])
        self.user_count_label.pack(padx=15, anchor="w")
        
        # Separator 2
        self.sidebar_sep2 = tk.Frame(self.sidebar, bg=self.COLORS['border'], height=1)
        self.sidebar_sep2.pack(fill=tk.X)
        
        # User list container
        self.user_list_frame = tk.Frame(self.sidebar, bg=self.COLORS['bg_secondary'])
        self.user_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== CHAT AREA =====
        self.chat_area = tk.Frame(self.main_container, bg=self.COLORS['bg_primary'])
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Chat header
        self.header = tk.Frame(self.chat_area, bg=self.COLORS['bg_secondary'], pady=12)
        self.header.pack(fill=tk.X)
        
        self.header_left = tk.Frame(self.header, bg=self.COLORS['bg_secondary'])
        self.header_left.pack(side=tk.LEFT, padx=15)
        
        self.header_icon = tk.Label(self.header_left, text="💬", font=("Segoe UI Emoji", 18),
                bg=self.COLORS['bg_secondary'])
        self.header_icon.pack(side=tk.LEFT)
        
        # Dynamic Room Label
        self.room_label = tk.Label(self.header_left, text=f"# {self.current_room}", font=self.font_heading,
                bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'])
        self.room_label.pack(side=tk.LEFT, padx=(8,0))
        
        self.header_right = tk.Frame(self.header, bg=self.COLORS['bg_secondary'])
        self.header_right.pack(side=tk.RIGHT, padx=15)
        
        # FITUR BARU: Theme Toggle Button
        self.theme_btn = tk.Button(self.header_right, text="🌙" if self.current_theme == "dark" else "☀️",
                                   font=("Segoe UI Emoji", 16),
                                   bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary'],
                                   activebackground=self.COLORS['bg_hover'],
                                   relief="flat", cursor="hand2",
                                   command=self.toggle_theme, width=3)
        self.theme_btn.pack(side=tk.RIGHT, padx=(10,0))
        
        self.status_dot = tk.Label(self.header_right, text="●", font=("Segoe UI", 12),
                                  bg=self.COLORS['bg_secondary'], fg=self.COLORS['accent_green'])
        self.status_dot.pack(side=tk.LEFT)
        self.status_text = tk.Label(self.header_right, text="Connected", font=self.font_small,
                                   bg=self.COLORS['bg_secondary'], fg=self.COLORS['accent_green'])
        self.status_text.pack(side=tk.LEFT, padx=(4,0))
        
        # User banner
        self.user_banner = tk.Frame(self.chat_area, bg=self.COLORS['bg_card'], pady=8)
        self.user_banner.pack(fill=tk.X)
        self.user_label = tk.Label(self.user_banner, text="", font=self.font_small,
                                  bg=self.COLORS['bg_card'], fg=self.COLORS['text_secondary'])
        self.user_label.pack()
        
        # FITUR BARU: Typing Indicator Area (di bawah input)
        # Akan di-pack setelah input area untuk positioning yang benar
        
        # Input area (PACK FIRST sehingga selalu visible)
        self.input_area = tk.Frame(self.chat_area, bg=self.COLORS['bg_secondary'], pady=12)
        self.input_area.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Typing indicator label (di atas input)
        self.typing_label = tk.Label(self.input_area, text="", font=self.font_tiny,
                                     bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_muted'],
                                     anchor="w")
        self.typing_label.pack(fill=tk.X, padx=12, pady=(0,5))
        # Input container
        self.input_container = tk.Frame(self.input_area, bg=self.COLORS['bg_secondary'])
        self.input_container.pack(fill=tk.X, padx=12)
        
        # FITUR BARU: Attachment Button (📎)
        self.attach_btn = tk.Button(self.input_container, text="📎", font=("Segoe UI Emoji", 16),
                                   bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_secondary'],
                                   activebackground=self.COLORS['bg_hover'],
                                   relief="flat", cursor="hand2",
                                   command=self.send_file, width=3)
        self.attach_btn.pack(side=tk.LEFT, padx=(0,10))
        
        # Input dengan border effect
        self.input_border = tk.Frame(self.input_container, bg=self.COLORS['border'], padx=2, pady=2)
        self.input_border.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.input_inner = tk.Frame(self.input_border, bg=self.COLORS['bg_input'])
        self.input_inner.pack(fill=tk.X)
        
        self.msg_entry = tk.Entry(self.input_inner, font=self.font_body,
                                 bg=self.COLORS['bg_input'], fg=self.COLORS['text_primary'],
                                 insertbackground=self.COLORS['accent_blue'], relief="flat")
        self.msg_entry.pack(fill=tk.X, padx=10, pady=8)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.msg_entry.bind("<FocusIn>", lambda e: self.input_border.config(bg=self.COLORS['accent_blue']))
        self.msg_entry.bind("<FocusOut>", lambda e: self.input_border.config(bg=self.COLORS['border']))
        
        # FITUR BARU: Typing Indicator - bind key events
        self.msg_entry.bind("<KeyPress>", self.on_key_press)
        self.msg_entry.bind("<KeyRelease>", self.on_key_release)
        
        # Send button
        self.send_btn = tk.Button(self.input_container, text="➤", font=("Segoe UI", 14),
                                 bg=self.COLORS['accent_blue'], fg=self.COLORS['text_primary'],
                                 activebackground=self.COLORS['accent_purple'],
                                 relief="flat", cursor="hand2", width=3,
                                 command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=(10,0), ipady=4)
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.config(bg=self.COLORS['accent_purple']))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.config(bg=self.COLORS['accent_blue']))
        
        # Chat display container
        self.chat_container = tk.Frame(self.chat_area, bg=self.COLORS['bg_primary'])
        self.chat_container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize default room display
        self.chat_display = self.get_or_create_room_display("general")
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # FITUR BARU: Right-click menu untuk reactions
        self.reaction_menu = Menu(self.root, tearoff=0, bg=self.COLORS['bg_card'],
                                 fg=self.COLORS['text_primary'], activebackground=self.COLORS['accent_blue'])
        
        # Popular emojis untuk reaction
        popular_emojis = ["👍", "❤️", "😂", "😮", "😢", "🎉", "🔥", "👏"]
        for emoji in popular_emojis:
            self.reaction_menu.add_command(
                label=emoji,
                command=lambda e=emoji: self.add_reaction_at_cursor(e)
            )
    
    # ==================== TYPING INDICATOR ====================
    def on_key_press(self, event):
        """
        Handler ketika user menekan key di input
        Kirim typing indicator ke server
        """
        # Jangan kirim untuk special keys
        if event.keysym in ['Return', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
            return
        
        # Jika belum typing, kirim [TYPING] ke server
        if not self.is_typing and self.client:
            self.is_typing = True
            try:
                self.client.send("[TYPING]\n".encode())
            except:
                pass
    
    def on_key_release(self, event):
        """
        Handler ketika user release key
        Set timer untuk auto-stop typing setelah 2 detik idle
        """
        # Cancel timer sebelumnya jika ada
        if self.typing_timer:
            self.typing_timer.cancel()
        
        # Set timer baru untuk stop typing
        self.typing_timer = threading.Timer(2.0, self.stop_typing)
        self.typing_timer.start()
    
    def stop_typing(self):
        """
        Kirim stop typing indicator ke server
        Dipanggil setelah 2 detik tidak ada input
        """
        if self.is_typing and self.client:
            self.is_typing = False
            try:
                self.client.send("[STOP_TYPING]\n".encode())
            except:
                pass
    
    def update_typing_indicator(self, users):
        """
        Update tampilan typing indicator
        Args:
            users: List username yang sedang mengetik
        """
        if not users:
            self.typing_label.config(text="")
            return
        
        # Format text berdasarkan jumlah user
        if len(users) == 1:
            text = f"{users[0]} is typing..."
        elif len(users) == 2:
            text = f"{users[0]} and {users[1]} are typing..."
        else:
            text = f"{users[0]}, {users[1]} and {len(users)-2} others are typing..."
        
        self.typing_label.config(text=text)
    
    # ==================== MESSAGE REACTIONS ====================
    def show_reaction_menu(self, event):
        """
        Tampilkan reaction menu pada right-click
        Simpan posisi klik untuk tracking message
        """
        # Simpan index posisi klik
        self.last_click_index = self.chat_display.index(f"@{event.x},{event.y}")
        
        # Tampilkan menu di posisi mouse
        try:
            self.reaction_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.reaction_menu.grab_release()
    
    def add_reaction_at_cursor(self, emoji):
        """
        Tambahkan reaction pada message terdekat dengan cursor
        Args:
            emoji: Emoji yang dipilih untuk reaction
        """
        if not hasattr(self, 'last_click_index'):
            return
        
        # Cari message ID terdekat dari posisi klik
        # Scan backwards untuk find message dengan [MSG_ID:...]
        click_line = int(self.last_click_index.split('.')[0])
        
        # Cari message ID di sekitar click position
        found_msg_id = None
        for msg_id, pos in self.message_positions.items():
            msg_line = int(pos.split('.')[0])
            # Check jika click dalam range message (±5 lines)
            if abs(click_line - msg_line) <= 5:
                found_msg_id = msg_id
                break
        
        if found_msg_id and self.client:
            # Kirim reaction ke server
            # Format: [REACTION]message_id:emoji
            try:
                self.client.send(f"[REACTION]{found_msg_id}:{emoji}\n".encode())
            except:
                pass
    
    def update_reaction_display(self, message_id, emoji, username):
        """
        Update tampilan reaction pada message
        Args:
            message_id: ID pesan yang di-react
            emoji: Emoji reaction
            username: User yang menambahkan reaction
        """
        # Update internal state
        if message_id not in self.message_reactions:
            self.message_reactions[message_id] = {}
        
        if emoji not in self.message_reactions[message_id]:
            self.message_reactions[message_id][emoji] = []
        
        # Toggle: jika user sudah react dengan emoji ini, remove
        if username in self.message_reactions[message_id][emoji]:
            self.message_reactions[message_id][emoji].remove(username)
            if not self.message_reactions[message_id][emoji]:
                del self.message_reactions[message_id][emoji]
        else:
            self.message_reactions[message_id][emoji].append(username)
        
        # Update display jika message masih ada
        if message_id in self.message_positions:
            self.refresh_message_reactions(message_id)
    
    def refresh_message_reactions(self, message_id):
        """
        Refresh tampilan reactions untuk satu message
        Args:
            message_id: ID pesan yang akan di-refresh
        """
        if message_id not in self.message_positions:
            return
        
        # Cari tag untuk reaction line
        reaction_tag = f"reaction_{message_id}"
        
        # Hapus reaction line lama jika ada
        self.chat_display.configure(state='normal')
        
        # Cari semua text dengan tag ini dan hapus
        ranges = self.chat_display.tag_ranges(reaction_tag)
        if ranges:
            for i in range(0, len(ranges), 2):
                self.chat_display.delete(ranges[i], ranges[i+1])
        
        # Tambahkan reaction line baru jika ada reactions
        if message_id in self.message_reactions and self.message_reactions[message_id]:
            # Build reaction string
            reaction_str = "   "
            for emoji, users in self.message_reactions[message_id].items():
                count = len(users)
                reaction_str += f"{emoji} {count}  "
            
            # Insert di posisi message
            pos = self.message_positions[message_id]
            line_num = int(pos.split('.')[0])
            insert_pos = f"{line_num + 2}.0"  # 2 lines after message
            
            self.chat_display.insert(insert_pos, reaction_str + "\n", (reaction_tag, 'reaction'))
        
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)
    
    # ==================== MESSAGE STATUS ====================
    def update_message_status(self, message_id, status):
        """
        Update status indicator untuk message
        Args:
            message_id: ID pesan
            status: 'sent', 'delivered', atau 'read'
        """
        if message_id not in self.message_status:
            self.message_status[message_id] = {'status': status}
        else:
            self.message_status[message_id]['status'] = status
        
        # Update visual indicator
        self.refresh_message_status(message_id)
    
    def refresh_message_status(self, message_id):
        """
        Refresh tampilan status untuk satu message
        Args:
            message_id: ID pesan yang akan di-refresh
        """
        if message_id not in self.message_positions:
            return
        
        status = self.message_status.get(message_id, {}).get('status', 'sent')
        
        # Icon untuk setiap status
        status_icons = {
            'sent': '✓',  # Single check
            'delivered': '✓✓',  # Double check
            'read': '✓✓'  # Double check (dengan warna berbeda)
        }
        
        status_colors = {
            'sent': self.COLORS['text_muted'],
            'delivered': self.COLORS['text_muted'],
            'read': self.COLORS['accent_blue']
        }
        
        icon = status_icons.get(status, '✓')
        color = status_colors.get(status, self.COLORS['text_muted'])
        
        # Update atau create status tag
        status_tag = f"status_{message_id}"
        
        self.chat_display.configure(state='normal')
        
        # Hapus status lama
        ranges = self.chat_display.tag_ranges(status_tag)
        if ranges:
            for i in range(0, len(ranges), 2):
                self.chat_display.delete(ranges[i], ranges[i+1])
        
        # Tambahkan status baru di akhir message line
        pos = self.message_positions[message_id]
        line_num = int(pos.split('.')[0])
        end_pos = f"{line_num + 1}.end"  # End of message text line
        
        # Configure color tag
        self.chat_display.tag_configure(status_tag, foreground=color, font=("Segoe UI", 8))
        self.chat_display.insert(end_pos, f" {icon}", (status_tag, 'status'))
        
        self.chat_display.configure(state='disabled')
    
    def send_read_receipt(self, message_id):
        """
        Kirim read receipt ke server untuk message
        Args:
            message_id: ID pesan yang sudah dibaca
        """
        if self.client:
            try:
                self.client.send(f"[READ]{message_id}\n".encode())
            except:
                pass
    
    # ==================== USER LIST ====================
    def update_user_list(self, users_data):
        """
        Update sidebar dengan daftar user online dan room mereka
        Args:
            users_data: Dictionary {username: active_room} atau List [username]
        """
        # Simpan data user terakhir untuk keperluan ganti tema
        self.last_users_data = users_data
        # Handle backward compatibility jika server mengirim list
        if isinstance(users_data, list):
            self.online_users = users_data
            users_status = {u: "general" for u in users_data}
        else:
            self.online_users = list(users_data.keys())
            users_status = users_data
            
        # Clear existing user labels
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
            
        # Update user count
        self.user_count_label.config(text=f"{len(self.online_users)} users online")
        
        # Add labels for each user
        # Sort users agar diri sendiri di paling atas
        sorted_users = sorted(self.online_users, key=lambda x: (x != self.username, x.lower()))
        
        for user in sorted_users:
            room = users_status.get(user, "general")
            user_color = get_user_color(user)
            
            user_frame = tk.Frame(self.user_list_frame, bg=self.COLORS['bg_secondary'], pady=5)
            user_frame.pack(fill=tk.X)
            
            # Avatar circle simulation
            dot = tk.Label(user_frame, text="●", font=("Segoe UI", 14),
                          bg=self.COLORS['bg_secondary'], fg=user_color)
            dot.pack(side=tk.LEFT)
            
            # Name and status container
            name_cnt = tk.Frame(user_frame, bg=self.COLORS['bg_secondary'])
            name_cnt.pack(side=tk.LEFT, padx=8)
            
            display_name = f"{user} (You)" if user == self.username else user
            tk.Label(name_cnt, text=display_name, font=self.font_small,
                    bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_primary']).pack(anchor="w")
            
            # Room status text
            room_status = f"in # {room}"
            tk.Label(name_cnt, text=room_status, font=("Segoe UI", 8),
                    bg=self.COLORS['bg_secondary'], fg=self.COLORS['text_muted']).pack(anchor="w")           
    
    # ==================== CONNECTION ====================
    def connect_server(self):
        """Connect ke server dan join chat room"""
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showwarning("Peringatan", "Username tidak boleh kosong!")
            return
        
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((SERVER_IP, PORT))
            self.client.send((self.username + "\n").encode())
            
            # Switch ke chat
            self.login_frame.pack_forget()
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            self.root.title(f"PyRTC - {self.username}")
            self.user_label.config(text=f"👤 Logged in as: {self.username}")
            
            self.add_message(f"🎉 Selamat datang di PyRTC, {self.username}!", "system_info")
            
            # Start receiver thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.msg_entry.focus_set()
            
            # FITUR BARU: Request history untuk default room (general)
            try:
                self.client.send("[GET_HISTORY]general\n".encode())
            except:
                pass
            
        except Exception as e:
            messagebox.showerror("Error", f"Gagal terhubung: {e}")
    
    def receive_messages(self):
        """
        Thread untuk receive messages dari server
        Handle berbagai jenis message protocol
        """
        buffer = ""
        while True:
            try:
                data = self.client.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    if msg:
                        self.process_message(msg)
            except:
                break
        
        # Connection lost
        self.add_message("⚠️ Koneksi ke server terputus", "system_leave")
        self.status_dot.config(fg=self.COLORS['accent_red'])
        self.status_text.config(text="Disconnected", fg=self.COLORS['accent_red'])
    
    def process_message(self, msg):
        """
        Process incoming message berdasarkan protocol
        Args:
            msg: Raw message dari server
        """
        # 1. USER LIST UPDATE
        if msg.startswith("[USERS]"):
            try:
                # Format baru: dictionary {username: room}
                users_data = json.loads(msg[7:])
                self.root.after(0, lambda: self.update_user_list(users_data))
            except:
                pass
            return
        
        # 2. TYPING INDICATOR
        elif msg.startswith("[TYPING]"):
            username = msg[8:]
            if username != self.username and username not in self.typing_users_list:
                self.typing_users_list.append(username)
                self.root.after(0, lambda: self.update_typing_indicator(self.typing_users_list))
            return
        
        elif msg.startswith("[STOP_TYPING]"):
            username = msg[13:]
            if username in self.typing_users_list:
                self.typing_users_list.remove(username)
                self.root.after(0, lambda: self.update_typing_indicator(self.typing_users_list))
            return
        
        # 3. MESSAGE REACTION
        elif msg.startswith("[REACTION]"):
            try:
                data = msg[10:]
                parts = data.split(":", 2)
                if len(parts) == 3:
                    msg_id, emoji, username = parts
                    self.root.after(0, lambda: self.update_reaction_display(msg_id, emoji, username))
            except:
                pass
            return
        
        # 4. MESSAGE STATUS
        elif msg.startswith("[DELIVERED]"):
            msg_id = msg[11:]
            self.root.after(0, lambda: self.update_message_status(msg_id, 'delivered'))
            return
        
        elif msg.startswith("[READ]"):
            try:
                parts = msg[6:].split(":", 1)
                if len(parts) == 2:
                    msg_id, reader = parts
                    # Hanya update jika bukan diri sendiri yang read
                    if reader != self.username:
                        self.root.after(0, lambda: self.update_message_status(msg_id, 'read'))
            except:
                pass
            return
        
        # 5. SYSTEM INFO
        elif msg.startswith("[INFO]"):
            # Play notification sound untuk join/leave
            if not msg.startswith("[USERS]"):
                try:
                    winsound.MessageBeep(winsound.MB_OK)
                except:
                    pass
            
            if "bergabung" in msg:
                self.add_message(f"👋 {msg}", "system_join")
            elif "keluar" in msg:
                self.add_message(f"👋 {msg}", "system_leave")
            else:
                self.add_message(f"ℹ️ {msg}", "system_info")
            return
        
        # 6. ROOM PROTOCOLS
        elif msg.startswith("[ROOM_LIST]"):
            try:
                rooms = json.loads(msg[11:])
                self.root.after(0, lambda: self.update_room_list(rooms))
            except:
                pass
            return
            
        elif msg.startswith("[ROOM_CREATED]"):
            room_name = msg[14:]
            self.root.after(0, lambda: self.switch_room(room_name))
            return
            
        elif msg.startswith("[ROOM_JOINED]"):
            room_name = msg[13:]
            self.root.after(0, lambda: self.switch_room(room_name))
            return
            
        elif msg.startswith("[ROOM_ERROR]"):
            error_msg = msg[12:]
            self.root.after(0, lambda: messagebox.showerror("Room Error", error_msg))
            return
            
        # 7. FILE SHARING PROTOCOL
        elif msg.startswith("[FILE_SHARED]"):
            # Format: [FILE_SHARED]room:file_id:filename:sender:size:base64
            try:
                data = msg[13:]
                parts = data.split(':', 5)
                if len(parts) == 6:
                    room, file_id, filename, sender, size, b64_data = parts
                    # Hanya tampilkan jika di room yang aktif
                    if room == self.current_room:
                        self.root.after(0, lambda: self.display_file(room, file_id, filename, sender, size, b64_data))
            except:
                pass
            return
            
        # 8. REGULAR CHAT MESSAGE (Fallback if no prefix)
        else:
            # Play notification sound untuk messages dari orang lain
            if self.username and f"] {self.username}:" not in msg:
                try:
                    winsound.MessageBeep(winsound.MB_OK)
                except:
                    pass
            self.parse_chat_message(msg)
    
    def parse_chat_message(self, msg, room=None):
        """
        Parse dan display chat message dengan format baru
        Format: [MSG_ID:id][timestamp] username: message
        Args:
            msg: Formatted message dari server
            room: Room tujuan (jika None, pakai current_room)
        """
        target_room = room if room else self.current_room
        display = self.get_or_create_room_display(target_room)
        
        try:
            # Extract message ID jika ada
            msg_id = None
            if msg.startswith("[MSG_ID:"):
                end_id = msg.index("]", 1)
                msg_id = msg[8:end_id]
                msg = msg[end_id+1:]  # Remove MSG_ID part
            
            # Extract timestamp
            end = msg.index("]")
            time_str = msg[1:end]
            rest = msg[end+2:]
            
            # Extract username dan message
            if ": " in rest:
                idx = rest.index(": ")
                sender = rest[:idx]
                content = rest[idx+2:]
            else:
                sender = "Unknown"
                content = rest
            
            is_own = (sender == self.username)
            sender_color = get_user_color(sender)
            tag = "msg_own" if is_own else "msg_other"
            
            display.configure(state='normal')
            
            # Insert message
            insert_index = display.index(tk.END)
            display.insert(tk.END, f"\n")
            
            # Sender dengan colored name
            display.insert(tk.END, f"● ", tag)
            display.insert(tk.END, f"{sender}", tag)
            display.insert(tk.END, f"  {time_str}\n", "time")
            
            # Message content line
            msg_line_index = display.index(tk.END)
            display.insert(tk.END, f"   {content}")
            
            # Simpan position untuk message ID
            if msg_id:
                self.message_positions[msg_id] = msg_line_index
                
                # Jika message dari orang lain, kirim read receipt
                if not is_own:
                    # Delay sedikit untuk simulate reading
                    threading.Timer(0.5, lambda: self.send_read_receipt(msg_id)).start()
                else:
                    # Jika message sendiri, set status sent
                    self.message_status[msg_id] = {'status': 'sent'}
            
            display.insert(tk.END, "\n")
            
            display.configure(state='disabled')
            display.see(tk.END)
            
            # Refresh message status jika ada
            if msg_id and is_own:
                self.root.after(100, lambda: self.refresh_message_status(msg_id))
        except:
            # Fallback untuk message yang tidak sesuai format
            self.add_message(msg, "system_info", room=target_room)
    
    def add_message(self, text, tag="system_info", room=None):
        """
        Add system message ke chat display
        Args:
            text: Text message
            tag: Tag untuk styling
            room: Room tujuan (jika None, pakai current_room)
        """
        target_room = room if room else self.current_room
        display = self.get_or_create_room_display(target_room)
        
        display.configure(state='normal')
        display.insert(tk.END, f"\n{text}\n", tag)
        display.configure(state='disabled')
        display.see(tk.END)
    
    def send_message(self):
        """
        Kirim message ke server
        Generate unique message ID untuk tracking
        """
        msg = self.msg_entry.get().strip()
        if not msg or not self.client:
            return
        
        try:
            # Stop typing indicator saat send message
            if self.is_typing:
                self.stop_typing()
                if self.typing_timer:
                    self.typing_timer.cancel()
            
            # Kirim message (server akan generate MSG_ID)
            self.client.send((msg + "\n").encode())
            self.msg_entry.delete(0, tk.END)
        except:
            messagebox.showerror("Error", "Gagal mengirim pesan")

# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
