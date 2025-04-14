import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import requests
from openpyxl import Workbook
import datetime
import os

def perform_ocr(image_path):
    response = requests.post(
        "https://19cc-34-124-151-28.ngrok-free.app/ocr",  # Thay thế API 
        json={"image_url": image_path},
    )
    if response.status_code == 200:
        return response.json().get("response_message")
    else:
        return f"Lỗi: {response.status_code}, {response.text}"

def process_image():
    image_url = url_entry.get()
    ocr_result = perform_ocr(image_url)
    result_text.delete(1.0, tk.END)  # Xóa nội dung cũ
    result_text.insert(tk.END, ocr_result)

    # Giả sử ocr_result chứa dữ liệu bảng dạng text, cần xử lý để tạo danh sách từ điển
    data = parse_ocr_result(ocr_result)
    if data:
        display_data(data)

def parse_ocr_result(ocr_result):
    # kết quả OCR là dạng văn bản có cấu trúc bảng
    lines = ocr_result.split('\n')
    header = [cell.strip() for cell in lines[0].split('|')]
    data = []
    for line in lines[2:]:  # Bỏ qua dòng tiêu đề và dòng phân cách
        cells = [cell.strip() for cell in line.split('|')]
        if len(cells) == len(header):
            data.append(dict(zip(header, cells)))
    return data

def display_data(data):
    # Xóa bảng cũ nếu có
    for widget in table_frame.winfo_children():
        widget.destroy()

    tree = ttk.Treeview(table_frame, columns=list(data[0].keys()), show="headings")

    # Tạo tiêu đề cột
    for col in data[0].keys():
        tree.heading(col, text=col)
        tree.column(col, width=100)  # Điều chỉnh chiều rộng cột

    # Chèn dữ liệu vào Treeview
    for row in data:
        tree.insert("", tk.END, values=list(row.values()))

    # Cho phép chỉnh sửa dữ liệu trực tiếp trong bảng
    tree.bind("<Double-1>", lambda event: edit_cell(event, tree))

    tree.pack(expand=tk.YES, fill=tk.BOTH)

    # Nút xuất Excel
    export_button = tk.Button(table_frame, text="Xuất Excel", command=lambda: export_to_excel(data))
    export_button.pack()

def edit_cell(event, tree):
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if item and column != '#0':  # Kiểm tra xem có phải ô dữ liệu không
        x, y, width, height = tree.bbox(item, column)
        value = tree.set(item, column)
        entry = tk.Entry(table_frame, width=width // 8)  # Chia 8 để đảm bảo kích thước phù hợp
        entry.insert(0, value)
        entry.place(x=x, y=y)
        entry.focus()

        def save_change(event):
            tree.set(item, column, entry.get())
            entry.destroy()

        entry.bind("<Return>", save_change)
        entry.bind("<FocusOut>", save_change)

def export_to_excel(data):
    workbook = Workbook()
    sheet = workbook.active

    # Ghi tiêu đề cột
    header = list(data[0].keys())
    sheet.append(header)

    # Ghi dữ liệu
    for row in data:
        sheet.append(list(row.values()))

    # Lấy ngày giờ hiện tại
    now = datetime.datetime.now()
    file_name = now.strftime("%Y-%m-%d_%H-%M-%S.xlsx")

    # Tạo thư mục data_result nếu chưa tồn tại
    if not os.path.exists("data_result"):
        os.makedirs("data_result")

    # Lưu file Excel vào thư mục data_result
    file_path = os.path.join("data_result", file_name)
    workbook.save(file_path)
    print(f"Dữ liệu đã được xuất ra file {file_path}")

# Tạo cửa sổ chính
window = tk.Tk()
window.title("OCR Image Recognition")

# Nhãn và ô nhập URL
url_label = tk.Label(window, text="URL hình ảnh:")
url_label.pack()
url_entry = tk.Entry(window, width=50)
url_entry.pack()

# Nút gửi yêu cầu
process_button = tk.Button(window, text="Xử lý", command=process_image)
process_button.pack()

# Vùng văn bản kết quả OCR
result_text = scrolledtext.ScrolledText(window, width=60, height=10)
result_text.pack()

# Frame để chứa bảng
table_frame = tk.Frame(window)
table_frame.pack(expand=tk.YES, fill=tk.BOTH)

# Chạy vòng lặp sự kiện
window.mainloop()