import os
import json
import hashlib
import random
import string
import smtplib
from email.message import EmailMessage
import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Listbox, Button
import winreg
import webbrowser
from PIL import Image, ImageTk
# Webcam and logging imports
import cv2
import time
from datetime import datetime
import logging

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURATION ---
USERS_FILE = "users.json"
ADMIN_EMAIL = "vijaychinthapatla1@gmail.com"
ADMIN_PASSWORD = "admin123"
SMTP_EMAIL = "vijaychinthapatla1@gmail.com"          # Admin email
SMTP_PASSWORD = "gwet aabs qcnx selv"          # App-specific password
PROJECT_INFO_HTML =resource_path("info.html")
USB_IMAGE =resource_path("usb_icons.jpg")

# --- LOGGER SETUP ---
logger = logging.getLogger("usb_security")
logger.setLevel(logging.WARNING)
fh = logging.FileHandler("intruder.log")
fh.setLevel(logging.WARNING)
logger.addHandler(fh)

# --- APP LOGGING SETUP ---
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.INFO)
app_fh = logging.FileHandler("app.log")
app_fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
app_fh.setFormatter(formatter)
app_logger.addHandler(app_fh)

# --- HELPER FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def send_password_email(receiver_email, password):
    msg = EmailMessage()
    msg['Subject'] = "Your USB Security App Password"
    msg['From'] = SMTP_EMAIL
    msg['To'] = receiver_email
    msg.set_content(f"Your registration was successful.\nYour login password is: {password}\nPlease wait for admin approval before logging in.")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        smtp.send_message(msg)

def register_user(email):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

    with open(USERS_FILE, 'r') as f:
        users = json.load(f)

    if email in users:
        return "User already registered."

    password = generate_random_password()
    hashed_pw = hash_password(password)

    users[email] = {
        "password": hashed_pw,
        "approved": False
    }

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

    send_password_email(email, password)
    return "Registration successful. Password sent via email."
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except json.JSONDecodeError:
        users = {}
    admin_hashed = hash_password(ADMIN_PASSWORD)
    if ADMIN_EMAIL not in users or not isinstance(users[ADMIN_EMAIL], dict) or users[ADMIN_EMAIL].get('password') != admin_hashed:
        users[ADMIN_EMAIL] = {"password": admin_hashed, "approved": True}
        save_users(users)
    return users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def toggle_usb(enable=True):
    value = 3 if enable else 4
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Services\\USBSTOR", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)

def get_usb_status():
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Services\\USBSTOR")
    value, _ = winreg.QueryValueEx(key, "Start")
    return "Enabled" if value == 3 else "Disabled"

def send_email(recipient, password):
    msg = EmailMessage()
    msg['Subject'] = 'Your USB Security App Password'
    msg['From'] = SMTP_EMAIL
    msg['To'] = recipient
    msg.set_content(f"Your system-generated password is:\n\n{password}\n\nWait for admin approval.")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Email sending failed: {e}")



