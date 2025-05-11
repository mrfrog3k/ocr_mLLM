import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import datetime
import base64
from openpyxl import Workbook

# OCR API call
def perform_ocr(image_url=None, image_base64=None):
    payload = {}
    if image_url:
        payload["image_url"] = image_url
    elif image_base64:
        payload["image_base64"] = image_base64
    else:
        return "Không có ảnh để gửi."

    try:
        response = requests.post(
            "https://0a25-34-16-163-174.ngrok-free.app/ocr",
            json=payload
        )
        if response.status_code == 200:
            return response.json().get("response_message")
        else:
            return f"Lỗi {response.status_code}: {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

# Mã hóa ảnh sang base64
def encode_image_base64(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Phân tích dữ liệu dạng bảng
def parse_ocr_table(text):
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    headers = []
    data_rows = []

    for line in lines:
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not headers:
                headers = cells
            else:
                while len(cells) < len(headers):
                    cells.append("")
                while len(cells) > len(headers):
                    headers.append(f"Cột {len(headers)+1}")
                data_rows.append(cells)

    return headers, data_rows

# Gửi URL
def on_submit():
    image_url = url_entry.get().strip()
    if not image_url:
        messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đường dẫn ảnh.")
        return

    result = perform_ocr(image_url=image_url)
    handle_result(result)

# Chọn ảnh từ thiết bị
def on_select_file():
    file_path = filedialog.askopenfilename(
        title="Chọn ảnh hóa đơn",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
    )
    if not file_path:
        return

    image_base64 = encode_image_base64(file_path)
    result = perform_ocr(image_base64=image_base64)
    handle_result(result)

# Hiển thị dữ liệu trả về
def handle_result(result):
    if not result or "|" not in result:
        messagebox.showerror("Lỗi", "Không kết nối được với Server.")
        return

    headers, rows = parse_ocr_table(result)

    if not headers or not rows:
        messagebox.showinfo("Không có dữ liệu", "Không tìm thấy bảng hợp lệ.")
        return

    create_tree(headers)
    for row in rows:
        tree.insert("", tk.END, values=row)

    global current_headers
    current_headers = headers

# Tạo bảng Treeview
def create_tree(headers):
    global tree, tree_frame
    if tree:
        tree.destroy()

    tree = ttk.Treeview(tree_frame, columns=headers, show="headings")

    for col in headers:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor=tk.CENTER)

    tree.pack(fill=tk.BOTH, expand=True)
    tree.bind("<Double-1>", on_double_click)

# Sửa dữ liệu trong bảng
def on_double_click(event):
    global edit_entry

    if edit_entry:
        edit_entry.destroy()
        edit_entry = None

    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return

    row_id = tree.identify_row(event.y)
    column_id = tree.identify_column(event.x)
    if not row_id or not column_id:
        return

    x, y, width, height = tree.bbox(row_id, column_id)
    column_index = int(column_id[1:]) - 1
    current_value = tree.item(row_id)["values"][column_index]

    edit_entry = tk.Entry(tree)
    edit_entry.place(x=x, y=y, width=width, height=height)
    edit_entry.insert(0, current_value)
    edit_entry.focus()

    def save_edit(event):
        new_value = edit_entry.get()
        values = list(tree.item(row_id)["values"])
        values[column_index] = new_value
        tree.item(row_id, values=values)
        edit_entry.destroy()

    edit_entry.bind("<Return>", save_edit)
    edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

# Xuất ra Excel
def export_to_excel():
    if not current_headers or not tree.get_children():
        messagebox.showwarning("Không có dữ liệu", "Không có bảng nào để xuất.")
        return

    folder = "data_result"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(folder, f"{timestamp}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "OCR Result"

    ws.append(current_headers)
    for row_id in tree.get_children():
        row = tree.item(row_id)["values"]
        ws.append(row)

    wb.save(filename)
    messagebox.showinfo("Xuất thành công", f"Đã lưu file: {filename}")

# Giao diện chính
root = tk.Tk()
root.title("OCR từ ảnh hóa đơn")
root.geometry("950x650")

tk.Label(root, text="Nhập đường dẫn ảnh hóa đơn:").pack(pady=5)
url_entry = tk.Entry(root, width=100)
url_entry.pack()

submit_button = tk.Button(root, text="Gửi yêu cầu OCR (từ URL)", command=on_submit)
submit_button.pack(pady=5)

select_button = tk.Button(root, text="Chọn ảnh từ thiết bị", command=on_select_file)
select_button.pack(pady=5)

export_button = tk.Button(root, text="Xuất Excel", command=export_to_excel)
export_button.pack(pady=10)

tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tree = None
edit_entry = None
current_headers = []

root.mainloop()
