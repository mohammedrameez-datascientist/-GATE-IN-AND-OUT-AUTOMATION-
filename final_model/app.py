from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

import ssl

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Replace with your actual username and password
uri = "mongodb+srv://rahulprakashlatha:jNPAVYjYAkZ16RTv@cluster0.kuyesmp.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Example: Access a collection
db = client['ssec_gate_attendance']
staff_collection = db['staff']
gate_records_collection = db['gate_records']
gate_staff_collection = db['gate_staff']
gate_student_collection = db['gate_student']

# Department-specific student collections
student_aiml_collection = db['Student_aiml']
student_cse_collection = db['Student_cse']
student_ece_collection = db['Student_ece']
student_eee_collection = db['Student_eee']
student_it_collection = db['Student_IT']
student_aids_collection = db['Student_aids']
student_cyber_collection = db['Student_cyber']
student_mech_collection = db['Student_mech']
student_civil_collection = db['Student_civil']

# Department mapping for easy lookup
department_collections = {
    'AIML': student_aiml_collection,
    'CSE': student_cse_collection,
    'ECE': student_ece_collection,
    'EEE': student_eee_collection,
    'IT': student_it_collection,
    'AIDS': student_aids_collection,
    'CYBERSECURITY': student_cyber_collection,
    'MECH': student_mech_collection,
    'CIVIL': student_civil_collection
}

# Initialize collections with existing data if needed
def initialize_collections():
    # Check if staff collection is empty
    if staff_collection.count_documents({}) == 0:
        try:
            staff_collection.insert_one({
                "id": "admin",
                "name": "Admin",
                "department": "Admin",
                "role": "admin"
            })
        except Exception as e:
            print("Error initializing staff collection:", e)

    # Check if gate_records collection is empty
    if gate_records_collection.count_documents({}) == 0:
        try:
            gate_records_collection.insert_one({
                "staff_id": "admin",
                "name": "Admin",
                "department": "Admin",
                "role": "admin",
                "entry_time": datetime.now().isoformat(),
                "exit_time": None
            })
        except Exception as e:
            print("Error initializing gate_records collection:", e)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Admin login
        if username == "admin" and password == "adminpass":
            session.clear()
            session['admin'] = True
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "success", "redirect": url_for('admin_dashboard')})
            return redirect(url_for('admin_dashboard'))

        # Management login
        if username == "management" and password == "managementpass":
            session.clear()
            session['management'] = True
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "success", "redirect": url_for('management_dashboard')})
            return redirect(url_for('management_dashboard'))

        # Gate login
        if username == "gate" and password == "gatepass":
            session.clear()
            session['gate'] = True
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "success", "redirect": url_for('gate_dashboard')})
            return redirect(url_for('gate_dashboard'))

        # Invalid credentials
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "fail"})
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    staff_list = list(staff_collection.find({}, {'_id': 0}))
    return render_template('admin.html', staff=staff_list)

@app.route('/management')
def management_dashboard():
    if 'management' not in session:
        return redirect(url_for('login'))
    staff_list = list(staff_collection.find({}, {'_id': 0}))
    return render_template('management.html', staff=staff_list)

@app.route('/gate')
def gate_dashboard():
    if 'gate' not in session:
        return redirect(url_for('login'))
    return render_template('gate.html')

