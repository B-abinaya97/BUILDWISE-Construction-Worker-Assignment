"""Construction Worker Assignment System: SQLite CRUD + Tkinter + SWI-Prolog.
Run: python gui_crud.py (keep reasoning.pl in the same directory).
"""
import re
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from pyswip import Prolog

BASE = Path(__file__).resolve().parent
DB = BASE / 'construction.db'
RULES = BASE / 'reasoning.pl'
NAVY, BLUE, BG, WHITE = '#16243a', '#2463db', '#edf2f8', '#ffffff'

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute('PRAGMA foreign_keys=ON')
conn.executescript('''
CREATE TABLE IF NOT EXISTS workers (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 skill TEXT NOT NULL,
 years INTEGER NOT NULL CHECK(years >= 0),
 certificate TEXT NOT NULL DEFAULT '',
 available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1))
);
CREATE TABLE IF NOT EXISTS tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 skill TEXT NOT NULL,
 min_years INTEGER NOT NULL CHECK(min_years >= 0),
 certificate TEXT NOT NULL DEFAULT ''
);
''')
conn.commit()

# Seed example records only when the database is first empty.
if conn.execute('SELECT COUNT(*) FROM workers').fetchone()[0] == 0 and conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 0:
    conn.executemany('INSERT INTO workers(name,skill,years,certificate,available) VALUES(?,?,?,?,?)', [
        ('Kamal','plumbing',3,'',1), ('Ravi','electrical',5,'electrical_license',1),
        ('John','bricklaying',6,'',1), ('Saman','electrical',5,'electrical_license',0),
        ('Nimal','plumbing',1,'',1), ('Sunil','painting',1,'',1)
    ])
    conn.executemany('INSERT INTO tasks(title,skill,min_years,certificate) VALUES(?,?,?,?)', [
        ('Plumbing','plumbing',3,''), ('Electrical installation','electrical',4,'electrical_license'),
        ('Bricklaying','bricklaying',3,''), ('Painting','painting',2,'')
    ])
    conn.commit()

prolog = Prolog()
try:
    prolog.consult(str(RULES))
except Exception as exc:
    messagebox.showerror('Prolog initialization error', str(exc))
    raise

# Normalize user-entered skill/certification names to safe Prolog atoms.
def atom(value):
    value = re.sub(r'[^a-z0-9_]+', '_', value.strip().lower()).strip('_')
    if not value:
        return None
    return 'a_' + value


def synchronize():
    """Refresh dynamic Prolog facts from persistent SQLite rows."""
    for predicate in ('worker/1','task/1','skill/2','skill_experience/3',
                      'certification/2','available/1','required_skill/2',
                      'minimum_experience/2','required_certification/2'):
        name, arity = predicate.split('/')
        prolog.retractall(f'{name}({",".join("_" for _ in range(int(arity)))})')
    for w in conn.execute('SELECT * FROM workers'):
        wid = f'w{w["id"]}'
        s = atom(w['skill'])
        prolog.assertz(f'worker({wid})')
        prolog.assertz(f'skill({wid},{s})')
        prolog.assertz(f'skill_experience({wid},{s},{w["years"]})')
        if w['certificate'].strip():
            prolog.assertz(f'certification({wid},{atom(w["certificate"])})')
        if w['available']:
            prolog.assertz(f'available({wid})')
    for t in conn.execute('SELECT * FROM tasks'):
        tid = f't{t["id"]}'
        prolog.assertz(f'task({tid})')
        prolog.assertz(f'required_skill({tid},{atom(t["skill"])})')
        prolog.assertz(f'minimum_experience({tid},{t["min_years"]})')
        if t['certificate'].strip():
            prolog.assertz(f'required_certification({tid},{atom(t["certificate"])})')

root = tk.Tk()
root.title('BUILDWISE | Construction Worker Assignment System')
root.geometry('1060x710')
root.minsize(900, 620)
root.configure(bg=BG)
style = ttk.Style(root)
style.theme_use('clam')
style.configure('Treeview', rowheight=29, font=('Segoe UI', 10), background=WHITE, fieldbackground=WHITE)
style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
style.configure('TNotebook.Tab', font=('Segoe UI', 11, 'bold'), padding=(20, 10))

