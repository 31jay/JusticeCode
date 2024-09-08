import streamlit as st 
import database as db 
import report 
from streamlit_folium import folium
from streamlit_folium import st_folium
import psycopg2
import base64


def get_user_docs():
    conn=db.connect_db() 
    db.get_all('')


def remove_on_click(placeholder,selected_file):
    conn=db.connect_db() 
    db.run_query(conn,f"Delete from pdf_reports where file_name='{selected_file}'",placeholder)


def main(user):
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Downloads</p>', unsafe_allow_html=True)
    c1,c2=st.columns([3,2])
    with c1.container(border=True,height=460):
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Download Case Report </p>', unsafe_allow_html=True)
        conn=db.connect_db() 
        all_cases=db.get_all(conn,"select caseid from caseReports")
        cases_list=[cases[0] for cases in all_cases]
        case=st.selectbox('Select the case:',options=cases_list,index=None)
        if case:
            conn=db.connect_db() 
            selected_case_data=db.from_db(conn,f"select case_date, nature_of_case,case_description,casestatus,caseno,lat,lng from caseReports where caseid='{case}'")
            s1,s2=st.columns([1,1])
            with s1:
                try:    
                    m=folium.Map(location=[selected_case_data[5],selected_case_data[6]],zoom_start=17,height=200,width=200) 
                    folium.Marker([selected_case_data[5],selected_case_data[6]]).add_to(m)
                    st_folium(m,height=210,use_container_width=True,returned_objects=[])
                except:
                    st.toast('Something went wrong displaying Map')
            with s2:
                st.write(f"Case No: {selected_case_data[4]}")
                st.write(f"Nature: {selected_case_data[1]}")
                st.write(f"Date: {selected_case_data[0]}")
                st.write(f"Status: {selected_case_data[3]}")
                with st.popover('Description'):
                    st.write(f"{selected_case_data[2]}")

            if st.button('Download Case Report',use_container_width=True):
                placeholder=st.empty() 
                html_content=report.generate_case_report(case,user)
                report.generate_pdf(html_content,"report.css",output_filename=f"Case_{case}.pdf",case=case,user=user)
                # with open(f"Case_{case}.pdf", "rb") as file:
                #     pdf_data = file.read()
                # conn=db.connect_db()
                # db.run_query(conn,f"""INSERT INTO pdf_reports (file, username,file_name) VALUES ({psycopg2.Binary(pdf_data)},'{user}','Case_{case}')
                #              ON CONFLICT (file_name) DO UPDATE SET file_name = 'Case_{case}'
                #              """,msg="File Saved",slot=placeholder)
        else:
            st.info('Select Case to generate report')

    with c2.container(border=True,height=460):
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Your Downloads </p>', unsafe_allow_html=True)
        conn = db.connect_db() 
        all_files = db.get_all(conn, f"SELECT file, file_name FROM pdf_reports WHERE username='{user}'")

        file_base64=None 
        selected_file=None 
        for file_data, filename in all_files:
            # Create a button for the current filename
            clicked_file = st.button(filename, key=f"file:{filename}", use_container_width=True)
            if clicked_file:
                file_base64 = base64.b64encode(file_data).decode('utf-8')
                selected_file=filename
    
    st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Report Viewer </p>', unsafe_allow_html=True)
    if file_base64 is not None:
        placeholder=st.empty() 
        st.button('Delete',on_click=remove_on_click(placeholder,selected_file))
        
        st.write(f'<iframe src="data:application/pdf;base64,{file_base64}" width="100%" height="800px"></iframe>', unsafe_allow_html=True)
    else:
        st.info('Select the downloads to view')
    
    db.footer()
        
if __name__=="__main__":
    main('31jay')