import os
from flask import Flask, flash, request, render_template, redirect, url_for, session, jsonify
import pandas as pd
 
app = Flask(__name__)
app.secret_key = '07022003'
 
# Load data from Excel file
file_path = 'Datasets/Master.xlsx'
xls = pd.ExcelFile(file_path)
sheet1_data = pd.read_excel(xls, sheet_name='Sheet1')
cleaned_programmes_data = pd.read_excel(xls, sheet_name='Cleaned_Programmes')
bachelor_scholarships_data = pd.read_excel(xls, sheet_name='BachScholar')
bachelor_programmes_data = pd.read_excel(xls, sheet_name='BachProgram')
 
# Helper function to match GPA ranges
def gpa_matches(gpa_range, user_gpa):
    try:
        # Convert the user GPA to float (if it's a valid number)
        user_gpa = float(user_gpa)
    except ValueError:
        # If conversion fails, return False or handle the error appropriately
        return False
    
    # Handle the case where gpa_range is a string that needs to be split into min/max GPA
    if isinstance(gpa_range, str):
        # Assuming the range is a string like "3.0-4.0"
        gpa_range = gpa_range.split('-')
    
    try:
        # Convert the range values to float
        min_gpa = float(gpa_range[0])
        max_gpa = float(gpa_range[1])
    except ValueError:
        # If there's an issue with the GPA range format, return False
        return False
    
    # Return True if the user's GPA is within the range, else False
    return min_gpa <= user_gpa <= max_gpa

profile_file_path = os.path.join('Datasets', 'profile.xlsx')
 
# Initialize the file if it doesn't exist
if not os.path.exists(profile_file_path):
    initial_data = pd.DataFrame(columns=["First Name", "Last Name", "Username", "Email", "Password"])
    initial_data.to_excel(profile_file_path, index=False)
 
 
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if session already contains email and username
    if 'email' in session and 'username' in session:
        print(f"Session exists: {session['email']}, {session['username']}")
        return render_template('search.html', username=session['username'])

    if request.method == 'POST':
        email = request.form['email'].strip()  # Strip leading/trailing spaces
        password = request.form['password'].strip()  # Strip leading/trailing spaces

        # Load the Excel file
        try:
            df = pd.read_excel(profile_file_path)
        except FileNotFoundError:
            flash("User data file not found. Please contact support.", "error")
            return render_template('login.html')

        # Ensure 'Email' and 'Password' are stripped for comparison
        df['Email'] = df['Email'].astype(str).str.strip()
        df['Password'] = df['Password'].astype(str).str.strip()

        # Check if email and password match
        user = df[(df['Email'] == email) & (df['Password'] == password)]
        print(f"User found: {user}")

        if not user.empty:
            username = user.iloc[0]['Username']  # Extract username from the dataframe
            print(f"Username extracted: {username}")
            
            # Store email and username in session
            session['email'] = email
            session['username'] = username
            print(f"Session stored: {session}")

            flash("Login successful!", "success")
            return render_template('search.html', username=username)  # Pass username to the template
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template('login.html')

    return render_template('login.html')

 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data and strip leading/trailing spaces
        first_name = request.form.get('first_name').strip()  # Strip spaces
        last_name = request.form.get('last_name').strip()  # Strip spaces
        username = request.form.get('username').strip()  # Strip spaces
        email = request.form.get('email').strip()  # Strip spaces
        password = request.form.get('password').strip()  # Strip spaces
        confirm_password = request.form.get('confirm_password').strip()  # Strip spaces
 
        # Load existing data
        profiles_data = pd.read_excel(profile_file_path)
 
        # Validation: Check if email is already registered
        if email in profiles_data['Email'].values:
            flash('This email is already registered. Please use a different email.', 'error')
            return render_template('signup.html')
 
        # Validation: Check if password and confirm_password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('signup.html')
 
        # Append new data
        new_profile = {
            "First Name": first_name,
            "Last Name": last_name,
            "Username": username,
            "Email": email,
            "Password": password
        }
        new_profile_df = pd.DataFrame([new_profile])
        profiles_data = pd.concat([profiles_data, new_profile_df], ignore_index=True)
 
        # Save to Excel
        profiles_data.to_excel(profile_file_path, index=False)
 
        # Store email and username in session
        session['email'] = email
        session['username'] = username
 
        # Flash success message and redirect to search page
        flash('Registration successful! Please proceed to search.', 'success')
 
        # Redirect to search page with the username as a query parameter
        return redirect(url_for('search', username=username))
 
    return render_template('signup.html')
 
 
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Extract form data
        user_country = request.form.getlist('countrySelect')
        user_gpa = request.form.get('gpa')
        user_programme = request.form.get('programInput')
        user_degree = request.form.get('degreeSelect', '').strip()

        # Store the data into the session
        session['user_country'] = user_country
        session['user_gpa'] = user_gpa
        session['user_programme'] = user_programme
        session['user_degree'] = user_degree

        # Redirect with query parameters
        return redirect(url_for('show_programmes',
                                country=user_country,
                                gpa=user_gpa,
                                programme=user_programme,
                                degree=user_degree))

    return render_template('search.html')


 
