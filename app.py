import csv
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_akademik_cloud' 

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- RUTE UNTUK LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and user['password'] == password:
                session['username'] = user['username']
                session['role'] = user['role'] 
                return redirect(url_for('dashboard'))
            else:
                error = "Username atau Password salah!"
        else:
            error = "Gagal terhubung ke database server cloud."
            
    return render_template('login.html', error=error)

# --- RUTE UNTUK DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    total_mhs = 0
    total_mk = 0
    nilai_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
    
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mahasiswa")
        total_mhs = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM mata_kuliah")
        total_mk = cur.fetchone()['count']
        
        cur.execute("SELECT nilai_huruf, COUNT(*) FROM nilai GROUP BY nilai_huruf")
        rows = cur.fetchall()
        for row in rows:
            nilai_stats[row['nilai_huruf']] = row['count']
            
        cur.close()
        conn.close()
        
    return render_template('dashboard.html', total_mhs=total_mhs, total_mk=total_mk, nilai_stats=nilai_stats)

# --- RUTE MANAJEMEN DATA MAHASISWA ---
@app.route('/mahasiswa')
def mahasiswa():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    mahasiswa_list = []
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM mahasiswa ORDER BY nim ASC")
        mahasiswa_list = cur.fetchall()
        cur.close()
        conn.close()
    return render_template('mahasiswa.html', mahasiswa_list=mahasiswa_list)

@app.route('/mahasiswa/tambah', methods=['POST'])
def tambah_mahasiswa():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']:
        return "Akses Ditolak!", 403
    nim, nama, jurusan, angkatan = request.form['nim'], request.form['nama'], request.form['jurusan'], request.form['angkatan']
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO mahasiswa (nim, nama, jurusan, angkatan) VALUES (%s, %s, %s, %s)", (nim, nama, jurusan, angkatan))
            conn.commit()
        except Exception as e: print(e)
        finally: cur.close(); conn.close()
    return redirect(url_for('mahasiswa'))

@app.route('/mahasiswa/hapus/<nim>')
def hapus_mahasiswa(nim):
    if 'username' not in session or session['role'] != 'admin': return "Akses Ditolak!", 403
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM mahasiswa WHERE nim = %s", (nim,))
        conn.commit()
        cur.close(); conn.close()
    return redirect(url_for('mahasiswa'))

@app.route('/mahasiswa/backup')
def backup_mahasiswa():
    if 'username' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT nim, nama, jurusan, angkatan FROM mahasiswa ORDER BY nim ASC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        csv_data = "NIM,Nama,Jurusan,Angkatan\n"
        for row in rows: csv_data += f"{row['nim']},{row['nama']},{row['jurusan']},{row['angkatan']}\n"
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = "attachment; filename=backup_mahasiswa_cloud.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    return "Gagal", 500

# --- RUTE MANAJEMEN NILAI & MATA KULIAH ---
@app.route('/nilai')
def nilai():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    nilai_list = []
    if conn:
        cur = conn.cursor()
        # Query JOIN untuk menyatukan data Nilai, Nama Mahasiswa, dan Nama Mata Kuliah
        cur.execute("""
            SELECT n.nim, m.nama as nama_mahasiswa, mk.nama_mk, mk.sks, n.nilai_angka, n.nilai_huruf 
            FROM nilai n
            JOIN mahasiswa m ON n.nim = m.nim
            JOIN mata_kuliah mk ON n.kode_mk = mk.kode_mk
            ORDER BY n.id DESC
        """)
        nilai_list = cur.fetchall()
        cur.close()
        conn.close()
    return render_template('nilai.html', nilai_list=nilai_list)

@app.route('/nilai/tambah-mk', methods=['POST'])
def tambah_mk():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']: return "Akses Ditolak!", 403
    kode_mk, nama_mk, sks = request.form['kode_mk'], request.form['nama_mk'], request.form['sks']
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO mata_kuliah (kode_mk, nama_mk, sks) VALUES (%s, %s, %s)", (kode_mk, nama_mk, sks))
            conn.commit()
        except Exception as e: print(e)
        finally: cur.close(); conn.close()
    return redirect(url_for('nilai'))

@app.route('/nilai/tambah-nilai', methods=['POST'])
def tambah_nilai():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']: return "Akses Ditolak!", 403
    nim, kode_mk, nilai_angka, nilai_huruf = request.form['nim'], request.form['kode_mk'], request.form['nilai_angka'], request.form['nilai_huruf']
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO nilai (nim, kode_mk, nilai_angka, nilai_huruf) VALUES (%s, %s, %s, %s)", (nim, kode_mk, nilai_angka, nilai_huruf))
            conn.commit()
        except Exception as e: print(e)
        finally: cur.close(); conn.close()
    return redirect(url_for('nilai'))

# --- RUTE UNTUK LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)