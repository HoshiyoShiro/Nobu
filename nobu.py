import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.scrolledtext import ScrolledText
import re
import os
import json
import threading
import time
from pathlib import Path
import keyword
import importlib
import ast

class Nobu(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title("Nobu - Code Editor")
        self.root.geometry("1200x800")
        
        self.config_path = Path.home() / '.nobu_editor_config.json'
        self.config = self.load_config()
        
        self.themes = {
            "default": {
                "bg": "white",
                "fg": "black",
                "keyword": "blue",
                "builtin": "purple",
                "string": "green",
                "comment": "gray",
                "number": "orange",
                "tag": "#0000FF",
                "attribute": "#FF00FF",
                "selector": "#A0A000",
                "property": "#00A0A0",
                "value": "#0000A0",
                "punctuation": "#808080"
            },
            "dark": {
                "bg": "#282c34",
                "fg": "#abb2bf",
                "keyword": "#c678dd",
                "builtin": "#61afef",
                "string": "#98c379",
                "comment": "#5c6370",
                "number": "#d19a66",
                "tag": "#61afef",
                "attribute": "#c678dd",
                "selector": "#98c379",
                "property": "#56b6c2",
                "value": "#61afef",
                "punctuation": "#abb2bf"
            },
            "light": {
                "bg": "#f5f5f5",
                "fg": "#333333",
                "keyword": "#0000ff",
                "builtin": "#800080",
                "string": "#008000",
                "comment": "#808080",
                "number": "#ff8c00",
                "tag": "#0000FF",
                "attribute": "#FF00FF",
                "selector": "#A0A000",
                "property": "#00A0A0",
                "value": "#0000A0",
                "punctuation": "#808080"
            }
        }
        
        self.language_keywords = {
            'python': {
                'keywords': set(keyword.kwlist),
                'builtins': set(dir(__builtins__)),
                'patterns': {
                    'keywords': r'\b(def|class|if|else|elif|for|while|try|except|import|from|as|return|break|continue)\b',
                    'builtin': r'\b(print|len|str|int|float|list|dict|set|tuple|range|enumerate|zip)\b',
                    'string': r'(\".*?\"|\'.*?\')',
                    'comment': r'(#.*$)',
                    'numbers': r'\b(\d+)\b'
                }
            },
            'html': {
                'patterns': {
                    'tag': r'(<[^>]*>)',
                    'attribute': r'\s([a-zA-Z-]+)=',
                    'string': r'(\".*?\"|\'.*?\')',
                    'comment': r'(<!--[\s\S]*?-->)'
                }
            },
            'css': {
                'patterns': {
                    'selector': r'([^\{\}]+)\{',
                    'property': r'([\w-]+)\s*:',
                    'value': r':\s*([^;]+);',
                    'comment': r'(/\*[\s\S]*?\*/)',
                    'numbers': r'\b(\d+\.?\d*)\b'
                }
            },
            'javascript': {
                'patterns': {
                    'keywords': r'\b(function|var|let|const|if|else|for|while|do|switch|case|break|return|try|catch|finally|class|extends|new|this)\b',
                    'builtin': r'\b(console|document|window|Array|Object|String|Number|Boolean|Function|Symbol|RegExp)\b',
                    'string': r'(\".*?\"|\'.*?\'|`[\s\S]*?`)',
                    'comment': r'(/\*[\s\S]*?\*/|//.*$)',
                    'numbers': r'\b(\d+\.?\d*)\b'
                }
            },
            'json': {
                'patterns': {
                    'string': r'(\".*?\")',
                    'numbers': r'\b(\d+\.?\d*)\b',
                    'keywords': r'\b(true|false|null)\b',
                    'punctuation': r'([\{\}\[\],:])'
                }
            }
        }

        # Initialize zoom level
        self.current_zoom = 100  # percentage
        
        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.setup_auto_save()
        
        # Bind mouse wheel for zooming
        self.root.bind("<Control-MouseWheel>", self.mouse_wheel_zoom)

    def mouse_wheel_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def load_config(self):
        default_config = {
            'theme': 'dark',
            'font': ('Consolas', 12),
            'auto_save_interval': 300,  # 5 minutes
            'recent_files': [],
            'code_snippets': {}
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            return default_config
        except Exception as e:
            print(f"Config load error: {e}")
            return default_config

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Config save error: {e}")

    def setup_ui(self):
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Status bar at the bottom
        self.status_bar = ttk.Label(self.root, text="Nobu - Ready", anchor=tk.W, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Initial tab
        self.new_file()

    def setup_menus(self):
        # Create a menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Print to File", command=self.print_to_file)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_current_tab, accelerator="Ctrl+W")
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Find", command=self.show_find_replace_dialog, accelerator="Ctrl+F")
        edit_menu.add_command(label="Go To Line", command=self.go_to_line)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.zoom_reset, accelerator="Ctrl+0")
        menubar.add_cascade(label="View", menu=view_menu)

        # Language menu
        language_menu = tk.Menu(menubar, tearoff=0)
        for lang in self.language_keywords.keys():
            language_menu.add_command(
                label=lang.capitalize(),
                command=lambda l=lang: self.change_language(l)
            )
        menubar.add_cascade(label="Language", menu=language_menu)

    def print_to_file(self):
        current = self.notebook.select()
        if current:
            tab = self.notebook.nametowidget(current).winfo_children()[0]
            content = tab.text_area.get('1.0', tk.END)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.status_bar.config(text=f"Content printed to: {filename}")
                except Exception as e:
                    messagebox.showerror("Print Error", str(e))

    def new_file(self):
        # Create a new tab container
        tab_container = ttk.Frame(self.notebook)
        
        # Create the CodeTab instance
        code_tab = CodeTab(tab_container, self)
        code_tab.pack(fill=tk.BOTH, expand=True)
        
        # Add the tab to notebook
        tab_name = f"Untitled-{len(self.notebook.tabs())+1}"
        self.notebook.add(tab_container, text=tab_name)
        
        # Select the new tab
        self.notebook.select(tab_container)
        self.status_bar.config(text="New file created")

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Python Files", "*.py"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("JavaScript Files", "*.js"),
                ("JSON Files", "*.json"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create new tab container
                tab_container = ttk.Frame(self.notebook)
                
                # Create the CodeTab instance
                code_tab = CodeTab(tab_container, self, filename, content)
                code_tab.pack(fill=tk.BOTH, expand=True)
                
                # Add the tab to notebook with the filename as title
                self.notebook.add(tab_container, text=os.path.basename(filename))
                self.notebook.select(tab_container)
                
                # Update recent files
                if filename not in self.config['recent_files']:
                    self.config['recent_files'].append(filename)
                    self.save_config()
                
                self.status_bar.config(text=f"Opened: {filename}")
            except Exception as e:
                messagebox.showerror("Open Error", str(e))

    def save_file(self, tab=None):
        if not tab:
            current = self.notebook.select()
            if not current:
                return False
            tab = self.notebook.nametowidget(current).winfo_children()[0]
        
        if not hasattr(tab, 'filename') or not tab.filename:
            return self.save_as_file(tab)
        
        try:
            with open(tab.filename, 'w', encoding='utf-8') as f:
                f.write(tab.text_area.get('1.0', tk.END))
            tab.is_modified = False
            self.status_bar.config(text=f"Saved: {tab.filename}")
            return True
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            return False

    def save_as_file(self, tab=None):
        if not tab:
            current = self.notebook.select()
            if not current:
                return False
            tab = self.notebook.nametowidget(current).winfo_children()[0]
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                ("Python Files", "*.py"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("JavaScript Files", "*.js"),
                ("JSON Files", "*.json"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(tab.text_area.get('1.0', tk.END))
                
                tab.filename = filename
                tab.is_modified = False
                
                # Update tab title
                current = self.notebook.select()
                self.notebook.tab(current, text=os.path.basename(filename))
                
                self.status_bar.config(text=f"Saved: {filename}")
                return True
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                return False

    def close_current_tab(self):
        if len(self.notebook.tabs()) > 1:
            current = self.notebook.select()
            self.notebook.forget(current)
            self.status_bar.config(text="Tab closed")
        else:
            messagebox.showinfo("Info", "Cannot close the last tab")

    def go_to_line(self):
        current = self.notebook.select()
        if current:
            tab = self.notebook.nametowidget(current).winfo_children()[0]
            line_number = simpledialog.askinteger("Go To Line", "Enter line number:")
            if line_number:
                try:
                    tab.text_area.mark_set(tk.INSERT, f"{line_number}.0")
                    tab.text_area.see(tk.INSERT)
                    # Highlight the line
                    tab.text_area.tag_remove('highlight_line', '1.0', tk.END)
                    tab.text_area.tag_add('highlight_line', f"{line_number}.0", f"{line_number}.end+1c")
                    tab.text_area.tag_config('highlight_line', background='yellow')
                except tk.TclError:
                    messagebox.showwarning("Warning", "Line number out of range")

    def show_find_replace_dialog(self):
        current = self.notebook.select()
        if current:
            tab = self.notebook.nametowidget(current).winfo_children()[0]
            FindReplaceDialog(self.root, tab.text_area)

    def change_theme(self, theme_name):
        self.config['theme'] = theme_name
        theme = self.themes[theme_name]
        
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id).winfo_children()[0]
            tab.text_area.configure(
                bg=theme['bg'], 
                fg=theme['fg']
            )
            tab.syntax_highlight()
        
        self.save_config()

    def zoom_in(self, event=None):
        if self.current_zoom < 200:  # Maximum 200%
            self.current_zoom += 10
            self.apply_zoom()

    def zoom_out(self, event=None):
        if self.current_zoom > 50:  # Minimum 50%
            self.current_zoom -= 10
            self.apply_zoom()

    def zoom_reset(self, event=None):
        self.current_zoom = 100
        self.apply_zoom()

    def apply_zoom(self):
        current = self.notebook.select()
        if current:
            tab = self.notebook.nametowidget(current).winfo_children()[0]
            font = list(self.config['font'])
            font_size = int(12 * self.current_zoom / 100)
            font[1] = font_size
            
            # Update both text area and line numbers font
            tab.text_area.configure(font=tuple(font))
            tab.line_numbers.configure(font=tuple(font))
            
            # Update line numbers width based on total lines
            total_lines = tab.text_area.get('1.0', tk.END).count('\n')
            width = len(str(total_lines)) + 1
            tab.line_numbers.configure(width=width)
            
            self.status_bar.config(text=f"Zoom: {self.current_zoom}%")

    def change_language(self, language):
        current = self.notebook.select()
        if current:
            tab = self.notebook.nametowidget(current).winfo_children()[0]
            tab.current_language = language
            tab.syntax_highlight()
            self.status_bar.config(text=f"Language changed to {language}")

    def auto_save(self):
        while True:
            for tab_id in self.notebook.tabs():
                tab = self.notebook.nametowidget(tab_id).winfo_children()[0]
                if hasattr(tab, 'is_modified') and tab.is_modified:
                    if hasattr(tab, 'filename') and tab.filename:
                        self.save_file(tab)
            time.sleep(self.config['auto_save_interval'])

    def setup_auto_save(self):
        auto_save_thread = threading.Thread(target=self.auto_save, daemon=True)
        auto_save_thread.start()

    def setup_shortcuts(self):
        shortcuts = [
            ('<Control-n>', self.new_file),
            ('<Control-o>', self.open_file),
            ('<Control-s>', lambda event: self.save_file()),
            ('<Control-Shift-S>', lambda event: self.save_as_file()),
            ('<Control-f>', self.show_find_replace_dialog),
            ('<Control-w>', self.close_current_tab),
            ('<Control-plus>', self.zoom_in),
            ('<Control-minus>', self.zoom_out),
            ('<Control-0>', self.zoom_reset)
        ]
        
        for shortcut, command in shortcuts:
            self.root.bind(shortcut, lambda event, cmd=command: cmd())

class CodeTab(ttk.Frame):
    def __init__(self, parent, master, filename=None, content=None):
        super().__init__(parent)
        
        self.master = master
        self.filename = filename
        self.is_modified = False
        
        # Determine language based on file extension
        self.current_language = 'python'  # default
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            lang_map = {
                '.py': 'python',
                '.html': 'html',
                '.css': 'css',
                '.js': 'javascript',
                '.json': 'json'
            }
            self.current_language = lang_map.get(ext, 'python')

        # Line numbers
        self.line_numbers = tk.Text(self, width=4, padx=4, takefocus=0, border=0, background='lightgray')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Text area setup
        self.text_area = ScrolledText(self, wrap=tk.WORD, undo=True)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Synchronize line numbers scrolling with text area
        self.text_area.vbar = self.text_area.vbar  # Get scrollbar reference
        self.text_area.vbar.config(command=self.on_scroll)
        self.text_area.config(yscrollcommand=self.on_text_scroll)
        
        # Configure text area
        self.text_area.configure(
            font=master.config['font'], 
            bg=master.themes[master.config['theme']]['bg'],
            fg=master.themes[master.config['theme']]['fg']
        )

        # Event bindings
        self.text_area.bind('<<Modified>>', self.on_modify)
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<Configure>', self.update_line_numbers)

        # Add content if provided
        if content:
            self.text_area.insert(tk.END, content)
            self.text_area.edit_reset()  # Clear undo/redo stack
            self.text_area.edit_modified(False)

        # Initialize line numbers
        self.update_line_numbers()

    def on_scroll(self, *args):
        # Synchronize text and line numbers scrolling
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

    def on_text_scroll(self, *args):
        # Update line numbers when text is scrolled
        self.text_area.vbar.set(*args)
        self.line_numbers.yview_moveto(args[0])

    def on_key_release(self, event):
        self.syntax_highlight()
        self.update_line_numbers()

    def on_modify(self, event=None):
        self.is_modified = self.text_area.edit_modified()
        if self.is_modified:
            current_text = self.text_area.get('1.0', tk.END)
            
            # Update tab name with asterisk if modified
            current_tab = self.master.notebook.select()
            current_text = self.master.notebook.tab(current_tab, "text")
            if not current_text.startswith("*"):
                self.master.notebook.tab(current_tab, text=f"*{current_text}")
            
            self.master.status_bar.config(text="File modified")

    def syntax_highlight(self, event=None):
        text_area = self.text_area
        content = text_area.get('1.0', tk.END)
        lang_patterns = self.master.language_keywords[self.current_language]['patterns']
        theme = self.master.themes[self.master.config['theme']]

        # Remove existing tags
        for tag in text_area.tag_names():
            text_area.tag_remove(tag, '1.0', tk.END)

        # Apply syntax highlighting based on language
        for token_type, pattern in lang_patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                
                # Get color from theme, fallback to foreground color
                color = theme.get(token_type, theme['fg'])
                text_area.tag_add(token_type, start, end)
                text_area.tag_config(token_type, foreground=color)

    def update_line_numbers(self, event=None):
        # Get the total number of lines
        final_index = self.text_area.index('end-1c')
        num_of_lines = int(final_index.split('.')[0])

        # Update line numbers width based on the number of digits
        width = len(str(num_of_lines)) + 1
        self.line_numbers.configure(width=width)

        # Generate line numbers text
        line_numbers_text = '\n'.join(str(i) for i in range(1, num_of_lines + 1))
        
        # Update line numbers
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state=tk.DISABLED)

class FindReplaceDialog(tk.Toplevel):
    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.text_widget = text_widget
        self.search_start_index = '1.0'
        
        self.title("Find and Replace")
        self.geometry("400x250")
        
        # Find section
        tk.Label(self, text="Find:").pack(pady=5)
        self.find_entry = tk.Entry(self, width=40)
        self.find_entry.pack()
        
        # Replace section
        tk.Label(self, text="Replace:").pack(pady=5)
        self.replace_entry = tk.Entry(self, width=40)
        self.replace_entry.pack()
        
        # Word count label
        self.word_count_label = tk.Label(self, text="")
        self.word_count_label.pack(pady=5)
        
        # Buttons
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=10)
        
        tk.Button(buttons_frame, text="Find", command=self.find_text).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Replace", command=self.replace_text).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Count", command=self.count_occurrences).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to find_text
        self.find_entry.bind('<Return>', lambda e: self.find_text())

    def find_text(self):
        text = self.find_entry.get()
        if not text:
            return
            
        # Remove previous highlights
        self.text_widget.tag_remove('highlight', '1.0', tk.END)
        
        # Start search from current position
        start_pos = self.text_widget.search(text, self.search_start_index, tk.END)
        
        if not start_pos:  # If not found, start from beginning
            self.search_start_index = '1.0'
            start_pos = self.text_widget.search(text, self.search_start_index, tk.END)
            if not start_pos:  # If still not found
                messagebox.showinfo("Find", "Text not found")
                return
        
        line, char = start_pos.split('.')
        end_pos = f"{line}.{int(char) + len(text)}"
        
        # Highlight the found text
        self.text_widget.tag_add('highlight', start_pos, end_pos)
        self.text_widget.tag_config('highlight', background='yellow')
        self.text_widget.see(start_pos)
        self.text_widget.mark_set(tk.INSERT, end_pos)
        
        # Update search start index for next search
        self.search_start_index = end_pos

    def replace_text(self):
        # First remove the current highlight if exists
        ranges = self.text_widget.tag_ranges('highlight')
        if ranges:
            start, end = ranges[0], ranges[1]
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, self.replace_entry.get())
            self.find_text()  # Find next occurrence

    def replace_all(self):
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        
        content = self.text_widget.get('1.0', tk.END)
        new_content = content.replace(find_text, replace_text)
        
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', new_content)
        
        # Show how many replacements were made
        occurrences = content.count(find_text)
        messagebox.showinfo("Replace All", f"Replaced {occurrences} occurrence(s)")

    def count_occurrences(self):
        find_text = self.find_entry.get()
        content = self.text_widget.get('1.0', tk.END)
        count = content.count(find_text)
        self.word_count_label.config(text=f"Occurrences: {count}")

def main():
    root = tk.Tk()
    
    try:
        root.iconbitmap('nobu_icon.ico')  
    except Exception:
        pass  # Fallback if icon loading fails
    
    app = Nobu(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Custom window management
    def on_closing():
        # Check for unsaved changes in all tabs
        for tab_id in app.notebook.tabs():
            tab = app.notebook.nametowidget(tab_id).winfo_children()[0]
            if tab.is_modified:
                response = messagebox.askyesnocancel(
                    "Unsaved Changes", 
                    "You have unsaved changes. Do you want to save before exiting?"
                )
                
                if response is None:  # Cancel
                    return
                elif response:  # Yes
                    app.save_file(tab)
        
        # Save configuration before closing
        app.save_config()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()