@app.route('/show_programmes', methods=['GET', 'POST'])
def show_programmes():
    # Check if it's a GET request (e.g., link navigation)
    if request.method == 'GET':
        # Load session or query parameters
        user_country = session.get('user_country', [])
        user_gpa = session.get('user_gpa', None)
        user_programme = session.get('user_programme', '')
        user_degree = session.get('user_degree', '').lower()

        # Handle cases where session data might be missing
        if not user_country or not user_degree:
            flash("Missing search criteria. Please perform a search first.", "error")
            return redirect(url_for('search'))

    elif request.method == 'POST':
        # Handle POST data
        user_country = request.form.getlist('countrySelect')
        user_gpa = request.form.get('gpa')
        user_programme = request.form.get('programInput')
        user_degree = request.form.get('degreeSelect')
        session['user_country'] = user_country
        session['user_gpa'] = user_gpa
        session['user_programme'] = user_programme
        session['user_degree'] = user_degree

    # Ensure `user_programme` is a string
    user_programme = str(user_programme) if user_programme else ""

    # Filtering logic (reused from your original code)
    def gpa_matches(row_gpa, user_gpa):
        try:
            gpa_range = row_gpa.split('-')
            if len(gpa_range) == 2:
                min_gpa = float(gpa_range[0].strip())
                max_gpa = float(gpa_range[1].strip())
                return min_gpa <= float(user_gpa) <= max_gpa
            return False
        except Exception:
            return False

    def debug_filtering(data, user_country, user_gpa=None):
        # Same filtering logic from your original code
        location_filtered = data[
            data['Location'].str.contains('|'.join(user_country), case=False, na=False)
        ]
        if user_gpa:
            location_filtered = location_filtered[
                location_filtered['Acceptable GPA for Merit-based Scholarships']
                .apply(lambda x: gpa_matches(x, user_gpa))
            ]
        return location_filtered

    if user_degree == 'bachelor':
        filtered_scholarships = debug_filtering(bachelor_scholarships_data, user_country, user_gpa)
        filtered_programmes = bachelor_programmes_data[
            (bachelor_programmes_data['Organization Location'].str.contains('|'.join(user_country), case=False, na=False)) &
            (bachelor_programmes_data['Programme'].str.contains(user_programme, case=False, na=False))
        ]
    else:
        filtered_scholarships = debug_filtering(sheet1_data, user_country, user_gpa)
        filtered_programmes = cleaned_programmes_data[
            (cleaned_programmes_data['Organization Location'].str.contains('|'.join(user_country), case=False, na=False)) &
            (cleaned_programmes_data['Programme'].str.contains(user_programme, case=False, na=False))
        ]

    return render_template(
        'programmes.html',
        scholarships=filtered_scholarships.to_dict(orient='records'),
        programmes=filtered_programmes.to_dict(orient='records'),
        selected_countries=user_country,
        selected_degree=user_degree
    )


