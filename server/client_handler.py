import threading
from datetime import datetime
import json
import uuid
import base64
import os

# Dictionary untuk menyimpan semua client yang terhubung
# Key: socket object, Value: username
clients = {}
clients_lock = threading.Lock()

# Dictionary untuk menyimpan reactions pada setiap pesan
# Key: message_id, Value: {emoji: [list of usernames]}
message_reactions = {}
reactions_lock = threading.Lock()

# Dictionary untuk tracking typing status
# Key: username, Value: True/False
typing_users = {}
typing_lock = threading.Lock()

# FITUR BARU: Discord-style Rooms
# Dictionary untuk menyimpan semua rooms
# Format: {room_name: {"users": [usernames], "messages": []}}
rooms = {"general": {"users": [], "messages": []}}
rooms_lock = threading.Lock()

# Track active room per user
# Format: {username: room_name}
user_active_room = {}
active_room_lock = threading.Lock()

def log_message(message, log_file):
    """
    Menyimpan pesan ke file log
    Args:
        message: Pesan yang akan disimpan
        log_file: Path ke file log
    """
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def broadcast(message, log_file, exclude_client=None):
    """
    Broadcast pesan ke semua client yang terhubung
    Args:
        message: Pesan yang akan di-broadcast
        log_file: Path ke file log
        exclude_client: Socket client yang tidak perlu menerima pesan (optional)
    """
    disconnected = []
    with clients_lock:
        for client in clients:
            # Skip client yang di-exclude (contoh: pengirim pesan)
            if client == exclude_client:
                continue
            try:
                client.send((message + "\n").encode())
            except:
                # Jika gagal kirim, tandai untuk dihapus
                disconnected.append(client)
        
        # Hapus client yang disconnect
        for client in disconnected:
            if client in clients:
                del clients[client]
    
    log_message(message, log_file)

def broadcast_to_room(room_name, message, log_file):
    """
    Broadcast pesan hanya ke users di room tertentu
    Args:
        room_name: Nama room
        message: Pesan yang akan di-broadcast
        log_file: Path ke file log
    """
    with clients_lock:
        with active_room_lock:
            for client_socket, username in clients.items():
                # Only send if user's active room matches
                if user_active_room.get(username) == room_name:
                    try:
                        client_socket.send((message + "\n").encode())
                    except:
                        pass
    log_message(f"[{room_name}] {message}", log_file)

def broadcast_user_list():
    """
    Kirim daftar user yang online ke semua client beserta room aktifnya
    Format: [USERS]{"user1": "general", "user2": "gaming"}
    """
    with clients_lock:
        with active_room_lock:
            # Buat mapping username -> active_room
            user_status = {}
            for username in clients.values():
                user_status[username] = user_active_room.get(username, "general")
            
            user_list_msg = f"[USERS]{json.dumps(user_status)}\n"
            for client in clients:
                try:
                    client.send(user_list_msg.encode())
                except:
                    pass

def broadcast_room_list():
    """
    Kirim daftar rooms yang tersedia ke semua client
    Format: [ROOM_LIST]["general", "gaming", "study"]
    """
    with rooms_lock:
        room_names = list(rooms.keys())
        room_list_msg = f"[ROOM_LIST]{json.dumps(room_names)}\n"
        with clients_lock:
            for client in clients:
                try:
                    client.send(room_list_msg.encode())
                except:
                    pass

def create_room(room_name, creator):
    """
    Buat room baru
    Args:
        room_name: Nama room yang akan dibuat
        creator: Username yang membuat room
    Returns:
        (success: bool, message: str)
    """
    with rooms_lock:
        if room_name in rooms:
            return False, "Room sudah ada"
        if not room_name or len(room_name) > 20:
            return False, "Nama room invalid"
        
        rooms[room_name] = {
            "users": [],
            "messages": [],
            "created_by": creator
        }
        return True, f"Room '{room_name}' berhasil dibuat"

def delete_room(room_name):
    """
    Hapus room dan pindahkan user di dalamnya ke general
    Args:
        room_name: Nama room yang akan dihapus
    Returns:
        (success: bool, message: str)
    """
    if room_name == "general":
        return False, "Room 'general' tidak bisa dihapus"
        
    with rooms_lock:
        if room_name not in rooms:
            return False, "Room tidak ditemukan"
            
        # Pindahkan user yang ada di room ini (di state user_active_room)
        with active_room_lock:
            for user, active_room in user_active_room.items():
                if active_room == room_name:
                    user_active_room[user] = "general"
        
        del rooms[room_name]
        return True, f"Room '{room_name}' berhasil dihapus"

def join_room(room_name, username):
    """
    Join user ke room
    Args:
        room_name: Nama room
        username: Username yang join
    Returns:
        (success: bool, message: str)
    """
    with rooms_lock:
        if room_name not in rooms:
            return False, "Room tidak ditemukan"
        
        if username not in rooms[room_name]["users"]:
            rooms[room_name]["users"].append(username)
        
        return True, f"Berhasil join room '{room_name}'"

