import streamlit as st  
import database as db 
from datetime import date
import pdfkit
import psycopg2

config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

def generate_case_report(case_id, username):
    # Connect to the database
    conn = db.connect_db() 

    # Fetch case details from the database
    case_details = db.from_db(conn,f"Select * from casereports where caseid='{case_id}'")

    # Fetch investigator details from the database
    conn = db.connect_db() 
    investigator_details = db.get_all(conn,f"""SELECT name, contact FROM officer_record WHERE id in 
                                      (select officer_id from officer_and_cases where case_id='{case_id}' and status='ongoing' and enrollment='active')""")
    conn = db.connect_db() 
    prev_investigator_details = db.get_all(conn,f"""SELECT name, contact FROM officer_record WHERE id in 
                                      (select officer_id from officer_and_cases where case_id='{case_id}' and enrollment='archive' or enrollment='revised')""")
    # Fetch victim and suspect details from the database
    conn = db.connect_db() 
    victim_details = db.get_all(conn,f"""SELECT name, contact, address FROM victims WHERE caseid='{case_id}'""")

    conn = db.connect_db() 
    suspect_details = db.get_all(conn,f"""SELECT name, contact,address FROM suspects WHERE caseid='{case_id}'""")

    # Fetch evidence details from the database
    conn = db.connect_db() 
    evidence_details = db.get_all(conn,f"""SELECT name, description FROM evidence WHERE case_id='{case_id}'""")

    # Fetch case timeline from the database
    conn=db.connect_db() 
    fetched_timeline = db.fetch_data(conn, table_name='case_timeline', 
                                     check_attributes=f"caseid='{case_id}'", 
                                     fetch_attributes='date,activity', 
                                     add='order by date ASC', 
                                     data='all')

    # Extract case details
    case_no, case_status, nature_of_case, description, recorded_date, case_date = case_details[0], case_details[8], case_details[3], case_details[4], case_details[7],case_details[2]

    # Generate HTML for case report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>

    </head>
    <body>
        <div class="header">
                <h2>Case Report</h2>
                <p>Case ID: {case_details[1]}</p>
                <p>Date: {date.today()}</p>
                <p>User: {username}</p>
        </div>

        <!-- Case Overview section -->
        <div class="case-overview">
            <h3>Case Overview</h3>
            <hr>
            <p><strong>Case No:</strong> {case_no}</p>
            <p><strong>Case Status:</strong> {case_status}</p>
            <p><strong>Nature of Case:</strong> {nature_of_case}</p>
            <p><strong>Description:</strong> {description}</p>
            <p><strong>Event Date:</strong> {case_date}</p>
            <p><strong>Recorded Date:</strong> {recorded_date}</p>
        </div>

        <!-- Investigators, Victims, Suspects, and Evidence sections -->
        <div class="container">
            <div class="column left-column">
                <!-- Investigators section -->
                <div class="section">
                    <h3 class="section-title">Active Investigators</h3>
                    <div class="section-content">
                        {"No records available" if not investigator_details else 
                            "".join(f"<p><strong>Name:</strong> {name}, <strong>Contact:</strong> {contact}</p>" 
                                    for name, contact in investigator_details)}
                    </div>
                </div>
                <div class="section">
                    <h3 class="section-title">Enrolled Investigators</h3>
                    <div class="section-content">
                        {"No records available" if not prev_investigator_details else 
                            "".join(f"<p><strong>Name:</strong> {name}, <strong>Contact:</strong> {contact}</p>" 
                                    for name, contact in prev_investigator_details)}
                    </div>
                </div>
                <!-- Victims section -->
                <div class="section">
                    <h3 class="section-title">Victims</h3>
                    <div class="section-content">
                        {"No records available" if not victim_details else 
                            "".join(f"<p><strong>Name:</strong> {name}, <strong>Contact:</strong> {contact}, <strong>Address:</strong> {address}</p>" 
                                    for name, contact, address in victim_details)}
                    </div>
                </div>
            </div>
            <div class="column right-column">
                <!-- Suspects section -->
                <div class="section">
                    <h3 class="section-title">Suspects</h3>
                    <div class="section-content">
                        {"No records available" if not suspect_details else 
                            "".join(f"<p><strong>Name:</strong> {name}, <strong>Contact:</strong> {contact}, <strong>Address:</strong> {address}</p>" 
                                    for name, contact, address in suspect_details)}
                    </div>
                </div>
                <!-- Evidence section -->
                <div class="section">
                    <h3 class="section-title">Evidence</h3>
                    <div class="section-content">
                        {"No records available" if not evidence_details else 
                            "".join(f"<p><strong>Name:</strong> {name}, <strong>Description:</strong> {description}</p>" 
                                    for name, description in evidence_details)}
                    </div>
                </div>
                <div class="section">
                    <h3 class="section-title">Case Timeline</h3>
                    <div class="section-content">
                        <ul>
                            { "No timeline available" if not fetched_timeline else 
                                "".join(f"<li>{c_date.date()}[{c_date.hour}:{c_date.minute}]: {activity}</li>" for c_date, activity in fetched_timeline) }
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        <hr>
        <div class="footer">
            <div>
                <p>Investigation with:</p>
                <p style="font-size: 25px"><strong>CrimeNetX</strong></p>
                <P>Crime Solve Done</p>
        </div>
    </body>
    </html>
    """

    return html_content


def generate_pdf(html_content,css_content,output_filename,case,user):
    if pdfkit.from_string(html_content, output_filename,configuration=config,css=css_content):
        placeholder=st.empty() 
        with open(f"Case_{case}.pdf", "rb") as file:
                pdf_data = file.read()
                conn=db.connect_db()
                db.run_query(conn,f"""INSERT INTO pdf_reports (file, username,file_name) VALUES ({psycopg2.Binary(pdf_data)},'{user}','Case_{case}')
                             ON CONFLICT (file_name) DO UPDATE SET file_name = 'Case_{case}'
                             """,msg="File Saved",slot=placeholder)
        # st.success(f"PDF generated: [{output_filename}]({output_filename})")
    else:
        st.error('Failed to generate case report !')

if __name__=="__main__":

    case_id = "001"
    username='31jay'
    html_content = generate_case_report(case_id,username)
    if st.button("Generate PDF"):
        generate_pdf(html_content,'report.css')