header = tk.Frame(root, bg=NAVY, height=85)
header.pack(fill='x')
header.pack_propagate(False)
tk.Label(header, text='BUILDWISE', bg=NAVY, fg=WHITE, font=('Segoe UI', 22, 'bold')).pack(anchor='w', padx=25, pady=(10, 0))
tk.Label(header, text='CONSTRUCTION WORKFORCE INTELLIGENCE  |  SQLite + SWI-Prolog', bg=NAVY, fg='#b9cbe2', font=('Segoe UI', 10)).pack(anchor='w', padx=27)

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True, padx=20, pady=15)
workers_tab, tasks_tab, reasoning_tab = (ttk.Frame(notebook) for _ in range(3))
for frame, title in ((workers_tab,'Workers · CRUD'),(tasks_tab,'Tasks · CRUD'),(reasoning_tab,'Assignment & Reasoning')):
    notebook.add(frame, text=title)


def field(parent, label, row, col, width=25):
    ttk.Label(parent, text=label).grid(row=row*2, column=col, sticky='w', padx=9, pady=(10, 2))
    entry = ttk.Entry(parent, width=width)
    entry.grid(row=row*2+1, column=col, sticky='ew', padx=9, pady=(0, 5))
    return entry

# Worker management
wf = ttk.LabelFrame(workers_tab, text='Worker details (select a row to edit)')
wf.pack(fill='x', padx=12, pady=12)
wname = field(wf,'Name',0,0)
wskill = field(wf,'Skill (e.g. plumbing)',0,1)
wyears = field(wf,'Skill experience (years)',0,2)
wcert = field(wf,'Certification (optional)',1,0)
wavailable = tk.BooleanVar(value=True)
ttk.Checkbutton(wf, text='Available for assignment', variable=wavailable).grid(row=3,column=1,sticky='w',padx=9)
wf.columnconfigure(0,weight=1); wf.columnconfigure(1,weight=1); wf.columnconfigure(2,weight=1)
wbuttons = ttk.Frame(workers_tab); wbuttons.pack(fill='x',padx=12,pady=4)
wtable = ttk.Treeview(workers_tab, columns=('id','name','skill','years','certificate','available'), show='headings', height=12)
for key,title,width in [('id','ID',55),('name','Name',150),('skill','Skill',150),('years','Years',80),('certificate','Certificate',180),('available','Available',90)]:
    wtable.heading(key,text=title); wtable.column(key,width=width,anchor='center' if key in ('id','years','available') else 'w')
wtable.pack(fill='both',expand=True,padx=12,pady=12)

# Task management
tf = ttk.LabelFrame(tasks_tab, text='Task details (select a row to edit)')
tf.pack(fill='x',padx=12,pady=12)
ttitle = field(tf,'Task title',0,0)
tskill = field(tf,'Required skill',0,1)
tyears = field(tf,'Minimum experience (years)',0,2)
tcert = field(tf,'Required certificate (optional)',1,0)
for col in range(3): tf.columnconfigure(col,weight=1)
tbuttons = ttk.Frame(tasks_tab); tbuttons.pack(fill='x',padx=12,pady=4)
ttable = ttk.Treeview(tasks_tab,columns=('id','title','skill','min_years','certificate'),show='headings',height=12)
for key,title,width in [('id','ID',60),('title','Task',200),('skill','Required skill',160),('min_years','Min. years',110),('certificate','Required certificate',220)]:
    ttable.heading(key,text=title); ttable.column(key,width=width)
ttable.pack(fill='both',expand=True,padx=12,pady=12)


def selected_id(table):
    items=table.selection()
    return int(table.item(items[0], 'values')[0]) if items else None


def put(entry, value):
    entry.delete(0,'end'); entry.insert(0,str(value))


def clear_worker():
    for e in (wname,wskill,wyears,wcert): e.delete(0,'end')
    wavailable.set(True)
    wtable.selection_remove(wtable.selection())


def clear_task():
    for e in (ttitle,tskill,tyears,tcert): e.delete(0,'end')
    ttable.selection_remove(ttable.selection())


def on_worker_select(_=None):
    wid=selected_id(wtable)
    if wid is None: return
    w=conn.execute('SELECT * FROM workers WHERE id=?',(wid,)).fetchone()
    if w:
        for e,val in ((wname,w['name']),(wskill,w['skill']),(wyears,w['years']),(wcert,w['certificate'])): put(e,val)
        wavailable.set(bool(w['available']))


def on_task_select(_=None):
    tid=selected_id(ttable)
    if tid is None: return
    t=conn.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
    if t:
        for e,val in ((ttitle,t['title']),(tskill,t['skill']),(tyears,t['min_years']),(tcert,t['certificate'])): put(e,val)