@app.route('/filter_programmes', methods=['POST'])
def filter_programmes():
    data = request.get_json()
    print("Received data from client (filter_programmes):", data)
 
    # Extract data from the request
    selected_countries = data.get('countries', [])
    selected_grant = data.get('grant', [])
    selected_deadline = data.get('deadline', [])
    selected_degree = data.get('degree', '')
 
    # Determine the dataset to use based on the degree type
    if selected_degree.lower() == 'bachelors':
        filtered_scholarships = bachelor_scholarships_data
    else:
        filtered_scholarships = sheet1_data
 
    print("Selected countries:", selected_countries)
    print("Selected grant:", selected_grant)
    print("Selected deadline:", selected_deadline)
    print("Selected degree:", selected_degree)
    print("Initial data count:", len(filtered_scholarships))
 
    # Apply location filter
    if selected_countries:
        def location_matches(loc):
            return any(country.lower() in loc.lower() for country in selected_countries)
        filtered_scholarships = filtered_scholarships[filtered_scholarships['Location'].apply(location_matches)]
        print("Data count after location filter:", len(filtered_scholarships))
   
 
    # Apply grant filter
    if 'various-benefits' in selected_grant:
        filtered_scholarships = filtered_scholarships[filtered_scholarships['Grant'] == 'Various benefits']
        print("Data count after grant filter (various-benefits):", len(filtered_scholarships))
    elif 'specific-grant' in selected_grant:
        filtered_scholarships = filtered_scholarships[filtered_scholarships['Grant'] != 'Various benefits']
        print("Data count after grant filter (specific-grant):", len(filtered_scholarships))
 
   
 
    # Apply deadline filter
    if 'anytime' in selected_deadline:
        filtered_scholarships = filtered_scholarships[filtered_scholarships['Deadline'] == 'Anytime']
        print("Data count after deadline filter (anytime):", len(filtered_scholarships))
    if 'not-specified' in selected_deadline:
        filtered_scholarships = filtered_scholarships[filtered_scholarships['Deadline'] == 'Not specified']
        print("Data count after deadline filter (not-specified):", len(filtered_scholarships))
    if 'specific-deadline' in selected_deadline:
        filtered_scholarships = filtered_scholarships[
        (filtered_scholarships['Deadline'] != 'Anytime') &
        (filtered_scholarships['Deadline'] != 'Not specified')
    ]
    print("Data count after deadline filter (specific-deadline):", len(filtered_scholarships))
 
 
 
   
 
    response = jsonify({
        "scholarships": filtered_scholarships.to_dict(orient='records'),
     
    })
 
    return response
 
 
@app.route('/university', methods=['GET', 'POST'])
def show_university():
    user_country = session.get('user_country', [])
    user_programme = session.get('user_programme', '')
    user_degree = session.get('user_degree', '').lower()


    print(user_degree)
 
    # Select relevant data
    if user_degree == 'bachelor':
        matching_programmes = bachelor_programmes_data[
            (bachelor_programmes_data['Organization Location'].apply(lambda loc: any(country.lower() in loc.lower() for country in user_country))) &
            (bachelor_programmes_data['Programme'].str.contains(user_programme, case=False))
        ]
    else:
        matching_programmes = cleaned_programmes_data[
            (cleaned_programmes_data['Organization Location'].apply(lambda loc: any(country.lower() in loc.lower() for country in user_country))) &
            (cleaned_programmes_data['Programme'].str.contains(user_programme, case=False)) &
            (cleaned_programmes_data['Degree Level'].str.lower() == user_degree)
        ]
 
    # Handle no results
    if matching_programmes.empty:
        return render_template('result.html', message="No matching programmes found.")
 
    return render_template('university.html',
                           programmes=matching_programmes.to_dict(orient='records'),
                           selected_countries=user_country,
                           selected_degree=user_degree,
                           selected_program=user_programme)
 