def generate_password(length=10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def project_info():
    if not os.path.exists(PROJECT_INFO_HTML):
        with open(PROJECT_INFO_HTML, 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Project Info</title></head>
<body><h2>USB Physical Security System</h2>
<p>This application controls USB access, user registration, admin login, and email alerts.</p>
</body></html>""")
    webbrowser.open(PROJECT_INFO_HTML)

# --- Webcam recording function ---
def capture_intruder_video(duration=5):
    try:
        # Ensure the 'intrusions' directory exists
        intrusion_dir = 'intrusions'
        if not os.path.exists(intrusion_dir):
            os.makedirs(intrusion_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(intrusion_dir, f"intruder_{timestamp}.avi")
        logger.warning(f"Intruder alert! Recording video: {filename}")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Failed to access webcam for intruder recording")
            return

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

        start_time = time.time()
        while int(time.time() - start_time) < duration:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break

        cap.release()
        out.release()
        logger.info(f"Intruder video recorded: {filename}")
        messagebox.showwarning("Intruder Detected", f"Security alert triggered!\nVideo recorded as {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error recording intruder video: {str(e)}")
        return None

# --- MAIN APP CLASS ---
class USBApp:
    def show_user_logs(self):
        app_logger.info(f"{getattr(self, 'current_user', 'Unknown')} viewed user logs.")
        log_file = "app.log"
        if not os.path.exists(log_file):
            messagebox.showinfo("User Logs", "No logs found.")
            return
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read logs: {e}")
            return
        # Show logs in a scrollable popup
        log_win = Toplevel(self.root)
        log_win.title("User Logs")
        log_win.geometry("1000x700")
        text = tk.Text(log_win, wrap="word", bg="black", fg="white")
        text.insert("1.0", logs)
        text.config(state="disabled")
        text.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(log_win, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    def __init__(self, root):  # constructor fixed
        self.root = root
        self.root.title("USB Physical Security")
        self.root.geometry("600x500")
        self.root.configure(bg="black")
        self.users = load_users()
        self.show_login()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_window()
        # Cyber crime themed background: very dark with a hint of red and green (hacker style, minimal)
        self.root.configure(bg="#0a0f0d")  # fallback
        if hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists():
            self.bg_canvas.destroy()
        self.bg_canvas = tk.Canvas(self.root, width=600, height=500, highlightthickness=0, bd=0, bg="#0a0f0d")
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Subtle grid in dark green
        for x in range(0, 600, 40):
            self.bg_canvas.create_line(x, 0, x, 500, fill="#133a13", width=1)
        for y in range(0, 500, 40):
            self.bg_canvas.create_line(0, y, 600, y, fill="#133a13", width=1)
        # Minimal red accent line (cyber crime vibe)
        self.bg_canvas.create_line(0, 498, 600, 498, fill="#ff003c", width=2)

        # Animated glowing title
        title = tk.Label(self.root, text="USB Physical Security", font=("Orbitron", 28, "bold"), fg="#00f2fe", bg="#0f2027")
        title.pack(pady=(36, 18))
        def animate_title():
            from random import randint
            glow = f"#{randint(0,255):02x}{randint(200,255):02x}{randint(240,255):02x}"
            title.config(fg=glow)
            self.root.after(350, animate_title)
        animate_title()

        # Glassmorphism login panel
        panel = tk.Frame(self.root, bg="#232b3a", bd=0, highlightthickness=0)
        panel.pack(pady=10, padx=30, ipadx=10, ipady=10)
        panel.configure(bg="#232b3a", highlightbackground="#00f2fe", highlightcolor="#00f2fe", highlightthickness=2)

        tk.Label(panel, text="Email:", fg="#e0e8ff", bg="#232b3a", font=("Montserrat", 13, "bold")).grid(row=0, column=0, sticky="e", pady=10, padx=10)
        self.email_entry = tk.Entry(panel, width=28, font=("Montserrat", 12), bg="#181f2a", fg="#00f2fe", insertbackground="#00f2fe", relief="flat", highlightthickness=2, highlightcolor="#38f9d7")
        self.email_entry.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(panel, text="Password:", fg="#e0e8ff", bg="#232b3a", font=("Montserrat", 13, "bold")).grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.password_entry = tk.Entry(panel, show="*", width=28, font=("Montserrat", 12), bg="#181f2a", fg="#00f2fe", insertbackground="#00f2fe", relief="flat", highlightthickness=2, highlightcolor="#38f9d7")
        self.password_entry.grid(row=1, column=1, pady=10, padx=10)

        # Custom button with hover effect
        def style_btn(btn, color, fg, hover_bg, hover_fg):
            btn.configure(bg=color, fg=fg, activebackground=hover_bg, activeforeground=hover_fg, font=("Montserrat", 13, "bold"), bd=0, relief="flat", cursor="hand2")
            def on_enter(e): btn.config(bg=hover_bg, fg=hover_fg)
            def on_leave(e): btn.config(bg=color, fg=fg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        login_btn = tk.Button(self.root, text="Login", command=self.login)
        style_btn(login_btn, "#00f2fe", "#232526", "#38f9d7", "#232526")
        login_btn.pack(pady=(22, 8), ipadx=22, ipady=7)

        reg_btn = tk.Button(self.root, text="Register", command=self.register)
        style_btn(reg_btn, "#38f9d7", "#232526", "#00f2fe", "#232526")
        reg_btn.pack(ipadx=22, ipady=7)

    def show_dashboard(self):
        self.clear_window()
        self.root.geometry("900x700")
        self.root.configure(bg="#0a0f0d")  # fallback
        if hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists():
            self.bg_canvas.destroy()
        self.bg_canvas = tk.Canvas(self.root, width=900, height=700, highlightthickness=0, bd=0, bg="#0a0f0d")
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Subtle grid in dark green
        for x in range(0, 900, 50):
            self.bg_canvas.create_line(x, 0, x, 700, fill="#133a13", width=1)
        for y in range(0, 700, 50):
            self.bg_canvas.create_line(0, y, 900, y, fill="#133a13", width=1)
        # Minimal red accent line (cyber crime vibe)
        self.bg_canvas.create_line(0, 698, 900, 698, fill="#ff003c", width=2)

        # Animated glowing title
        title = tk.Label(self.root, text="USB Physical Security App", font=("Orbitron", 26, "bold"), fg="#00f2fe", bg="#0f2027")
        title.pack(pady=(28, 12))
        def animate_title():
            from random import randint
            glow = f"#{randint(0,255):02x}{randint(200,255):02x}{randint(240,255):02x}"
            title.config(fg=glow)
            self.root.after(350, animate_title)
        animate_title()

        # Glassmorphism dashboard panel
        panel = tk.Frame(self.root, bg="#232b3a", bd=0, highlightthickness=0)
        panel.pack(pady=10, padx=30, ipadx=10, ipady=10)
        panel.configure(bg="#232b3a", highlightbackground="#00f2fe", highlightcolor="#00f2fe", highlightthickness=2)

        btns = [
            ("Project Info", "#ff3c6f", "#fff", project_info),
            ("Enable USB", "#1dbe0e", "#232526", lambda: self.toggle_usb(True)),
            ("Disable USB", "#9F0D0D", "#00f2fe", lambda: self.toggle_usb(False)),
            ("USB Status", "#a7bf09", "#232526", self.show_usb_status),
            ("User Logs", "#674ba2", "#fff", self.show_user_logs),
            ("User Approval", "#094284", "#232526", self.user_approval_panel),
            ("Logout", "#bb3cff", "#fff", self.show_login)
        ]
        def style_btn(btn, color, fg, hover_bg, hover_fg):
            btn.configure(bg=color, fg=fg, activebackground=hover_bg, activeforeground=hover_fg, font=("Montserrat", 13, "bold"), bd=0, relief="flat", cursor="hand2")
            def on_enter(e): btn.config(bg=hover_bg, fg=hover_fg)
            def on_leave(e): btn.config(bg=color, fg=fg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        for idx, (text, color, fg, cmd) in enumerate(btns):
            btn = tk.Button(panel, text=text, command=cmd)
            style_btn(btn, color, fg, "#38f9d7", "#232526")
            btn.pack(pady=5, ipadx=12, ipady=6, fill="x")
            # Show the image only below the Project Info button
            if text == "Project Info":
                img_path = r"C:\\Users\\vijay\\OneDrive\\文档\\1.png.jpg"
                if os.path.exists(img_path):
                    try:
                        custom_img = Image.open(img_path)
                        custom_img = custom_img.resize((300, 200))
                        self.custom_tk_img = ImageTk.PhotoImage(custom_img)
                        img_label = tk.Label(panel, image=self.custom_tk_img, bg="#232b3a")
                        img_label.pack(pady=10)
                    except Exception as e:
                        print(f"Error loading dashboard image: {e}")

    def login(self):
        email = self.email_entry.get().strip()
        pwd = self.password_entry.get().strip()
        hashed = hash_password(pwd)

        if email in self.users and self.users[email]['password'] == hashed:
            if not self.users[email].get('approved', False):
                messagebox.showwarning("Approval Pending", "Wait for admin approval.")
            else:
                self.current_user = email
                self.show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid password.")
            # Record video on wrong password
            capture_intruder_video(duration=5)

    def register(self):
        def submit_registration():
            email = email_entry.get().strip()
            if not email:
                messagebox.showerror("Error", "Email cannot be empty.")
                return
            if email in self.users:
                messagebox.showerror("Error", "User already exists.")
                return

            password = generate_random_password()
            self.users[email] = {"password": hash_password(password), "approved": False}
            save_users(self.users)

            try:
                send_password_email(email, password)
                messagebox.showinfo("Registered", "Password sent to your email. Await admin approval.")
                reg_window.destroy()
            except Exception as e:
                messagebox.showerror("Email Error", f"Failed to send password email: {e}")

        # Open new registration window
        reg_window = Toplevel(self.root)
        reg_window.title("User Registration")
        reg_window.geometry("350x200")
        reg_window.configure(bg="black")

        tk.Label(reg_window, text="Register New User", font=("Helvetica", 14), fg="white", bg="black").pack(pady=10)
        tk.Label(reg_window, text="Email:", fg="white", bg="black").pack()
        email_entry = tk.Entry(reg_window, width=30)
        email_entry.pack(pady=5)

        tk.Button(reg_window, text="Submit", bg="green", fg="white", command=submit_registration).pack(pady=10)


    def toggle_usb(self, enable):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\\CurrentControlSet\\Services\\USBSTOR",
                0,
                winreg.KEY_SET_VALUE
            )
            value = 3 if enable else 4  # 3 = enabled, 4 = disabled
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)

            state = "enabled" if enable else "disabled"
            messagebox.showinfo("Success", f"USB ports {state}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle USB ports: {e}")

    def show_usb_status(self):
        status = get_usb_status()
        messagebox.showinfo("USB Status", f"Current USB status: {status}")
    # Inside your USBApp class

    def user_approval_panel(self):
        if getattr(self, "current_user", "") != ADMIN_EMAIL:
            messagebox.showerror("Access Denied", "Only admin can access this panel.")
            return

        top = Toplevel(self.root)
        top.title("User Approval")
        # Increase the user approval window size
        top.geometry("700x600")
        lb = Listbox(top)
        lb.pack(fill="both", expand=True, padx=10, pady=5)

        def approve_selected():
            selected = lb.curselection()
            if not selected:
                return
            email = lb.get(selected[0]).split(" - ")[0]
            self.users[email]['approved'] = True
            save_users(self.users)
            messagebox.showinfo("User Approved", f"{email} is now approved.")
            top.destroy()

        def reject_selected():
            selected = lb.curselection()
            if not selected:
                return
            email = lb.get(selected[0]).split(" - ")[0]
            confirm = messagebox.askyesno("Confirm Rejection", f"Are you sure you want to reject (delete) {email}?")
            if confirm:
                del self.users[email]
                save_users(self.users)
                messagebox.showinfo("User Rejected", f"{email} has been removed.")
                top.destroy()

        for email, data in self.users.items():
            if email != ADMIN_EMAIL:
                status = "Approved" if data.get("approved") else "Pending"
                lb.insert(tk.END, f"{email} - {status}")
        Button(top, text="Approve Selected", command=approve_selected, bg="green", fg="white", width=20, height=1).pack(pady=10)
        Button(top, text="Reject Selected", command=reject_selected, bg="red", fg="white", width=20, height=1).pack(pady=5)

        def approve_selected():
            selected = lb.curselection()
            if not selected:
                return
            email = lb.get(selected[0]).split(" - ")[0]
            self.users[email]['approved'] = True
            save_users(self.users)
            messagebox.showinfo("User Approved", f"{email} is now approved.")
            top.destroy()

        for email, data in self.users.items():
            if email != ADMIN_EMAIL:
                status = "Approved" if data.get("approved") else "Pending"
                lb.insert(tk.END, f"{email} - {status}")

        

if __name__ == "__main__":
    # simple check for google libs
    root = tk.Tk()
    app = USBApp(root)
    root.mainloop()