@app.route('/api/staff', methods=['GET'])
def get_staff():
    staff = list(staff_collection.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
    return jsonify(staff)

@app.route('/api/staff', methods=['POST'])
def api_add_staff():
    data = request.get_json()
    staff_id = data.get('id')
    staff_name = data.get('name')
    staff_dept = data.get('department')
    staff_role = data.get('role')
    
    if not staff_id or not staff_name or not staff_dept or not staff_role:
        return jsonify({"error": "Missing fields"}), 400

    # Check if staff ID already exists
    if staff_collection.find_one({'id': staff_id}):
        return jsonify({"error": "Staff ID already exists"}), 400

    try:
        staff_collection.insert_one({
            "id": staff_id,
            "name": staff_name,
            "department": staff_dept,
            "role": staff_role
        })
        return jsonify({"message": "Staff added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/staff/<staff_id>', methods=['DELETE'])
def api_delete_staff(staff_id):
    try:
        result = staff_collection.delete_one({"id": staff_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Staff not found"}), 404
        return jsonify({"message": "Staff deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/staff/<staff_id>', methods=['PUT'])
def api_edit_staff(staff_id):
    data = request.get_json()
    name = data.get('name')
    department = data.get('department')
    role = data.get('role')
    
    try:
        result = staff_collection.update_one(
            {'id': staff_id},
            {'$set': {"name": name, "department": department, "role": role}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Staff not found"}), 404
        return jsonify({"message": "Staff updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/gate/entry', methods=['POST'])
def gate_entry():
    data = request.get_json()
    staff_id = data.get('staff_id')
    name = data.get('name')
    department = data.get('department')
    role = data.get('role')
    entry_time = datetime.now().isoformat()
    
    # Check staff first
    staff = staff_collection.find_one({'id': staff_id})
    if staff:
        name = staff.get('name')
        department = staff.get('department')
        role = staff.get('role')
        display_id = staff_id
    else:
        # Check all department collections for students
        student_found = None
        for dept_name, collection in department_collections.items():
            student = collection.find_one({'Barcode ID': staff_id})
            if student:
                student_found = student
                department = dept_name
                break
        
        if student_found:
            name = student_found.get('Name')
            role = 'student'
            display_id = student_found.get('Barcode ID')
        else:
            return jsonify({"success": False, "error": "ID not found"}), 404
    
    record = {
        "staff_id": staff_id,
        "name": name,
        "department": department,
        "role": role,
        "entry_time": entry_time,
        "exit_time": None
    }
    try:
        # Store in main gate_records collection
        gate_records_collection.insert_one(record)
        
        # Also store in role-specific collection
        if role == 'student':
            gate_student_collection.insert_one(record)
        else:
            gate_staff_collection.insert_one(record)
            
        return jsonify({"success": True, "message": f"IN registered for {name} ({display_id})"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/gate/exit', methods=['POST'])
def gate_exit():
    data = request.get_json()
    staff_id = data.get('staff_id')
    exit_time = datetime.now().isoformat()
    
    # Check staff first
    staff = staff_collection.find_one({'id': staff_id})
    if staff:
        # Staff found, proceed with exit
        pass
    else:
        # Check all department collections for students
        student_found = False
        for dept_name, collection in department_collections.items():
            student = collection.find_one({'Barcode ID': staff_id})
            if student:
                student_found = True
                break
        
        if not student_found:
            return jsonify({"success": False, "error": "ID not found"}), 404
    
    try:
        # Update in main gate_records collection
        result = gate_records_collection.update_one(
            {"staff_id": staff_id, "exit_time": None}, 
            {"$set": {"exit_time": exit_time}}
        )
        
        # Also update in role-specific collections
        staff_update = gate_staff_collection.update_one(
            {"staff_id": staff_id, "exit_time": None}, 
            {"$set": {"exit_time": exit_time}}
        )
        student_update = gate_student_collection.update_one(
            {"staff_id": staff_id, "exit_time": None}, 
            {"$set": {"exit_time": exit_time}}
        )
        
        if result.matched_count == 0 and staff_update.matched_count == 0 and student_update.matched_count == 0:
            return jsonify({"success": False, "error": "No active entry found"}), 404
        return jsonify({"success": True, "message": "Exit recorded"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/gate/records', methods=['GET'])
def get_gate_records():
    try:
        records = list(gate_records_collection.find({}, {'_id': 0}))
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/gate/records/weekly', methods=['GET'])
def get_weekly_gate_records():
    try:
        one_week_ago = datetime.now() - timedelta(days=7)
        records = list(gate_records_collection.find(
            {"entry_time": {"$gte": one_week_ago.isoformat()}},
            {'_id': 0}
        ))
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students')
def get_all_students():
    students = []
    # Fetch students from all department collections
    for dept_name, collection in department_collections.items():
        for s in collection.find():
            students.append({
                "id": s.get("Barcode ID", ""),
                "name": s.get("Name", ""),
                "year": s.get("Year", ""),
                "department": s.get("Department", "")
            })
    return jsonify(students)

@app.route('/api/students/aiml', methods=['GET'])
def get_aiml_students():
    students = []
    for s in student_aiml_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/cse', methods=['GET'])
def get_cse_students():
    students = []
    for s in student_cse_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/ece', methods=['GET'])
def get_ece_students():
    students = []
    for s in student_ece_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/eee', methods=['GET'])
def get_eee_students():
    students = []
    for s in student_eee_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/it', methods=['GET'])
def get_it_students():
    students = []
    for s in student_it_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/aids', methods=['GET'])
def get_aids_students():
    students = []
    for s in student_aids_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/cyber', methods=['GET'])
def get_cyber_students():
    students = []
    for s in student_cyber_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/mech', methods=['GET'])
def get_mech_students():
    students = []
    for s in student_mech_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/api/students/civil', methods=['GET'])
def get_civil_students():
    students = []
    for s in student_civil_collection.find():
        students.append({
            "id": s.get("Barcode ID", ""),
            "name": s.get("Name", ""),
            "year": s.get("Year", ""),
            "department": s.get("Department", "")
        })
    return jsonify(students)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def prune_old_records():
    try:
        one_month_ago = datetime.now() - timedelta(days=30)
        # Clean all gate record collections
        gate_records_collection.delete_many(
            {"entry_time": {"$lt": one_month_ago.isoformat()}}
        )
        gate_staff_collection.delete_many(
            {"entry_time": {"$lt": one_month_ago.isoformat()}}
        )
        gate_student_collection.delete_many(
            {"entry_time": {"$lt": one_month_ago.isoformat()}}
        )
    except Exception as e:
        print("Error pruning old records:", e)

@app.route('/api/gate/records/staff', methods=['GET'])
def get_staff_gate_records():
    try:
        # Get staff records from gate_staff collection
        records = list(gate_staff_collection.find({}, {'_id': 0}))
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gate/records/students', methods=['GET'])
def get_student_gate_records():
    try:
        # Get student records from gate_student collection
        records = list(gate_student_collection.find({}, {'_id': 0}))
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gate/records/staff/stats/today', methods=['GET'])
def staff_gate_stats_today():
    from datetime import datetime
    today = datetime.now().date().isoformat()
    try:
        # Get staff records from gate_staff collection for today
        query = {
            'entry_time': {'$regex': f'^{today}'}
        }
        records = list(gate_staff_collection.find(query, {'_id': 0}))
        total_entries = len(records)
        total_exits = sum(1 for r in records if r.get('exit_time'))
        current_inside = total_entries - total_exits
        return jsonify({
            'current_inside': current_inside,
            'total_entries': total_entries,
            'total_exits': total_exits
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student', methods=['POST'])
def api_add_student():
    data = request.get_json()
    name = data.get('name')
    roll_no = data.get('roll_no')
    year = data.get('year')
    department = data.get('department')
    
    if not name or not roll_no or not year or not department:
        return jsonify({"error": "Missing fields"}), 400
    
    # Normalize department name for lookup
    dept_upper = department.upper().replace(' ', '')
    if dept_upper == 'CYBERSECURITY':
        dept_upper = 'CYBERSECURITY'
    
    # Check if department is supported
    if dept_upper not in department_collections:
        return jsonify({"error": f"Unsupported department: {department}"}), 400
    
    # Get the correct collection for this department
    target_collection = department_collections[dept_upper]
    
    # Check if student already exists in the target collection
    if target_collection.find_one({'Barcode ID': roll_no}):
        return jsonify({"error": "Student already exists"}), 400
    
    try:
        target_collection.insert_one({
            "Barcode ID": roll_no,
            "Name": name,
            "Year": year,
            "Department": department
        })
        return jsonify({"message": "Student added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/student/<roll_no>', methods=['DELETE'])
def api_delete_student(roll_no):
    try:
        # Check all department collections for the student
        deleted = False
        for dept_name, collection in department_collections.items():
            result = collection.delete_one({"Barcode ID": roll_no})
            if result.deleted_count > 0:
                deleted = True
                break
        
        if not deleted:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"message": "Student deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    initialize_collections()
    prune_old_records()
    print("Starting Flask app...")
    app.run(debug=True)