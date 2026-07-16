import os
import re
import json
import pdfplumber
import webbrowser
import threading
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

JS_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

# In-memory transaction state
pending_db = None
pending_subject = ""
pending_target = ""

SUBJECT_KEYS = {
    'dm': {
        'overall': 'dm',
        't1': 'dm1',
        't2': 'dm2',
        't3': 'dm3',
        't4': 'dm4'
    },
    'coa': {
        'overall': 'coa',
        't1': 'coa1',
        't2': 'coa2',
        't3': 'coa3',
        't4': 'coa4'
    },
    'fsd2': {
        'overall': 'fsd2',
        't1': 'fsd21',
        't2': 'fsd22',
        't3': 'fsd23',
        't4': 'fsd24'
    },
    'python2': {
        'overall': 'python2',
        't1': 'fcsp',  # Python-II T1 is stored as fcsp
        't2': 'python22',
        't3': 'python23',
        't4': 'python24'
    },
    'toc': {
        'overall': 'toc',
        't1': 'toc1',
        't2': 'toc2',
        't3': 'toc3',
        't4': 'toc4'
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LJ University - Academic Admin Portal</title>
    <!-- Remix Icons & Google Fonts -->
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f111a;
            --card-bg: rgba(20, 24, 40, 0.65);
            --border-glass: rgba(255, 255, 255, 0.08);
            --primary: #8a7cff;
            --accent: #00cec9;
            --success: #2ecc71;
            --error: #e84393;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * {
            margin: 0; padding: 0; box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 950px;
            background: var(--card-bg);
            border: 1px solid var(--border-glass);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }
        header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border-glass);
            padding-bottom: 20px;
        }
        header i {
            font-size: 2.2rem;
            color: var(--primary);
        }
        header h1 {
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff 30%, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        header p {
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
        .form-group {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }
        .select-input, .text-input {
            width: 100%;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border-glass);
            color: var(--text-main);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.3s;
        }
        .select-input option {
            background-color: #141828;
            color: var(--text-main);
        }
        .select-input:focus, .text-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px rgba(138, 124, 255, 0.2);
        }
        .upload-zone {
            border: 2px dashed rgba(138, 124, 255, 0.3);
            border-radius: 16px;
            padding: 35px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: rgba(138, 124, 255, 0.01);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        .upload-zone:hover {
            border-color: var(--primary);
            background: rgba(138, 124, 255, 0.04);
        }
        .upload-zone i {
            font-size: 2.5rem;
            color: var(--primary);
        }
        .upload-zone p {
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .upload-zone span {
            color: var(--primary);
            font-weight: 600;
        }
        .file-info {
            display: none;
            background: rgba(138, 124, 255, 0.08);
            border: 1px dashed var(--primary);
            border-radius: 12px;
            padding: 12px 16px;
            margin-top: 15px;
            align-items: center;
            justify-content: space-between;
            font-size: 0.85rem;
        }
        .file-info button {
            background: none; border: none; color: var(--error); cursor: pointer; font-size: 1.1rem;
        }
        .btn-submit {
            background: linear-gradient(135deg, var(--primary), #705eff);
            border: none; color: #fff; font-weight: 700;
            padding: 15px; border-radius: 12px; cursor: pointer;
            font-size: 0.95rem; display: flex; align-items: center;
            justify-content: center; gap: 8px; width: 100%;
            box-shadow: 0 10px 20px rgba(138, 124, 255, 0.25);
            transition: all 0.3s;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 25px rgba(138, 124, 255, 0.35);
        }
        .btn-submit:active { transform: translateY(0); }
        .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .results-panel {
            display: none;
            margin-top: 30px;
            border-top: 1px solid var(--border-glass);
            padding-top: 30px;
        }
        .status-box {
            background: rgba(253, 203, 110, 0.1);
            border: 1px solid rgba(253, 203, 110, 0.25);
            color: var(--accent);
            padding: 15px; border-radius: 12px;
            margin-bottom: 20px; font-weight: 600;
            display: flex; align-items: center; gap: 8px;
        }
        .results-table-scroll {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border-glass);
            border-radius: 12px;
        }
        table {
            width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;
        }
        th, td { padding: 12px 16px; border-bottom: 1px solid var(--border-glass); }
        th { background: rgba(255,255,255,0.02); font-weight: 600; color: var(--text-muted); }
        tr:hover td { background: rgba(255,255,255,0.01); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <i class="ri-shield-user-line"></i>
            <div>
                <h1>LJ University - Academic Admin Portal</h1>
                <p>Upload compiled marksheets to dynamically update student databases</p>
            </div>
        </header>

        <form id="uploadForm" onsubmit="handleUpload(event)">
            <div class="grid">
                <!-- Left: Settings -->
                <div>
                    <div class="form-group">
                        <label>Select Target Subject</label>
                        <select class="select-input" id="subject" name="subject" required>
                            <option value="dm">Discrete Mathematics (DM)</option>
                            <option value="coa">Computer Organization & Architecture (COA)</option>
                            <option value="fsd2">Full Stack Development-II (FSD-II)</option>
                            <option value="python2">Python-II</option>
                            <option value="toc">Theory of Computation (TOC)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Target Database Column / Exam</label>
                        <select class="select-input" id="examTarget" name="examTarget" required>
                            <option value="overall">Cumulative Overall Subject Score (e.g. coa, dm)</option>
                            <option value="t2">T2 Score (e.g. coa2, dm2)</option>
                            <option value="t3">T3 Score (e.g. coa3, dm3)</option>
                            <option value="t4">T4 Score (e.g. coa4, dm4)</option>
                            <option value="t1">T1 Score (e.g. fcsp - Python-II Only)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Weightage Multiplier / Formula Mode</label>
                        <select class="select-input" id="multiplier" name="multiplier" required>
                            <option value="1.0">Add Full Marks (current_score + pdf_mark)</option>
                            <option value="0.5">Add Half Marks (current_score + pdf_mark / 2.0)</option>
                            <option value="overwrite">Overwrite / Direct Replace (Replace with pdf_mark)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>PDF Mark Position on Line</label>
                        <select class="select-input" id="markPos" name="markPos" required>
                            <option value="last">Last numeric value on the line (Default)</option>
                            <option value="first">First numeric value after Enrollment</option>
                            <option value="second">Second numeric value after Enrollment</option>
                        </select>
                    </div>

                    <div class="form-group" style="flex-direction: row; align-items: center; gap: 10px; margin-top: 15px;">
                        <input type="checkbox" id="updateCumulative" name="updateCumulative" checked style="width: 18px; height: 18px; accent-color: var(--primary); cursor: pointer;">
                        <label for="updateCumulative" style="cursor: pointer; user-select: none;">Also update Cumulative Overall Subject Score (if updating T2/T3/T4)</label>
                    </div>
                </div>

                <!-- Right: File Drag/Drop & Submit -->
                <div style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div class="form-group">
                        <label>Upload Compiled Marksheet PDF</label>
                        <input type="file" id="fileInput" name="file" accept=".pdf" style="display: none;" onchange="fileSelected(event)" required>
                        <div class="upload-zone" onclick="document.getElementById('fileInput').click()" ondragover="event.preventDefault()" ondrop="fileDropped(event)">
                            <i class="ri-file-pdf-line"></i>
                            <p>Drag and drop your PDF here, or <span>browse</span></p>
                            <p style="font-size: 0.75rem; color: var(--text-muted);">Only compiled marksheet PDFs are supported</p>
                        </div>
                        <div class="file-info" id="fileInfo">
                            <span id="fileName">marksheet.pdf</span>
                            <button type="button" onclick="clearFile()"><i class="ri-close-circle-line"></i></button>
                        </div>
                    </div>

                    <button type="submit" class="btn-submit" id="btnSubmit">
                        <i class="ri-upload-cloud-line"></i> Upload & Preview Changes
                    </button>
                </div>
            </div>
        </form>

        <!-- Results / Confirmation Panel -->
        <div class="results-panel" id="confirmPanel">
            <div class="status-box">
                <i class="ri-alert-line" style="font-size: 1.2rem;"></i>
                <span id="statusMessage">Preview Mode: Data parsed in-memory. Click Accept to save to disk.</span>
            </div>

            <!-- Daksh's Highlight Card -->
            <div id="dakshCard" style="background: rgba(138, 124, 255, 0.08); border: 1px solid var(--primary); border-radius: 16px; padding: 20px; margin-bottom: 25px; display: none;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 1.5rem;">👑</span>
                    <h3 style="font-size: 1.1rem; color: #fff; font-weight: 700;">Target Student Verification: BHAVSAR DAKSH NARENDRABHAI</h3>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; font-size: 0.9rem;">
                    <div>
                        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Exam Score (<span id="dakshKey">coa4</span>)</span>
                        <strong id="dakshOldNew" style="color: var(--primary);">0.00 → 38.00</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Overall Subject Score (Cumulative)</span>
                        <strong id="dakshCumOldNew" style="color: var(--accent);">71.00 → 90.00</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block; font-size: 0.75rem;">Overall Delta (Change Added)</span>
                        <strong id="dakshDelta" style="color: var(--success);">+19.00</strong>
                    </div>
                </div>
            </div>

            <!-- Action buttons -->
            <div style="display: flex; gap: 15px; margin-bottom: 25px;">
                <button type="button" id="btnAccept" class="btn-submit" onclick="confirmChanges()" style="background: linear-gradient(135deg, var(--success), #27ae60); box-shadow: 0 10px 20px rgba(46, 213, 115, 0.25);">
                    <i class="ri-checkbox-circle-line"></i> Accept & Apply Changes (Save DB)
                </button>
                <button type="button" id="btnReject" class="btn-submit" onclick="discardChanges()" style="background: linear-gradient(135deg, var(--error), #c0392b); box-shadow: 0 10px 20px rgba(232, 67, 147, 0.25);">
                    <i class="ri-close-circle-line"></i> Reject & Discard Changes
                </button>
            </div>

            <div class="toppers-title" style="margin-bottom: 12px; font-weight: 700; color: var(--text-muted); font-size: 0.85rem;">
                Comparison Matrix Log (Sample Updates)
            </div>
            <div class="results-table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Roll</th>
                            <th>Enrollment</th>
                            <th>Name</th>
                            <th>Exam Score (Raw)</th>
                            <th>Overall Cumulative</th>
                            <th>Overall Delta</th>
                        </tr>
                    </thead>
                    <tbody id="resultsTableBody">
                        <!-- Filled dynamically -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const subjectSelect = document.getElementById('subject');
        const targetSelect = document.getElementById('examTarget');

        function updateTargetOptions() {
            const sub = subjectSelect.value;
            const target = targetSelect.value;
            
            Array.from(targetSelect.options).forEach(opt => {
                opt.disabled = false;
            });
            
            if (sub !== 'python2') {
                const t1Opt = targetSelect.querySelector('option[value="t1"]');
                if (t1Opt) t1Opt.disabled = true;
                if (target === 't1') targetSelect.value = 'overall';
            }
        }

        subjectSelect.addEventListener('change', updateTargetOptions);
        document.addEventListener('DOMContentLoaded', updateTargetOptions);

        function fileSelected(e) {
            const file = e.target.files[0];
            if (file) showFile(file.name);
        }
        function fileDropped(e) {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.pdf')) {
                document.getElementById('fileInput').files = e.dataTransfer.files;
                showFile(file.name);
            }
        }
        function showFile(name) {
            document.getElementById('fileName').textContent = name;
            document.getElementById('fileInfo').style.display = 'flex';
        }
        function clearFile() {
            document.getElementById('fileInput').value = '';
            document.getElementById('fileInfo').style.display = 'none';
        }

        async function handleUpload(e) {
            e.preventDefault();
            const btn = document.getElementById('btnSubmit');
            btn.disabled = true;
            btn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Processing PDF & DB...';

            const formData = new FormData(document.getElementById('uploadForm'));
            formData.append('updateCumulative', document.getElementById('updateCumulative').checked ? 'true' : 'false');

            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('statusMessage').textContent = `Preview Mode: Successfully parsed marks for ${result.updated_count} students in-memory. Please review below:`;
                    
                    // Show Daksh's Card if found
                    const dakshCard = document.getElementById('dakshCard');
                    if (result.daksh_log) {
                        document.getElementById('dakshKey').textContent = result.target_key;
                        document.getElementById('dakshOldNew').textContent = `${result.daksh_log.old_exam.toFixed(2)} → ${result.daksh_log.new_exam.toFixed(2)}`;
                        document.getElementById('dakshCumOldNew').textContent = `${result.daksh_log.old_cumulative.toFixed(2)} → ${result.daksh_log.new_cumulative.toFixed(2)}`;
                        
                        const delta = result.daksh_log.cumulative_delta;
                        const deltaStr = delta >= 0 ? `+${delta.toFixed(2)}` : `${delta.toFixed(2)}`;
                        document.getElementById('dakshDelta').textContent = deltaStr;
                        document.getElementById('dakshDelta').style.color = delta >= 0 ? 'var(--success)' : 'var(--error)';
                        
                        dakshCard.style.display = 'block';
                    } else {
                        dakshCard.style.display = 'none';
                    }

                    // Populate table
                    let tableHTML = '';
                    result.sample_logs.forEach(log => {
                        const delta = log.cumulative_delta;
                        const deltaStr = delta >= 0 ? `+${delta.toFixed(2)}` : `${delta.toFixed(2)}`;
                        const deltaColor = delta >= 0 ? 'var(--success)' : 'var(--error)';
                        tableHTML += `
                            <tr>
                                <td>${log.roll}</td>
                                <td>${log.enrollment}</td>
                                <td>${log.name}</td>
                                <td>${log.old_exam.toFixed(2)} → ${log.new_exam.toFixed(2)}</td>
                                <td>${log.old_cumulative.toFixed(2)} → ${log.new_cumulative.toFixed(2)}</td>
                                <td style="color:${deltaColor}; font-weight:700;">${deltaStr}</td>
                            </tr>
                        `;
                    });
                    document.getElementById('resultsTableBody').innerHTML = tableHTML || '<tr><td colspan="6" style="text-align:center">No students updated</td></tr>';
                    
                    // Show panel & reset accept/reject buttons
                    document.getElementById('btnAccept').disabled = false;
                    document.getElementById('btnReject').disabled = false;
                    document.getElementById('btnAccept').innerHTML = '<i class="ri-checkbox-circle-line"></i> Accept & Apply Changes (Save DB)';
                    document.getElementById('btnReject').innerHTML = '<i class="ri-close-circle-line"></i> Reject & Discard Changes';
                    document.getElementById('confirmPanel').style.display = 'block';
                    document.getElementById('confirmPanel').scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (err) {
                alert('Connection error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="ri-upload-cloud-line"></i> Upload & Preview Changes';
            }
        }

        async function confirmChanges() {
            const btn = document.getElementById('btnAccept');
            const rejectBtn = document.getElementById('btnReject');
            btn.disabled = true;
            rejectBtn.disabled = true;
            btn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Saving to disk & committing...';

            try {
                const response = await fetch('/confirm', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    let msg = `✅ Success: Database changes written to disk! Backup created as "${result.backup_created}".`;
                    if (result.commit_done) {
                        msg += `<br/>📦 Committed to Git: "<em>${result.commit_message}</em>"`;
                    } else if (result.warning) {
                        msg += `<br/>⚠️ ${result.warning}`;
                    }
                    msg += `<br/><br/>🚀 <strong>You can now run "git push origin main" in your terminal!</strong>`;
                    document.getElementById('statusMessage').innerHTML = msg;
                    btn.innerHTML = '<i class="ri-check-line"></i> Changes Applied';
                    btn.style.background = 'var(--success)';
                } else {
                    alert('Error saving changes: ' + result.error);
                    btn.disabled = false;
                    rejectBtn.disabled = false;
                    btn.innerHTML = '<i class="ri-checkbox-circle-line"></i> Accept & Apply Changes (Save DB)';
                }
            } catch (err) {
                alert('Connection error: ' + err.message);
                btn.disabled = false;
                rejectBtn.disabled = false;
                btn.innerHTML = '<i class="ri-checkbox-circle-line"></i> Accept & Apply Changes (Save DB)';
            }
        }

        async function discardChanges() {
            const btn = document.getElementById('btnAccept');
            const rejectBtn = document.getElementById('btnReject');
            btn.disabled = true;
            rejectBtn.disabled = true;
            rejectBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Discarding...';

            try {
                const response = await fetch('/discard', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    document.getElementById('statusMessage').textContent = '❌ Discarded: Pending changes have been cleared. Database was NOT modified.';
                    rejectBtn.innerHTML = '<i class="ri-close-line"></i> Discarded';
                } else {
                    alert('Error discarding changes: ' + result.error);
                    btn.disabled = false;
                    rejectBtn.disabled = false;
                    rejectBtn.innerHTML = '<i class="ri-close-circle-line"></i> Reject & Discard Changes';
                }
            } catch (err) {
                alert('Connection error: ' + err.message);
                btn.disabled = false;
                rejectBtn.disabled = false;
                rejectBtn.innerHTML = '<i class="ri-close-circle-line"></i> Reject & Discard Changes';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    global pending_db, pending_subject, pending_target
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    subject = request.form.get('subject')
    target = request.form.get('examTarget')
    multiplier_mode = request.form.get('multiplier')
    update_cumulative = request.form.get('updateCumulative') in ('true', 'on')
    mark_pos = request.form.get('markPos', 'last')

    if not subject or not target:
        return jsonify({'success': False, 'error': 'Missing subject or target parameter'})

    # 1. Resolve keys
    if subject not in SUBJECT_KEYS:
        return jsonify({'success': False, 'error': 'Invalid subject'})
    
    if target not in SUBJECT_KEYS[subject]:
        return jsonify({'success': False, 'error': f'Exam target "{target}" is not supported for subject "{subject}"'})
    
    target_key = SUBJECT_KEYS[subject][target]
    cumulative_key = SUBJECT_KEYS[subject]['overall']

    # 2. Save PDF temporarily
    temp_pdf_path = 'temp_uploaded_marksheet.pdf'
    file.save(temp_pdf_path)

    # 3. Parse PDF
    pdf_records = {}
    try:
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.splitlines():
                    line = line.strip()
                    enroll_match = re.search(r'\b(2\d{13})\b', line)
                    if enroll_match:
                        enroll = enroll_match.group(1)
                        
                        idx = line.find(enroll)
                        after_enroll = line[idx + len(enroll):].strip()
                        tokens = after_enroll.split()
                        
                        scores = []
                        for t in tokens:
                            t_clean = t.strip().upper()
                            if t_clean in ('AB', 'ABS', 'UFM', 'PENDING', 'FEES PENDING', '-'):
                                scores.append(0.0)
                            else:
                                t_clean = re.sub(r'[^\d\.]', '', t_clean)
                                if t_clean and t_clean.replace('.', '', 1).isdigit():
                                    scores.append(float(t_clean))
                        
                        if scores:
                            if mark_pos == 'last':
                                mark_val = scores[-1]
                            elif mark_pos == 'first':
                                mark_val = scores[0]
                            elif mark_pos == 'second' and len(scores) > 1:
                                mark_val = scores[1]
                            else:
                                mark_val = scores[-1]
                            
                            pdf_records[enroll] = mark_val
    except Exception as e:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return jsonify({'success': False, 'error': f'Failed to parse PDF: {str(e)}'})

    if os.path.exists(temp_pdf_path):
        os.remove(temp_pdf_path)

    if not pdf_records:
        return jsonify({'success': False, 'error': 'No student records (14-digit enrollment numbers starting with 2) found in the PDF.'})

    # 4. Load JS Database
    try:
        with open(JS_PATH, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        start_idx = js_content.find('[')
        end_idx = js_content.rfind(']') + 1
        if start_idx == -1 or end_idx == 0:
            return jsonify({'success': False, 'error': 'Could not parse database array in new_datamarksheet.js'})
        
        json_str = js_content[start_idx:end_idx]
        data = json.loads(json_str)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to load database: {str(e)}'})

    # 5. Update data in memory
    updated_count = 0
    all_logs = []
    
    for s in data:
        enroll = s.get('enrollment')
        is_in_pdf = enroll in pdf_records
        
        if is_in_pdf:
            pdf_val = pdf_records[enroll]
        else:
            pdf_val = 0.0  # Treat missing students as absent (0.0 marks)
            
        old_val = s.get(target_key, 0.0) or 0.0
        old_cumulative = s.get(cumulative_key, 0.0) or 0.0
        
        if multiplier_mode == 'overwrite':
            new_val = pdf_val
            s[target_key] = new_val
            if update_cumulative and target != 'overall':
                diff = new_val - old_val
                s[cumulative_key] = round((s.get(cumulative_key, 0.0) or 0.0) + diff, 2)
        else:
            mult = float(multiplier_mode)
            if target == 'overall':
                calculated_change = pdf_val * mult
                new_val = old_val + calculated_change
                s[target_key] = round(new_val, 2)
            else:
                new_val = pdf_val
                s[target_key] = new_val
                if update_cumulative:
                    # Calculate change based on the difference of new and old exam scores to keep it idempotent
                    calculated_change = (pdf_val - old_val) * mult
                    s[cumulative_key] = round((s.get(cumulative_key, 0.0) or 0.0) + calculated_change, 2)
        
        # Recalculate totals
        dm = s.get('dm', 0.0) or 0.0
        coa = s.get('coa', 0.0) or 0.0
        fsd2 = s.get('fsd2', 0.0) or s.get('fsd-ii', 0.0) or 0.0
        python2 = s.get('python2', 0.0) or 0.0
        toc = s.get('toc', 0.0) or 0.0
        s['total'] = round(dm + coa + fsd2 + python2 + toc, 2)
        
        new_cumulative = s.get(cumulative_key, 0.0) or 0.0
        cum_delta = round(new_cumulative - old_cumulative, 2)
        
        # Only log students who were actually present in the PDF or had a change in marks
        if is_in_pdf or new_val != old_val or cum_delta != 0.0:
            updated_count += 1
            all_logs.append({
                'roll': s.get('roll'),
                'enrollment': enroll,
                'name': s.get('name'),
                'old_exam': old_val,
                'new_exam': new_val,
                'old_cumulative': old_cumulative,
                'new_cumulative': new_cumulative,
                'cumulative_delta': cum_delta
            })

    # Search for Daksh Bhavsar in all logs
    daksh_log = None
    for log in all_logs:
        if log['enrollment'] == '24002171410007' or ('DAKSH' in log['name'].upper() and 'BHAVSAR' in log['name'].upper()):
            daksh_log = log
            break

    # Save to global pending variables
    pending_db = data
    pending_subject = subject
    pending_target = target

    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'target_key': target_key,
        'daksh_log': daksh_log,
        'sample_logs': all_logs[:50]
    })

HTML_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\28.html'

def bump_html_version():
    if not os.path.exists(HTML_PATH):
        return None
    try:
        with open(HTML_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'(<script src="new_datamarksheet\.js\?v=)(\d+)("></script>)'
        match = re.search(pattern, content)
        if match:
            prefix = match.group(1)
            current_version = int(match.group(2))
            suffix = match.group(3)
            
            new_version = current_version + 1
            new_tag = f"{prefix}{new_version}{suffix}"
            
            updated_content = content.replace(match.group(0), new_tag)
            with open(HTML_PATH, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return new_version
    except Exception as e:
        print(f"Error bumping HTML version: {e}")
    return None

@app.route('/confirm', methods=['POST'])
def confirm_changes():
    global pending_db, pending_subject, pending_target
    if pending_db is None:
        return jsonify({'success': False, 'error': 'No pending changes to confirm.'})
    
    try:
        # 1. Create backup file
        backup_filename = f"{JS_PATH}.{pending_subject}_{pending_target}.bak"
        if os.path.exists(JS_PATH):
            import shutil
            shutil.copy2(JS_PATH, backup_filename)
        
        # 2. Write database content
        new_content = 'const data = ' + json.dumps(pending_db, indent=2, ensure_ascii=False) + ';\n'
        with open(JS_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        # 2b. Bump version in 28.html to bust GitHub Pages cache
        new_ver = bump_html_version()
            
        # 3. Automatic Git Add and Commit (include 28.html)
        commit_message = f"Upload and integrate {pending_subject.upper()} {pending_target.upper()} compiled marksheet"
        if new_ver:
            commit_message += f" (Bust cache to v{new_ver})"
            
        import subprocess
        try:
            # git add both files
            subprocess.run(["git", "add", JS_PATH, HTML_PATH], check=True, capture_output=True)
            # git commit
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
            commit_done = True
            warning_msg = None
        except subprocess.CalledProcessError as ge:
            commit_done = False
            warning_msg = f"Database updated & backup created, but Git commit skipped: {ge.stderr.decode('utf-8', errors='ignore').strip()}"
            
        # Reset state
        pending_db = None
        pending_subject = ""
        pending_target = ""
        
        return jsonify({
            'success': True,
            'backup_created': os.path.basename(backup_filename),
            'commit_done': commit_done,
            'commit_message': commit_message,
            'warning': warning_msg
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to write updated database/backup: {str(e)}'})

@app.route('/discard', methods=['POST'])
def discard_changes():
    global pending_db, pending_subject, pending_target
    pending_db = None
    pending_subject = ""
    pending_target = ""
    return jsonify({'success': True})

def start_server():
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    print("Starting LJ University Admin Server on http://127.0.0.1:5000...")
    threading.Timer(1.5, lambda: webbrowser.open_new("http://127.0.0.1:5000")).start()
    start_server()