wtable.bind('<<TreeviewSelect>>',on_worker_select)
ttable.bind('<<TreeviewSelect>>',on_task_select)


def validate(name, skill, years, cert):
    if not name.strip() or not skill.strip(): raise ValueError('Name/title and skill are required.')
    if not atom(skill): raise ValueError('Skill must contain letters or numbers.')
    if cert.strip() and not atom(cert): raise ValueError('Invalid certificate.')
    try: n=int(years)
    except ValueError: raise ValueError('Experience must be a whole number.')
    if n < 0: raise ValueError('Experience cannot be negative.')
    return n


def modify_worker(action):
    try:
        if action=='delete':
            wid=selected_id(wtable)
            if wid is None: raise ValueError('Select a worker to delete.')
            if not messagebox.askyesno('Confirm deletion','Delete the selected worker?'): return
            conn.execute('DELETE FROM workers WHERE id=?',(wid,))
        else:
            vals=(wname.get().strip(),wskill.get().strip(),wyears.get().strip(),wcert.get().strip())
            years=validate(*vals)
            params=(vals[0],vals[1],years,vals[3],int(wavailable.get()))
            if action=='add':
                conn.execute('INSERT INTO workers(name,skill,years,certificate,available) VALUES(?,?,?,?,?)',params)
            else:
                wid=selected_id(wtable)
                if wid is None: raise ValueError('Select a worker to update.')
                conn.execute('UPDATE workers SET name=?,skill=?,years=?,certificate=?,available=? WHERE id=?',params+(wid,))
        conn.commit(); clear_worker(); refresh()
    except (ValueError,sqlite3.Error) as exc: messagebox.showerror('Worker management',str(exc))


def modify_task(action):
    try:
        if action=='delete':
            tid=selected_id(ttable)
            if tid is None: raise ValueError('Select a task to delete.')
            if not messagebox.askyesno('Confirm deletion','Delete the selected task?'): return
            conn.execute('DELETE FROM tasks WHERE id=?',(tid,))
        else:
            vals=(ttitle.get().strip(),tskill.get().strip(),tyears.get().strip(),tcert.get().strip())
            years=validate(*vals)
            params=(vals[0],vals[1],years,vals[3])
            if action=='add':
                conn.execute('INSERT INTO tasks(title,skill,min_years,certificate) VALUES(?,?,?,?)',params)
            else:
                tid=selected_id(ttable)
                if tid is None: raise ValueError('Select a task to update.')
                conn.execute('UPDATE tasks SET title=?,skill=?,min_years=?,certificate=? WHERE id=?',params+(tid,))
        conn.commit(); clear_task(); refresh()
    except (ValueError,sqlite3.Error) as exc: messagebox.showerror('Task management',str(exc))

for title, action in [('Add Worker','add'),('Update Selected','update'),('Delete Selected','delete')]:
    ttk.Button(wbuttons,text=title,command=lambda a=action:modify_worker(a)).pack(side='left',padx=5)
ttk.Button(wbuttons,text='Clear Form',command=clear_worker).pack(side='left',padx=5)
for title, action in [('Add Task','add'),('Update Selected','update'),('Delete Selected','delete')]:
    ttk.Button(tbuttons,text=title,command=lambda a=action:modify_task(a)).pack(side='left',padx=5)
ttk.Button(tbuttons,text='Clear Form',command=clear_task).pack(side='left',padx=5)

# Recommendation / eligibility UI
selector = ttk.LabelFrame(reasoning_tab,text='Choose a worker and task from the database')
selector.pack(fill='x',padx=15,pady=15)
ttk.Label(selector,text='Worker').grid(row=0,column=0,sticky='w',padx=12,pady=(12,3))
ttk.Label(selector,text='Task').grid(row=0,column=1,sticky='w',padx=12,pady=(12,3))
worker_choice=ttk.Combobox(selector,state='readonly',width=37)
task_choice=ttk.Combobox(selector,state='readonly',width=37)
worker_choice.grid(row=1,column=0,sticky='ew',padx=12,pady=(0,12))
task_choice.grid(row=1,column=1,sticky='ew',padx=12,pady=(0,12))
selector.columnconfigure(0,weight=1); selector.columnconfigure(1,weight=1)
result = tk.Text(reasoning_tab,wrap='word',font=('Consolas',11),height=18,bg=WHITE,fg=NAVY,padx=15,pady=15)
result.pack(fill='both',expand=True,padx=15,pady=12)
buttons=ttk.Frame(reasoning_tab); buttons.pack(fill='x',padx=15,pady=4)
worker_ids={}; task_ids={}


