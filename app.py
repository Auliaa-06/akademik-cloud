import csv
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
# Kita panggil fungsi khusus penembak API Supabase dari config.py
from config import query_supabase_api, supabase_client 

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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Ambil data user dari tabel 'users' di Supabase Cloud via API
        users_data = query_supabase_api('users', filters={'username': username})
        user = users_data[0] if users_data else None

        # validasi password (mendukung teks biasa atau hash)
        if user and (user['password'] == password or check_password_hash(user['password'], password)):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))

        error = 'Username atau Password salah!'

    return render_template('login.html', error=error)

# --- RUTE UNTUK DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Ambil data statistik langsung dari tabel cloud Supabase
    mhs_data = query_supabase_api('mahasiswa')
    mk_data = query_supabase_api('mata_kuliah')
    nilai_data = query_supabase_api('nilai')

    total_mhs = len(mhs_data)
    total_mk = len(mk_data)
    
    nilai_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
    counts = Counter(item['nilai_huruf'] for item in nilai_data)
    for key, value in counts.items():
        if key in nilai_stats:
            nilai_stats[key] = value

    return render_template(
        'dashboard.html',
        total_mhs=total_mhs,
        total_mk=total_mk,
        nilai_stats=nilai_stats,
    )

# --- RUTE MANAJEMEN DATA MAHASISWA ---
@app.route('/mahasiswa')
def mahasiswa():
    if 'username' not in session:
        return redirect(url_for('login'))

    mhs_data = query_supabase_api('mahasiswa')
    mahasiswa_list = sorted(mhs_data, key=lambda item: item['nim'])
    return render_template('mahasiswa.html', mahasiswa_list=mahasiswa_list)

@app.route('/mahasiswa/tambah', methods=['POST'])
def tambah_mahasiswa():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']:
        return 'Akses Ditolak!', 403

    nim = request.form.get('nim', '').strip()
    nama = request.form.get('nama', '').strip()
    jurusan = request.form.get('jurusan', '').strip()
    angkatan = request.form.get('angkatan', '').strip()

    if nim and nama and jurusan and angkatan:
        try:
            data_insert = {'nim': nim, 'nama': nama, 'jurusan': jurusan, 'angkatan': int(angkatan)}
            supabase_client.table('mahasiswa').insert(data_insert).execute()
        except Exception as e:
            print(f"Gagal tambah mahasiswa: {e}")

    return redirect(url_for('mahasiswa'))

@app.route('/mahasiswa/hapus/<nim>')
def hapus_mahasiswa(nim):
    if 'username' not in session or session['role'] != 'admin':
        return 'Akses Ditolak!', 403

    try:
        supabase_client.table('nilai').delete().eq('nim', nim).execute()
        supabase_client.table('mahasiswa').delete().eq('nim', nim).execute()
    except Exception as e:
        print(f"Gagal hapus mahasiswa: {e}")
        
    return redirect(url_for('mahasiswa'))

@app.route('/mahasiswa/backup')
def backup_mahasiswa():
    if 'username' not in session:
        return redirect(url_for('login'))

    mhs_data = query_supabase_api('mahasiswa')
    output = []
    output.append('NIM,Nama,Jurusan,Angkatan')
    for row in sorted(mhs_data, key=lambda item: item['nim']):
        output.append(f"{row['nim']},{row['nama']},{row['jurusan']},{row['angkatan']}")

    csv_data = '\n'.join(output) + '\n'
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=backup_mahasiswa_cloud.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

# --- RUTE MANAJEMEN NILAI & MATA KULIAH ---
@app.route('/nilai')
def nilai():
    if 'username' not in session:
        return redirect(url_for('login'))

    raw_nilai = query_supabase_api('nilai')
    mhs_data = query_supabase_api('mahasiswa')
    mk_data = query_supabase_api('mata_kuliah')

    nilai_list = []
    # Melakukan teknik manual JOIN dari hasil API agar kompatibel dengan Vercel
    for item in sorted(raw_nilai, key=lambda row: row.get('id', 0), reverse=True):
        mahasiswa = next((mhs for mhs in mhs_data if mhs['nim'] == item['nim']), None)
        mata_kuliah = next((mk for mk in mk_data if mk['kode_mk'] == item['kode_mk']), None)
        nilai_list.append({
            'nim': item['nim'],
            'nama_mahasiswa': mahasiswa['nama'] if mahasiswa else '-',
            'nama_mk': mata_kuliah['nama_mk'] if mata_kuliah else '-',
            'sks': mata_kuliah['sks'] if mata_kuliah else '-',
            'nilai_angka': item['nilai_angka'],
            'nilai_huruf': item['nilai_huruf'],
        })

    return render_template('nilai.html', nilai_list=nilai_list)

@app.route('/nilai/tambah-mk', methods=['POST'])
def tambah_mk():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']:
        return 'Akses Ditolak!', 403

    kode_mk = request.form.get('kode_mk', '').strip()
    nama_mk = request.form.get('nama_mk', '').strip()
    sks = request.form.get('sks', '').strip()

    if kode_mk and nama_mk and sks:
        try:
            data_insert = {'kode_mk': kode_mk, 'nama_mk': nama_mk, 'sks': int(sks)}
            supabase_client.table('mata_kuliah').insert(data_insert).execute()
        except Exception as e:
            print(f"Gagal tambah mata kuliah: {e}")

    return redirect(url_for('nilai'))

@app.route('/nilai/tambah-nilai', methods=['POST'])
def tambah_nilai():
    if 'username' not in session or session['role'] not in ['admin', 'dosen']:
        return 'Akses Ditolak!', 403

    nim = request.form.get('nim', '').strip()
    kode_mk = request.form.get('kode_mk', '').strip()
    nilai_angka = request.form.get('nilai_angka', '').strip()
    nilai_huruf = request.form.get('nilai_huruf', '').strip()

    if nim and kode_mk and nilai_angka and nilai_huruf:
        try:
            data_insert = {
                'nim': nim,
                'kode_mk': kode_mk,
                'nilai_angka': int(nilai_angka),
                'nilai_huruf': nilai_huruf,
            }
            supabase_client.table('nilai').insert(data_insert).execute()
        except Exception as e:
            print(f"Gagal tambah nilai: {e}")

    return redirect(url_for('nilai'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)