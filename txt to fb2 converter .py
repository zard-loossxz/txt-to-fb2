"""
Compact TXT → FB2 Converter (Tkinter)
Improved interface with FB2 output
"""

import re
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime


def natural_key(s: str):
    """Natural sorting for filenames"""
    parts = re.split(r'([0-9]+)', str(s))
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p.lower())
    return key


def fb2_escape(text: str) -> str:
    """Escape XML special characters for FB2"""
    return (text.replace('&', '&amp;')
               .replace('<', '&lt;')
               .replace('>', '&gt;')
               .replace('"', '&quot;')
               .replace("'", '&apos;'))


class CompactTxtToFb2App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TXT → FB2 Converter")
        self.geometry("900x650")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.files = []
        self.sections = []
        self.current_folder = ""

        self._build_compact_ui()

    def _build_compact_ui(self):
        # Main container with grid
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top controls frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Left side - file operations
        left_controls = ttk.Frame(top_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(left_controls, text="📁 Добавить TXT", 
                  command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_controls, text="📂 Выбрать папку", 
                  command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_controls, text="🗑️ Очистить", 
                  command=self.clear_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_controls, text="🔢 Сортировать", 
                  command=self.natural_sort).pack(side=tk.LEFT, padx=5)

        # Right side - move buttons
        right_controls = ttk.Frame(top_frame)
        right_controls.pack(side=tk.RIGHT)

        ttk.Button(right_controls, text="↑ Вверх", 
                  command=lambda: self.move_selected(-1)).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(right_controls, text="↓ Вниз", 
                  command=lambda: self.move_selected(1)).pack(side=tk.LEFT, padx=2)

        # Book title frame
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="Название книги:").pack(side=tk.LEFT)
        self.ent_title = ttk.Entry(title_frame, width=40)
        self.ent_title.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        ttk.Label(title_frame, text="Автор:").pack(side=tk.LEFT)
        self.ent_author = ttk.Entry(title_frame, width=20)
        self.ent_author.insert(0, "Автор")
        self.ent_author.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(title_frame, text="Папка:").pack(side=tk.LEFT)
        self.lbl_folder = ttk.Label(title_frame, text="Не выбрана", foreground='gray', width=15)
        self.lbl_folder.pack(side=tk.LEFT, padx=(5, 0))

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left - file list
        file_frame = ttk.LabelFrame(content_frame, text="Файлы", padding=5)
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.lst_files = tk.Listbox(file_frame, height=15, bg='white', relief='solid', bd=1)
        files_scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.lst_files.yview)
        self.lst_files.configure(yscrollcommand=files_scrollbar.set)
        
        self.lst_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lst_files.bind('<<ListboxSelect>>', self.on_select)

        # Middle - chapter list
        chapter_frame = ttk.LabelFrame(content_frame, text="Главы (двойной клик)", padding=5)
        chapter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.lst_chapters = tk.Listbox(chapter_frame, height=15, bg='white', relief='solid', bd=1)
        chapters_scrollbar = ttk.Scrollbar(chapter_frame, orient=tk.VERTICAL, command=self.lst_chapters.yview)
        self.lst_chapters.configure(yscrollcommand=chapters_scrollbar.set)
        
        self.lst_chapters.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chapters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lst_chapters.bind('<Double-1>', self.on_chapter_double)

        # Right - preview
        preview_frame = ttk.LabelFrame(content_frame, text="Просмотр", padding=5)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Preview text with scrollbars
        text_container = ttk.Frame(preview_frame)
        text_container.pack(fill=tk.BOTH, expand=True)

        self.txt_preview = tk.Text(text_container, wrap=tk.WORD, bg='white', relief='solid', bd=1, 
                                 font=('Arial', 9), padx=3, pady=3, height=10)
        
        v_scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.txt_preview.yview)
        h_scrollbar = ttk.Scrollbar(text_container, orient=tk.HORIZONTAL, command=self.txt_preview.xview)
        
        self.txt_preview.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.txt_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bottom controls
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(bottom_frame, text="Очистить просмотр", 
                  command=lambda: self.txt_preview.delete('1.0', tk.END)).pack(side=tk.LEFT)

        self.btn_convert = ttk.Button(bottom_frame, text="📚 Конвертировать в FB2", 
                                     command=self.save_fb2)
        self.btn_convert.pack(side=tk.RIGHT)

    def add_files(self):
        """Add individual TXT files"""
        paths = filedialog.askopenfilenames(
            title='Выбрать TXT файлы', 
            filetypes=[('TXT files', '*.txt'), ('All files', '*.*')]
        )
        if paths:
            for p in paths:
                if p not in self.files:
                    self.files.append(p)
            self._rebuild_sections()
            self.refresh_lists()

    def add_folder(self):
        """Add all TXT files from a folder"""
        folder_path = filedialog.askdirectory(title='Выбрать папку с TXT файлами')
        if folder_path:
            self.current_folder = folder_path
            folder_name = Path(folder_path).name
            self.lbl_folder.config(text=folder_name)
            
            # Auto-set book title from folder name
            self.ent_title.delete(0, tk.END)
            self.ent_title.insert(0, folder_name)
            
            # Find all txt files in folder
            txt_files = list(Path(folder_path).glob('*.txt'))
            if txt_files:
                self.files = [str(f) for f in txt_files]
                self.natural_sort()
            else:
                messagebox.showwarning('Файлы не найдены', 'В выбранной папке нет TXT файлов')

    def clear_files(self):
        """Clear all files from list"""
        if not self.files or messagebox.askyesno('Подтвердить', 'Очистить список файлов?'):
            self.files = []
            self.sections = []
            self.current_folder = ""
            self.lbl_folder.config(text="Не выбрана")
            self.refresh_lists()
            self.txt_preview.delete('1.0', tk.END)

    def natural_sort(self):
        """Sort files naturally"""
        self.files.sort(key=lambda p: natural_key(p))
        self._rebuild_sections()
        self.refresh_lists()

    def move_selected(self, direction: int):
        """Move selected file up or down"""
        sel = self.lst_files.curselection()
        if not sel:
            return
        i = sel[0]
        j = i + direction
        if 0 <= j < len(self.files):
            self.files[i], self.files[j] = self.files[j], self.files[i]
            self._rebuild_sections()
            self.refresh_lists()
            self.lst_files.selection_set(j)

    def _rebuild_sections(self):
        """Extract titles and content from files - preserve original titles"""
        self.sections = []
        seen_titles = {}
        
        for path in self.files:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
            except Exception as e:
                lines = [f"Ошибка чтения файла: {e}"]

            # Extract title from first non-empty line
            title = Path(path).stem  # Default to filename without extension
            body_lines = []
            found_title = False
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not found_title:
                    # First non-empty line is the title
                    title_candidate = stripped_line
                    clean_title = title_candidate.strip('= ').strip()
                    title = clean_title if clean_title else title_candidate
                    found_title = True
                else:
                    # Everything else is content
                    body_lines.append(line)

            # Avoid duplicate titles
            if title in seen_titles:
                seen_titles[title] += 1
                title = f"{title} ({seen_titles[title]})"
            else:
                seen_titles[title] = 1

            self.sections.append((title, body_lines, path))

    def refresh_lists(self):
        """Refresh file and chapter lists"""
        # File list - show only filenames
        self.lst_files.delete(0, tk.END)
        for p in self.files:
            filename = Path(p).name
            self.lst_files.insert(tk.END, filename)

        # Chapter list - show original titles
        self.lst_chapters.delete(0, tk.END)
        for title, _, _ in self.sections:
            self.lst_chapters.insert(tk.END, title)

    def on_select(self, event=None):
        """When file is selected in left list"""
        sel = self.lst_files.curselection()
        if sel:
            idx = sel[0]
            if idx < len(self.sections):
                title, body_lines, path = self.sections[idx]
                self._show_preview(title, body_lines, path)

    def on_chapter_double(self, event=None):
        """When chapter is double-clicked"""
        sel = self.lst_chapters.curselection()
        if sel:
            idx = sel[0]
            if idx < len(self.sections):
                title, body_lines, path = self.sections[idx]
                self._show_preview(title, body_lines, path)
                # Select corresponding file
                try:
                    file_idx = self.files.index(path)
                    self.lst_files.selection_clear(0, tk.END)
                    self.lst_files.selection_set(file_idx)
                except ValueError:
                    pass

    def _show_preview(self, title, body_lines, path):
        """Show content preview"""
        self.txt_preview.delete('1.0', tk.END)
        self.txt_preview.insert(tk.END, f"=== {title} ===\n\n")
        
        # Show content
        preview_text = '\n'.join(body_lines)
        if len(preview_text) > 1500:
            preview_text = preview_text[:1500] + "\n\n[...продолжение...]"
        
        self.txt_preview.insert(tk.END, preview_text)
        self.txt_preview.see('1.0')

    def save_fb2(self):
        """Convert and save as FB2"""
        if not self.sections:
            messagebox.showwarning('Нет данных', 'Нет загруженных глав для конвертации')
            return

        book_title = self.ent_title.get().strip() or 'Без названия'
        author_name = self.ent_author.get().strip() or 'Автор'
        
        save_path = filedialog.asksaveasfilename(
            defaultextension='.fb2',
            filetypes=[('FB2 files', '*.fb2')],
            title='Сохранить FB2',
            initialfile=f"{book_title}.fb2"
        )
        
        if not save_path:
            return

        try:
            self._create_fb2(book_title, author_name, save_path)
            messagebox.showinfo('Готово', f'FB2 успешно создан:\n{save_path}')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось создать FB2:\n{str(e)}')

    def _create_fb2(self, book_title, author_name, save_path):
        """Create FB2 file with proper structure"""
        # Build body sections
        body_sections = []
        
        for title, body_lines, path in self.sections:
            # Process body lines
            content_lines = []
            for line in body_lines:
                if line.strip():
                    content_lines.append(f"<p>{fb2_escape(line)}</p>")
                else:
                    content_lines.append("<empty-line/>")
            
            body_content = '\n    '.join(content_lines)
            
            section = f"""  <section>
    <title>
      <p>{fb2_escape(title)}</p>
    </title>
    {body_content}
  </section>"""
            body_sections.append(section)

        # Combine all sections
        full_body = '\n'.join(body_sections)

        # Create complete FB2
        fb2_content = f"""<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
  <description>
    <title-info>
      <genre>fiction</genre>
      <author>
        <nickname>{fb2_escape(author_name)}</nickname>
      </author>
      <book-title>{fb2_escape(book_title)}</book-title>
      <lang>ru</lang>
    </title-info>
    <document-info>
      <author>
        <nickname>TXT2FB2 Converter</nickname>
      </author>
      <program-used>TXT to FB2 Converter</program-used>
      <date>{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}</date>
      <id>{uuid.uuid4()}</id>
      <version>1.0</version>
    </document-info>
  </description>
  <body>
{full_body}
  </body>
</FictionBook>"""

        # Save file
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(fb2_content)


if __name__ == '__main__':
    app = CompactTxtToFb2App()
    app.mainloop()