def handle_file_upload(message, username, log_file):
    """
    Handle file upload dari client
    Format: [FILE]room:filename:size:base64_data
    Args:
        message: Message dengan format file upload
        username: Username yang upload
        log_file: Path ke file log
    """
    try:
        # Parse message
        data = message[6:]  # Remove [FILE] prefix
        parts = data.split(':', 3)
        if len(parts) != 4:
            return
        
        room_name, filename, filesize, b64_data = parts
        
        # Create uploads directory if not exists
        uploads_dir = os.path.join(os.path.dirname(log_file), "../uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        filepath = os.path.join(uploads_dir, f"{file_id}_{filename}")
        
        # Decode and save file
        file_data = base64.b64decode(b64_data)
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        # Broadcast to room
        file_msg = f"[FILE_SHARED]{room_name}:{file_id}:{filename}:{username}:{filesize}:{b64_data}"
        
        # FITUR BARU: Simpan ke history room
        with rooms_lock:
            if room_name in rooms:
                rooms[room_name]["messages"].append(file_msg)
                # Limit history to 50 items
                if len(rooms[room_name]["messages"]) > 50:
                    rooms[room_name]["messages"].pop(0)
                    
        broadcast_to_room(room_name, file_msg, log_file)
        
        print(f"[FILE] {username} uploaded {filename} ({filesize} bytes) to {room_name}")
    except Exception as e:
        print(f"[ERROR] File upload failed: {e}")

def broadcast_typing_status(username, is_typing):
    """
    Broadcast status typing ke semua client
    Args:
        username: Nama user yang sedang/berhenti mengetik
        is_typing: True jika mulai mengetik, False jika berhenti
    """
    with typing_lock:
        typing_users[username] = is_typing
    
    # Format pesan typing indicator
    if is_typing:
        msg = f"[TYPING]{username}\n"
    else:
        msg = f"[STOP_TYPING]{username}\n"
    
    # Kirim ke semua client
    with clients_lock:
        for client in clients:
            try:
                client.send(msg.encode())
            except:
                pass

def broadcast_reaction(message_id, emoji, username, log_file):
    """
    Broadcast reaction baru ke semua client
    Args:
        message_id: ID pesan yang di-reaction
        emoji: Emoji yang ditambahkan
        username: User yang menambahkan reaction
        log_file: Path ke file log
    """
    with reactions_lock:
        # Initialize message reactions jika belum ada
        if message_id not in message_reactions:
            message_reactions[message_id] = {}
        
        # Initialize emoji list jika belum ada
        if emoji not in message_reactions[message_id]:
            message_reactions[message_id][emoji] = []
        
        # Toggle reaction: jika sudah ada, hapus; jika belum ada, tambahkan
        if username in message_reactions[message_id][emoji]:
            message_reactions[message_id][emoji].remove(username)
            # Hapus emoji jika tidak ada yang react lagi
            if not message_reactions[message_id][emoji]:
                del message_reactions[message_id][emoji]
        else:
            message_reactions[message_id][emoji].append(username)
    
    # Broadcast reaction update ke semua client
    # Format: [REACTION]message_id:emoji:username
    msg = f"[REACTION]{message_id}:{emoji}:{username}\n"
    with clients_lock:
        for client in clients:
            try:
                client.send(msg.encode())
            except:
                pass
    
    log_message(msg.strip(), log_file)

def broadcast_read_status(message_id, username, log_file):
    """
    Broadcast read receipt ke semua client
    Args:
        message_id: ID pesan yang sudah dibaca
        username: User yang membaca pesan
        log_file: Path ke file log
    """
    # Format: [READ]message_id:username
    msg = f"[READ]{message_id}:{username}\n"
    with clients_lock:
        for client in clients:
            try:
                client.send(msg.encode())
            except:
                pass
    
    log_message(msg.strip(), log_file)

def send_room_history(client_socket, room_name):
    """
    Kirim history pesan di suatu room ke client tertentu
    Args:
        client_socket: Socket client
        room_name: Nama room
    """
    with rooms_lock:
        if room_name in rooms:
            history = rooms[room_name]["messages"]
            for msg in history:
                try:
                    # Kirim history satu per satu
                    client_socket.send((msg + "\n").encode())
                except:
                    break

def handle_client(client_socket, address, log_file):
    """
    Handle komunikasi dengan satu client
    Args:
        client_socket: Socket connection ke client
        address: IP address dan port client
        log_file: Path ke file log
    """
    username = None
    try:
        # Terima username dari client (dengan buffering singkat)
        buffer = ""
        while "\n" not in buffer:
            data = client_socket.recv(1024).decode()
            if not data: break
            buffer += data
        
        if "\n" in buffer:
            username, buffer = buffer.split("\n", 1)
        else:
            username = buffer
            buffer = ""
            
        username = username.strip()
        with clients_lock:
            clients[client_socket] = username

        # Broadcast pesan join
        join_msg = f"[INFO] {username} bergabung dari {address}"
        broadcast(join_msg, log_file)
        
        # FITUR BARU: Discord-style Rooms initialization
        # Auto-join ke room 'general' saat login
        with active_room_lock:
            user_active_room[username] = "general"
        
        join_room("general", username)
        
        # Kirim info daftar user dan daftar rooms ke client
        broadcast_user_list()
        broadcast_room_list()
        
        # Kirim konfirmasi join room ke client
        client_socket.send("[ROOM_JOINED]general\n".encode())

        # Loop untuk menerima pesan dari client
        buffer = ""
        while True:
            try:
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    message = message.strip()
                    if not message:
                        continue

                    # DEBUG LOGGING (Opsional: simpan ke file log)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] RECV from {username}: {message}\n")

                    # Handle berbagai jenis pesan berdasarkan prefix dengan lebih robust
                    
                    # 1. TYPING INDICATOR
                    if message.startswith("[TYPING]"):
                        broadcast_typing_status(username, True)
                        continue
                    
                    elif message.startswith("[STOP_TYPING]"):
                        broadcast_typing_status(username, False)
                        continue
                    
                    # 2. MESSAGE REACTION
                    elif message.startswith("[REACTION]"):
                        try:
                            data = message[10:]
                            msg_id, emoji = data.split(":", 1)
                            broadcast_reaction(msg_id, emoji, username, log_file)
                        except:
                            pass
                        continue
                    
                    # 3. READ RECEIPT
                    elif message.startswith("[READ]"):
                        try:
                            msg_id = message[6:]
                            broadcast_read_status(msg_id, username, log_file)
                        except:
                            pass
                        continue
                    
                    # 4. CREATE ROOM
                    elif message.startswith("[CREATE_ROOM]"):
                        room_name = message[13:].strip()
                        success, m = create_room(room_name, username)
                        if success:
                            broadcast_room_list()
                            join_room(room_name, username)
                            with active_room_lock:
                                user_active_room[username] = room_name
                            client_socket.send(f"[ROOM_CREATED]{room_name}\n".encode())
                            broadcast_user_list()
                        else:
                            client_socket.send(f"[ROOM_ERROR]{m}\n".encode())
                        continue

                    # 5. JOIN ROOM
                    elif message.startswith("[JOIN_ROOM]"):
                        room_name = message[11:].strip()
                        success, m = join_room(room_name, username)
                        if success:
                            with active_room_lock:
                                user_active_room[username] = room_name
                            client_socket.send(f"[ROOM_JOINED]{room_name}\n".encode())
                            broadcast_user_list()
                        else:
                            client_socket.send(f"[ROOM_ERROR]{m}\n".encode())
                        continue

                    # 5.5 DELETE ROOM
                    elif message.startswith("[DELETE_ROOM]"):
                        room_name = message[13:].strip()
                        success, m = delete_room(room_name)
                        if success:
                            broadcast_room_list()
                            broadcast_user_list() 
                            broadcast(f"[INFO] Room '{room_name}' telah dihapus", log_file)
                        else:
                            client_socket.send(f"[ROOM_ERROR]{m}\n".encode())
                        continue

                    # 6. SWITCH ROOM
                    elif message.startswith("[SWITCH_ROOM]"):
                        room_name = message[13:].strip()
                        with active_room_lock:
                            user_active_room[username] = room_name
                        broadcast_user_list()
                        continue

                    # 6.5 GET ROOM HISTORY
                    elif message.startswith("[GET_HISTORY]"):
                        room_name = message[13:].strip()
                        send_room_history(client_socket, room_name)
                        continue

                    # 7. FILE SHARING
                    elif message.startswith("[FILE]"):
                        handle_file_upload(message, username, log_file)
                        continue
                    
                    # 8. REGULAR CHAT MESSAGE (Hanya jika tidak ada prefix [XXX])
                    elif not message.startswith("["):
                        with active_room_lock:
                            current_room = user_active_room.get(username, "general")
                        
                        msg_id = str(uuid.uuid4())
                        time_msg = datetime.now().strftime("%H:%M:%S")
                        full_msg = f"[MSG_ID:{msg_id}][{time_msg}] {username}: {message}"
                        
                        with rooms_lock:
                            if current_room in rooms:
                                rooms[current_room]["messages"].append(full_msg)
                                if len(rooms[current_room]["messages"]) > 50:
                                    rooms[current_room]["messages"].pop(0)
                                    
                        broadcast_to_room(current_room, full_msg, log_file)
                        
                        try:
                            client_socket.send(f"[DELIVERED]{msg_id}\n".encode())
                        except:
                            pass
                    else:
                        # Ini kemungkinan command yang typo atau corrupt, log saja
                        with open(log_file, "a") as f:
                            f.write(f"[WARN] Unknown protocol format: {message}\n")
            except Exception as e:
                print(f"[ERROR] {e}")
                break

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        # Cleanup saat client disconnect
        if username:
            leave_msg = f"[INFO] {username} keluar"
            broadcast(leave_msg, log_file)
            
            # Reset typing status
            with typing_lock:
                if username in typing_users:
                    del typing_users[username]
            broadcast_typing_status(username, False)
        
        with clients_lock:
            if client_socket in clients:
                del clients[client_socket]
        client_socket.close()
        broadcast_user_list()
