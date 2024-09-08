import streamlit as st 
import database as db 
from streamlit_option_menu import option_menu
from caseReport import update_db
import base64
  
def query_database(search_off=None):
    if search_off is None:
        query = """SELECT 
                        o.id AS officer_id,
                        o.name,
                        o.contact,
                        COUNT(oac.case_id) AS total_cases,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='active') AS cases_solved,
                        o.joined_date,
                        o.image,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='revised') AS cases_revised,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'ongoing' AND enrollment='active') AS live_cases
                    FROM 
                        officer_record o
                    LEFT JOIN 
                        officer_and_cases oac ON o.id = oac.officer_id
                    inner join
                        authorized auth ON auth.id=o.id 
                    GROUP BY 
                        o.id, o.name, o.contact, o.joined_date, o.image;"""

    else:
        query = f"""SELECT 
                        o.id AS officer_id,
                        o.name,
                        o.contact,
                        COUNT(oac.case_id) AS total_cases,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='active') AS cases_solved,
                        o.joined_date,
                        o.image,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='revised') AS cases_revised,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'ongoing' AND enrollment='active') AS live_cases
                    FROM 
                        officer_record o
                    LEFT JOIN 
                        officer_and_cases oac ON o.id = oac.officer_id
                    inner join
                        authorized auth ON auth.id=o.id 
                    WHERE o.name='{search_off}'
                    GROUP BY 
                        o.id, o.name, o.contact, o.joined_date, o.image;"""
    conn = db.connect_db() 
    details=db.get_all(conn,query)
    return details


def query_archive_database(search_off=None):
    if search_off is None:
        query = """SELECT 
                        o.id AS officer_id,
                        o.joined_date,
                        arch.left_date,
                        o.contact,
                        COUNT(oac.case_id) AS total_cases,
                        o.image,
                        o.name,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' and enrollment='active') AS cases_solved,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='revised') AS cases_revised
                    FROM 
                        officer_record o
                    LEFT JOIN 
                        officer_and_cases oac ON o.id = oac.officer_id
                    inner join
                        officer_archive arch ON arch.id=o.id 
                    GROUP BY 
                        o.id, o.name, o.contact, o.joined_date,arch.left_date, o.image;"""

    else:
        query = """SELECT 
                        o.id AS officer_id,
                        o.joined_date,
                        arch.left_date,
                        o.contact,
                        COUNT(oac.case_id) AS total_cases,
                        o.image,
                        o.name,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' and enrollment='active') AS cases_solved,
                        (SELECT COUNT(*) FROM officer_and_cases WHERE officer_id = o.id AND status = 'solved' AND enrollment='revised') AS cases_revised
                    FROM 
                        officer_record o
                    LEFT JOIN 
                        officer_and_cases oac ON o.id = oac.officer_id
                    inner join
                        officer_archive arch ON arch.id=o.id 
                    WHERE o.name='{search_off}'
                    GROUP BY 
                        o.id, o.name, o.contact, o.joined_date, arch.left_date, o.image;"""
    conn = db.connect_db() 
    details=db.get_all(conn,query)
    return details

def all_officers():
    conn=db.connect_db() 
    current_officers=db.get_all(conn,"""Select name from 
                               officer_record INNER JOIN authorized
                               ON officer_record.id=authorized.id""")
    
    conn=db.connect_db()
    former_officers=db.get_all(conn,"""Select name from 
                               officer_record INNER JOIN officer_archive
                               ON officer_record.id=officer_archive.id
                               """)
    return current_officers,former_officers

def past_officer_record(my_officers):
    if my_officers:
        for i, officer in enumerate(my_officers):
            # Alternate between columns
            if i % 3 == 0:
                col1, col2,col3 = st.columns(3)

            # Display image and details for each officer
            with (col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3):
                with st.container(border=True, height=400):
                    st.write(
                            f"""
                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                <img src="data:image/png;base64,{base64.b64encode(officer[5]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;"  />
                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[6]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[3]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[1]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Left:</b> {officer[2]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Involved:</b> {officer[4]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Solved:</b> {officer[7]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[8]}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    else:
        st.write('No Records Found')

def current_officers_record(my_officers):
    if my_officers:
        for i, officer in enumerate(my_officers):
            # Alternate between columns
            if i % 3 == 0:
                col1, col2 ,col3= st.columns(3)

            # Display image and details for each officer
            with (col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3):
                with st.container(border=True,height=400):
                    st.write(
                            f"""
                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                <img src="data:image/png;base64,{base64.b64encode(officer[6]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[1]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[2]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[5]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Involved:</b> {officer[3]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: green;font-weight: bold'><b style='color: grey'> Live Cases:</b> {officer[8]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Solved:</b> {officer[4]}</p>
                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[7]}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    else:
        st.write('No Records Found')



def main():
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Investigators</p>', unsafe_allow_html=True)
    current_officers,formr_officers=all_officers() 
    current,past=st.tabs(['Current Investigators','Former Investigators'])
    try:
        with current:

        #### Investigators REcord 
            with st.container(height=800,border=False):
                st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 25px; font-weight: bold">Investigators Record</p>', unsafe_allow_html=True)
                my_officers=[officer for (officer,) in current_officers]
                search_off=st.selectbox('Search Here',options=my_officers,index=None,placeholder='Search Here',key='current',label_visibility='collapsed')
                if search_off is None:
                    details=query_database()
                    current_officers_record(details)
                else:
                    details=query_database(search_off)
                    current_officers_record(details)
        with past:
                st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 25px; font-weight: bold">Investigators Record</p>', unsafe_allow_html=True)
                my_officers = [officer for (officer,) in formr_officers]
                search_off=st.selectbox('Search Here',options=my_officers,key='former',label_visibility='collapsed',index=None,placeholder='Search Here')
                if search_off is None:
                    details=query_archive_database() 
                    past_officer_record(details)
                else:
                    details=query_archive_database(search_off)
                    past_officer_record(details)
    except Exception as e:
        st.warning(f'Something wrong with database {e}')
    
    db.footer() 

if __name__=='__main__':
    main()