@app.route('/filter_universities', methods=['POST'])
def filter_universities():
    data = request.get_json()
    print("Received data: ", data)
 
    # Extract filters from the request
    selected_countries = data.get('countries', [])
    selected_degree = data.get('degree', '')
    selected_programs = data.get('programs', [])
 
    # Determine dataset based on degree type
    if selected_degree.lower() == 'bachelors':
        filtered_universities = bachelor_programmes_data
    else:
        filtered_universities = cleaned_programmes_data
 
    print("Initial dataset size: ", len(filtered_universities))
 
    # Apply country filter
    if selected_countries:
        def location_matches(location):
            return any(country.lower() in location.lower() for country in selected_countries)
 
        filtered_universities = filtered_universities[
            filtered_universities['Organization Location'].apply(location_matches)
        ]
        print("Dataset size after country filter: ", len(filtered_universities))
 
    # Apply program filter
    if selected_programs:
        filtered_universities = filtered_universities[
            filtered_universities['Programme'].isin(selected_programs)
        ]
        print("Dataset size after program filter: ", len(filtered_universities))
 
    # Extract unique programs for the frontend
    unique_programs = filtered_universities['Programme'].drop_duplicates().tolist()
    print("Number of unique programs: ", len(unique_programs))
    print(unique_programs)
 
    # Prepare JSON response
    response = {
        "universities": filtered_universities.to_dict(orient='records'),
        "programs": unique_programs,
    }
 
    return jsonify(response)
 
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if the user is logged in by verifying the session
    if 'email' not in session:
        flash("You need to log in first.", "error")
        return redirect(url_for('login'))
 
    # Retrieve the email from the session
    email = session.get('email')
 
    # Load the Excel file
    try:
        df = pd.read_excel(profile_file_path)
    except FileNotFoundError:
        flash("User data file not found. Please contact support.", "error")
        return redirect(url_for('login'))
 
    # Ensure 'Email' column is stripped of spaces for comparison
    df['Email'] = df['Email'].astype(str).str.strip()
 
    # Find the user in the dataframe (assuming email is unique)
    user = df[df['Email'] == email]
 
    if user.empty:
        flash("User not found.", "error")
        return redirect(url_for('login'))  # Redirect to login if user not found
 
    # Extract user data for pre-populating the form
    first_name = user.iloc[0]['First Name']
    last_name = user.iloc[0]['Last Name']
    username = user.iloc[0]['Username']
    password = user.iloc[0]['Password']
 
    if request.method == 'POST':
        # Get the updated data from the form
        updated_first_name = request.form.get('first_name')
        updated_last_name = request.form.get('last_name')
        updated_username = request.form.get('username')
        updated_email = request.form.get('email')
        updated_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
 
        # Print data to check what is being retrieved
        print(f"Updated First Name: {updated_first_name}")
        print(f"Updated Last Name: {updated_last_name}")
        print(f"Updated Username: {updated_username}")
        print(f"Updated Email: {updated_email}")
        print(f"Updated Password: {updated_password}")
        print(f"Confirm Password: {confirm_password}")
 
        # If email doesn't change, ensure email remains from session
        if updated_email != email:
            flash('Email cannot be changed.', 'error')
            return redirect(url_for('profile'))
 
        # If password and confirm password match, update the profile
        if updated_password == confirm_password:
            # Update the user's details in the DataFrame
            df.loc[df['Email'] == email, 'First Name'] = updated_first_name
            df.loc[df['Email'] == email, 'Last Name'] = updated_last_name
            df.loc[df['Email'] == email, 'Username'] = updated_username
            df.loc[df['Email'] == email, 'Password'] = updated_password
 
            # Save the updated data to the Excel file
            try:
                df.to_excel(profile_file_path, index=False)
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                flash(f"Error saving file: {e}", 'error')
                print(f"Error saving Excel file: {e}")
 
            return redirect(url_for('profile'))  # Redirect to the same profile page
 
        else:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('profile'))
 
    # Pass the user data to the template for pre-population of the form
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
        'email': email,
        'password': password
    }
 
    return render_template('profile.html', user=user_data)
 
 
if __name__ == '__main__':
    app.run(debug=True)