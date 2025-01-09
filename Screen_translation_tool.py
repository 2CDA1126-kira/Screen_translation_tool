import os
import pytesseract
from googletrans import Translator
from PIL import ImageGrab, Image
import tkinter as tk
from tkinter import font, Frame, Label, ttk, messagebox
import glob

tesseract_path = "C:\\Program Files\\Tesseract-OCR"
if tesseract_path not in os.environ["PATH"].split(os.pathsep):
    os.environ["PATH"] += os.pathsep + tesseract_path

pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_path, 'tesseract.exe')

memo_folder = "Screen_translation_tool_memo"
os.makedirs(memo_folder, exist_ok=True)  

def capture_screen_area():
    root.withdraw()  
    capture_root = tk.Toplevel()
    capture_root.attributes('-fullscreen', True)
    capture_root.attributes('-alpha', 0.3)
    capture_root.configure(bg='gray')

    canvas = tk.Canvas(capture_root, cursor="cross", bg="gray")
    canvas.pack(fill=tk.BOTH, expand=True)

    rect_id = None

    def on_mouse_down(event):
        nonlocal rect_id
        global start_x, start_y
        start_x, start_y = event.x, event.y
        rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)

    def on_mouse_drag(event):
        nonlocal rect_id
        canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        global end_x, end_y
        end_x, end_y = event.x, event.y
        capture_root.quit()

    canvas.bind('<ButtonPress-1>', on_mouse_down)
    canvas.bind('<B1-Motion>', on_mouse_drag)
    canvas.bind('<ButtonRelease-1>', on_mouse_up)

    capture_root.mainloop()
    capture_root.destroy()
    root.deiconify()  
    return (start_x, start_y, end_x, end_y)

def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng') 
    return text

def translate_text(text):
    cleaned_text = text.replace('\n', ' ').replace('\r', '').strip() 
    translator = Translator()
    translated = translator.translate(cleaned_text, src='en', dest='ja')  
    return translated.text

def start_translation():
    region = capture_screen_area()
    bbox = (region[0], region[1], region[2], region[3])
    screenshot = ImageGrab.grab(bbox=bbox)
    screenshot.save('screenshot.png')
    extracted_text = extract_text('screenshot.png')
    translated_text = translate_text(extracted_text)
    original_text_box.delete(1.0, tk.END)
    translated_text_box.delete(1.0, tk.END)
    original_text_box.insert(tk.END, extracted_text)
    translated_text_box.insert(tk.END, translated_text)

def manual_translate():
    manual_text = original_text_box.get(1.0, tk.END).strip()
    translated_text = translate_text(manual_text)
    translated_text_box.delete(1.0, tk.END)
    translated_text_box.insert(tk.END, translated_text)

def save_note():
    title = title_entry.get()
    if title in notes:
        messagebox.showwarning("エラー", "そのタイトルはすでに存在します")
    else:
        content = translated_text_box.get(1.0, tk.END)
        notes[title] = content
        update_note_list()
        save_to_file(title, content)

def delete_note(): 
    try: 
        selected_title = note_list.get(note_list.curselection()) 
        del notes[selected_title] 
        os.remove(os.path.join(memo_folder, f"{selected_title}.txt"))  
        update_note_list() 
        note_content_box.delete(1.0, tk.END) 
    except tk.TclError: 
        messagebox.showwarning("エラー", "削除するメモを選択してください")

def update_note_list():
    note_list.delete(0, tk.END)
    for title in notes.keys():
        note_list.insert(tk.END, title)

def display_note_content(event):
    selected_title = note_list.get(note_list.curselection())
    note_content = notes[selected_title]
    note_content_box.delete(1.0, tk.END)
    note_content_box.insert(tk.END, note_content)

def save_to_file(title, content):
    file_path = os.path.join(memo_folder, f"{title}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def load_notes():
    for file_path in glob.glob(os.path.join(memo_folder, "*.txt")):
        title = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            notes[title] = content
    update_note_list()

notes = {}

root = tk.Tk()
root.title("スクリーン翻訳ツール")

custom_font = font.Font(root, family="Helvetica", size=12)

tab_control = ttk.Notebook(root)
tab1 = ttk.Frame(tab_control)
tab2 = ttk.Frame(tab_control)
tab_control.add(tab1, text='翻訳')
tab_control.add(tab2, text='メモ')
tab_control.pack(expand=1, fill='both')

frame = Frame(tab1)
frame.pack()

original_label = Label(frame, text="原文")
original_label.grid(row=0, column=0)
translated_label = Label(frame, text="翻訳")
translated_label.grid(row=0, column=1)

original_text_box = tk.Text(frame, wrap='word', height=20, width=50, font=custom_font)
original_text_box.grid(row=1, column=0)

translated_text_box = tk.Text(frame, wrap='word', height=20, width=50, font=custom_font)
translated_text_box.grid(row=1, column=1)

translate_button = tk.Button(tab1, text="翻訳する文を選択", command=start_translation)
translate_button.pack()

manual_translate_button = tk.Button(tab1, text="手動翻訳", command=manual_translate)
manual_translate_button.pack()

title_label = Label(tab1, text="タイトル")
title_label.pack()
title_entry = tk.Entry(tab1)
title_entry.pack()

save_button = tk.Button(tab1, text="メモを保存", command=save_note)
save_button.pack()

note_list = tk.Listbox(tab2)
note_list.pack()
note_list.bind('<<ListboxSelect>>', display_note_content)

delete_button = tk.Button(tab2, text="メモを削除", command=delete_note)
delete_button.pack()

note_content_box = tk.Text(tab2, wrap='word', height=20, width=50, font=custom_font)
note_content_box.pack()

load_notes()  

root.mainloop()