def show(text):
    result.delete('1.0','end'); result.insert('end',text)


def get_selection(choice,mapping,what):
    key=mapping.get(choice.get())
    if key is None: raise ValueError(f'Please select a {what}.')
    return key


def reason(action):
    try:
        synchronize()
        if action=='check':
            wid=get_selection(worker_choice,worker_ids,'worker')
            tid=get_selection(task_choice,task_ids,'task')
            w,t=f'w{wid}',f't{tid}'
            passed=bool(list(prolog.query(f'eligible_worker({w},{t})')))
            checks=[('Required skill',f'has_required_skill({w},{t})'),
                    ('Required experience',f'has_required_experience({w},{t})'),
                    ('Required certification',f'has_required_certification({w},{t})'),
                    ('Availability',f'available({w})')]
            lines=['ELIGIBILITY: '+('ELIGIBLE' if passed else 'NOT ELIGIBLE'),'']
            lines += [f'{name}: {"PASS" if list(prolog.query(q)) else "FAIL"}' for name,q in checks]
            show('\n'.join(lines))
        elif action=='workers':
            tid=get_selection(task_choice,task_ids,'task')
            rows=list(prolog.query(f'eligible_worker_list(t{tid}, Workers)'))
            ids=rows[0]['Workers'] if rows else []
            names=[conn.execute('SELECT name FROM workers WHERE id=?',(int(str(x)[1:]),)).fetchone()['name'] for x in ids]
            show('ELIGIBLE WORKERS\n\n'+('\n'.join(f'• {n}' for n in names) if names else 'No eligible workers.')+f'\n\nTotal: {len(names)}')
        elif action=='tasks':
            wid=get_selection(worker_choice,worker_ids,'worker')
            rows=list(prolog.query(f'recommend_task(w{wid}, Task)'))
            ids=sorted({int(str(r['Task'])[1:]) for r in rows})
            names=[conn.execute('SELECT title FROM tasks WHERE id=?',(i,)).fetchone()['title'] for i in ids]
            show('RECOMMENDED TASKS\n\n'+('\n'.join(f'• {n}' for n in names) if names else 'No eligible tasks.')+f'\n\nTotal: {len(names)}')
    except (ValueError,Exception) as exc:
        messagebox.showerror('Reasoning error',str(exc))

for title,action in [('Check Eligibility','check'),('Find Eligible Workers','workers'),('Find Recommended Tasks','tasks')]:
    ttk.Button(buttons,text=title,command=lambda a=action:reason(a)).pack(side='left',padx=5,pady=5)


def refresh():
    for tree in (wtable,ttable):
        for item in tree.get_children(): tree.delete(item)
    for w in conn.execute('SELECT * FROM workers ORDER BY id'):
        wtable.insert('', 'end', values=(w['id'],w['name'],w['skill'],w['years'],w['certificate'],'Yes' if w['available'] else 'No'))
    for t in conn.execute('SELECT * FROM tasks ORDER BY id'):
        ttable.insert('', 'end', values=(t['id'],t['title'],t['skill'],t['min_years'],t['certificate']))
    global worker_ids,task_ids
    worker_ids={f'{w["name"]} (W{w["id"]})':w['id'] for w in conn.execute('SELECT * FROM workers ORDER BY id')}
    task_ids={f'{t["title"]} (T{t["id"]})':t['id'] for t in conn.execute('SELECT * FROM tasks ORDER BY id')}
    worker_choice['values']=list(worker_ids)
    task_choice['values']=list(task_ids)
    worker_choice.set(next(iter(worker_ids),'') if worker_choice.get() not in worker_ids else worker_choice.get())
    task_choice.set(next(iter(task_ids),'') if task_choice.get() not in task_ids else task_choice.get())
    synchronize()


def close():
    conn.close(); root.destroy()
root.protocol('WM_DELETE_WINDOW',close)
refresh()
show('Welcome to BUILDWISE!\n\n1. Manage workers and tasks in the first two tabs.\n2. Select a worker and task above.\n3. Check eligibility or request recommendations.\n\nRecords are saved automatically in construction.db.')
root.mainloop()
