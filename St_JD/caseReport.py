import streamlit as st
import datetime
import folium
from streamlit_folium import st_folium
import database as db 
import pandas as pd 
import time 
import psycopg2
import base64


def case_assigned_to(username):
    conn=db.connect_db() 
    conn = db.connect_db()
    cases = db.get_all(conn, f"""SELECT caseNo,caseId,case_date,nature_of_case,case_description,caseStatus
                       from caseReports cs JOIN
                       officer_and_cases oc
                       ON cs.caseid=oc.case_id
                       WHERE oc.officer_id=(select id from authorized where username='{username}') and status='ongoing' and enrollment='active'""")
    cases_df = pd.DataFrame(cases, columns=['Case Number', 'Case ID', 'Date', 'Nature of Case','Case Description','Case Status'])
    case_ids = cases_df['Case ID'].tolist()
    return cases_df, case_ids 



def apply_style(row):
    if row['Case Status'] == 'ongoing':
        return ['background-color: rgba(255, 255, 0, 0.3)'] * len(row)
    elif row['Case Status'] == 'closed':
        return ['background-color: rgba(128, 128, 128, 0.3)'] * len(row)
    elif row['Case Status'] == 'solved':
        return ['background-color: rgba(50, 205, 50, 0.3)'] * len(row)
    else:
        return [''] * len(row)


def update_selected_case(selected_case):
    st.session_state.selected_case = selected_case

def update_checkbox(status): 
    st.session_state.case_status=status

def update_db(query,value,msg,place):
    here=place
    if value is not None and value != '':
        conn=db.connect_db() 
        db.run_query(conn,query,here,msg)

# if __name__=="__main__":
def case_investigation(username):
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Case Reports</p>', unsafe_allow_html=True)

    conn=db.connect_db() 
    role=db.from_db(conn,f"select role from authorized where username='{username}'")

    # Connect to the database and fetch cases
    conn = db.connect_db()
    cases_data = db.fetch_data(conn, table_name='caseReports', data='all', fetch_attributes='caseNo,caseId,case_date,nature_of_case,case_description,caseStatus')
    try:
        # Convert fetched data to pandas DataFrame
        cases_df = pd.DataFrame(cases_data, columns=['Case Number', 'Case ID', 'Date', 'Nature of Case','Case Description','Case Status'])
        case_ids = cases_df['Case ID'].tolist()

        styled_df = cases_df.style.apply(apply_style, axis=1)

        # Display the DataFrame
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Records</p>', unsafe_allow_html=True)
        st.dataframe(styled_df, use_container_width=True, hide_index=True,height=150)

    # Case Picker Section : 
        
        with st.container(border=True):
            # st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Picker</p>', unsafe_allow_html=True)
            if 'selected_case' not in st.session_state:
                st.session_state.selected_case=None 

            # select box with all cases in the dropdown and the selected will be picked up for the investigation
            assigned_df,assigned_ids=case_assigned_to(username)
            if role[0]=='Administrator':
                selected_case = st.selectbox('Select a case to investigate', options=case_ids, key="case_select",index=None,placeholder="Put case to dashboard")
            else:
                selected_case = st.selectbox('Select a case to investigate', options=assigned_ids, key="case_select",index=None,placeholder="Put case to dashboard")

            st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Assigned Cases</p>', unsafe_allow_html=True)
            if assigned_df.empty:
                st.write('No any assigned cases')
            else:
                st.dataframe(assigned_df, use_container_width=True, hide_index=True,height=150)


            update_selected_case(selected_case)        
            conn=db.connect_db()
            selected_case_data=db.fetch_data(conn,table_name='caseReports',check_attributes=f'caseId=\'{st.session_state.selected_case}\'')
            print(selected_case_data)
            #Case Dashboard Section 
            st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 25px; font-weight: bold; margin-bottom: 0px">Case Dashboard</p>', unsafe_allow_html=True)

            if st.session_state.selected_case is not None:
                st.write('<br>',unsafe_allow_html=True )
                col1,col2=st.columns([1.7,2.5])

                with col1:
                    try:    
                        m=folium.Map(location=[selected_case_data[5],selected_case_data[6]],zoom_start=17,height=200,width=200) 
                        folium.Marker([selected_case_data[5],selected_case_data[6]]).add_to(m)
                        st_folium(m,height=300,use_container_width=True,returned_objects=[])
                    except:
                        st.toast('Something went wrong displaying Map')
                    if 'closing_st' not in st.session_state:
                        st.session_state.closing_st=None 

                    if 'case_closed' not in st.session_state:
                        st.session_state.case_closed=None 
                    if(selected_case_data[8]=='solved' or selected_case_data[8]=='closed'):
                        st.session_state.case_closed=True 
                    else:
                        st.session_state.case_closed=False 
                    index=0
                    if selected_case_data[8] =='ongoing':
                        index=0
                    elif selected_case_data[8]=='solved':
                        index=1
                    elif selected_case_data[8]=='closed':
                        index=2
                        st.session_state.closing_st=True 
                    with st.container(border=True):
                        # update the case status here. 
                        case_status=st.radio('Case Status',options=['ongoing','solved','closed'],index=index,horizontal=True)
                        if ((case_status == 'solved' or case_status=='closed') and (selected_case_data[8]=='ongoing'))or((case_status=='ongoing') and (selected_case_data[8]=='closed' or selected_case_data[8]=='solved')):
                            st.session_state.closing_st=False 
                        else:
                            st.session_state.closing_st=True 
                        # text input for the case slosing statement. Disable if case is ongoing 
                        with st.form('Status',border=False,clear_on_submit=True):
                            closing_st=st.text_area('Final Statment',placeholder='* Case Closing Statement',label_visibility='collapsed',disabled=st.session_state.closing_st)
                            submit_final=st.form_submit_button('Confirm',disabled=st.session_state.closing_st)
                        if submit_final:
                            if closing_st.strip()!='':
                                conn=db.connect_db() 
                                msg_place=st.empty() 
                            # Updates the case status and adds the report to timeline 
                                db.run_query(conn,f'''
                                            Update caseReports SET casestatus='{case_status}' where caseid='{selected_case_data[1]}';
                                            Insert into case_timeline(caseid,date,activity) values('{selected_case_data[1]}','{datetime.datetime.now()}','Case Status: {case_status} Remark: {closing_st} ::User:{username}');
                                            ''',msg="Case Status Updated",slot=msg_place)
                                conn=db.connect_db() 
                                if case_status=='solved':
                                    db.run_query(conn,f"""
                                                 update officer_and_cases set status='solved',case_left_on='{datetime.datetime.now().date()}' where case_id='{selected_case_data[1]}' and status='ongoing' and enrollment='active';    
                                                """,slot=msg_place)
                                elif case_status=='ongoing':
                                        db.run_query(conn,f"""
                                                        update officer_and_cases set enrollment='revised' where case_id='{selected_case_data[1]}' and status='solved' and enrollment='active';
                                                        """,slot=msg_place)
                                    
                                elif case_status=='closed':
                                    db.run_query(conn,f"""
                                                        update officer_and_cases set status='closed', enrollment='archive',case_left_on='{datetime.datetime.now().date()}' where case_id='{selected_case_data[1]}' and status='ongoing' and enrollment='active';

                                                """,slot=msg_place)
                                    pass 
                                time.sleep(2)
                                msg_place.empty() 
                                st.rerun() 
                            else:
                                st.error('Fill required field')
                    s1,s2=st.columns([1,1])
            
            # buttons for the activity
            # will be disabled for the closed cases 
                    with s1.popover('Case Update',use_container_width=True,disabled=st.session_state.case_closed):
                        with st.container(border=False):
                            conn=db.connect_db()
                            db_cases=db.fetch_data(conn,fetch_attributes='nature_of_case',table_name='nature_of_case',data='all')
                            cases = [case[0] for case in db_cases]
                            cases.append('Other')
                            nature_of_case=st.selectbox('Update Nature of Case',options=cases,placeholder=selected_case_data[3],index=None)
                            cases.pop() #Remove other from the cases 
                            if nature_of_case=='Other':
                                other_nature=st.text_input('Nature Of Case:')
                                is_duplicate=False
                                is_duplicate,duplicate=db.check_for_duplicates(other_nature,cases)    
                                warning=st.empty()
                                if is_duplicate:
                                    warning.info(f'Nature of Case: Did you mean {duplicate}')
                                    choice=st.radio('What do you want ?',[f'Use \'{duplicate}\'', f'Use \'{other_nature}\''],index=None)

                                    if choice is not None:
                                        if choice.startswith(f'Use \'{duplicate}\''):
                                            nature_of_case=duplicate
                                        else:
                                            nature_of_case=other_nature

                                if other_nature and not is_duplicate:
                                    nature_of_case=other_nature
                            conn=db.connect_db() 
                            db_officers = db.get_all(conn,"""select name, username from 
                                                     authorized a JOIN officer_record off 
                                                     ON a.id=off.id
                                                     """)
                            officers_options = [f"{officer[0]}: {officer[1]}" for officer in db_officers]

                            conn=db.connect_db() 
                            remove_opt=db.get_all(conn,f"""Select name,username from 
                                                  officer_record off INNER JOIN officer_and_cases oc ON off.id=oc.officer_id 
                                                  INNER JOIN authorized a ON a.id=off.id 
                                                  WHERE case_id='{selected_case_data[1]}' and status='ongoing' and enrollment='active'""")
                            remove_options = [f"{officer[0]}: {officer[1]}" for officer in remove_opt]

                            # Display the select box with officer options
                            if role[0]=='Administrator':    
                            #Add new Investigator/ Remove  
                                assigned_officer = st.selectbox('Add Investigator', options=officers_options, 
                                                                placeholder='Assign Investigating Officer',index=None)
                                removed_officer=st.selectbox('Remove Investigator', options=remove_options, 
                                                                placeholder='Remove Investigating Officer',index=None)
                            else:
                                st.selectbox('Add Investigator', options=officers_options, 
                                                                placeholder='Contact Administrator',index=None,disabled=True)
                                st.selectbox('Remove Investigator', options=officers_options, 
                                                                placeholder='Contact Administrator',index=None,disabled=True)


                            if st.button('Submit',use_container_width=True):
                                place_msg=st.empty() 
                                if nature_of_case not in cases and nature_of_case is not None:
                                    conn=db.connect_db()
                                    db.run_query(conn,f'''
                                    Insert into nature_of_case(nature_of_case) 
                                    values('{other_nature}')
                                    ''',slot=place_msg)
                                    nature_of_case=other_nature


                                if nature_of_case is not None and nature_of_case!=selected_case_data[3]:
                                    conn=db.connect_db() 
                                    db.run_query(conn,f"""Update caseReports set nature_of_case='{nature_of_case}' where caseid='{selected_case_data[1]}';
                                                        Insert into case_timeline(caseid,date,activity) values('{selected_case_data[1]}','{datetime.datetime.now()}','Nature of Case Changed: {selected_case_data[3]} :-> {nature_of_case}');
                                                        Update nature_of_case set case_count=case_count-1 where nature_of_case='{selected_case_data[3]}';
                                                        Update nature_of_case set case_count=case_count+1 where nature_of_case='{nature_of_case}';
                                                    """,msg='Updated to CaseReports',slot=place_msg)
                                    
                                if assigned_officer is not None :
                                    # Extract the selected officer ID from the selected option
                                    selected_officer_username = assigned_officer.split(': ')[1]
                                    conn=db.connect_db() 
                                    officer_id_cnt=db.from_db(conn,f"select contact,id from officer_record where id=(select id from authorized where username='{selected_officer_username}')")
                                    conn=db.connect_db() 
                                    already_enrolled=db.from_db(conn,f"select * from officer_and_cases where officer_id='{officer_id_cnt[1]}' and case_id='{selected_case_data[1]}' and status='ongoing' and enrollment='active';")
                                    if already_enrolled is None:
                                        conn=db.connect_db()
                                        db.run_query(conn,f'''
                                                    insert into case_timeline(date,caseid,activity) values ('{datetime.datetime.now()}','{selected_case_data[1]}','Officer Assigned by {username}:: {assigned_officer}::Contact: {officer_id_cnt[0]}');
                                                    insert into officer_and_cases(officer_id,case_id,status,enrollment,case_assigned_on) values({officer_id_cnt[1]},'{selected_case_data[1]}','ongoing','active','{datetime.datetime.now().date()}');
                                                    ''',msg="Updated to timeline",slot=place_msg) 
                                    else:
                                        place_msg.info('Investigator is already in the case.')
                                if removed_officer is not None :
                                    # Extract the selected officer ID from the selected option
                                    selected_officer_username = removed_officer.split(': ')[1]
                                    conn=db.connect_db() 
                                    officer_id_cnt=db.from_db(conn,f"select contact,id from officer_record where id=(select id from authorized where username='{selected_officer_username}')")
                                    conn=db.connect_db() 
                                    db.run_query(conn,f'''
                                                insert into case_timeline(date,caseid,activity) values ('{datetime.datetime.now()}','{selected_case_data[1]}','Officer Removed by: {username}:: {removed_officer}::Contact: {officer_id_cnt[0]}');
                                                Update officer_and_cases set enrollment='archive', case_left_on='{datetime.datetime.now().date()}' where officer_id={officer_id_cnt[1]} and case_id='{selected_case_data[1]}' and enrollment='active';
                                                ''',msg="Updated to timeline",slot=place_msg) 
                    
                    #Add the case images to database    
                        case_image=st.file_uploader('Upload Photos',type=['jpg','jpeg','png','gif'])
                        if case_image:
                                # with open(photos,"rb") as image_file:
                                image_data=case_image.read() 
                                des=str() 
                                des=st.text_input(f'Describe image *',placeholder='What this image about ?')
                                place=st.empty()
                                if st.button('Done',key='case_img_upload'):
                                    if des.strip():
                                        conn=db.connect_db() 
                                        db.run_query(conn,f"insert into case_images(caseid,image,description) values('{selected_case_data[1]}',{psycopg2.Binary(image_data)},'{des}')",msg='Added Successfully',slot=place)
                                    else:
                                        place.error('Image Caption Required')
                # Add the case victims 
                    with s2.popover('Add Victim',use_container_width=True,disabled=st.session_state.case_closed):
                        with st.form('Victim',clear_on_submit=True,border=False):
                            victim_id=str() 
                            victim_id=st.text_input('victim_id',placeholder="Add New or Add existing to update")
                            victim_name = st.text_input("Name: ")
                            victim_nickname = st.text_input("Nickname: ")
                            victim_gender = st.selectbox("Gender: ", ["Male", "Female", "Other"],index=None)
                            victim_address = st.text_input("Address:") 
                            victim_contact = st.text_input("Contact Information:")
                            victim_statement = st.text_area("Statement:")
                            victim_image=st.file_uploader(label='Upload Image',type=['jpg','jpeg','png','gif'])
                            victim_img=None 
                            if victim_image:    
                                victim_img=victim_image.read() 
                            else:
                                image_path = 'icons/victim.jpg'
                                with open(image_path, 'rb') as file:
                                    victim_img = file.read() 
                            if st.form_submit_button('Update'):
                                here=st.empty()
                                if victim_id.strip():
                                    conn=db.connect_db()
                                    ids=db.fetch_data(conn,'victims',f"victim_id='{victim_id}'",'name')
                                    if ids:
                                        update_db(value=victim_name,query=f"Update victims set name='{victim_name}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_nickname,query=f"Update victims set nickname='{victim_nickname}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_gender,query=f"Update victims set gender='{victim_gender}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_address,query=f"Update victims set address='{victim_address}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_contact,query=f"Update victims set contact='{victim_contact}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_statement,query=f"Update victims set statement='{victim_statement}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                        update_db(value=victim_img,query=f"Update victims set image={psycopg2.Binary(victim_img)} where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    else:
                                        query = f"""
                                            INSERT INTO victims 
                                            (caseid,victim_id, name, nickname, gender, contact, address, statement, image) 
                                            VALUES 
                                            ('{selected_case_data[1]}','{victim_id}', '{victim_name}', '{victim_nickname}', '{victim_gender}', '{victim_contact}', '{victim_address}', '{victim_statement}', {psycopg2.Binary(victim_img)})
                                        """          
                                        conn=db.connect_db()
                                        db.run_query(conn,query,msg="Added Successfully",slot=here)
                                        time.sleep(2)
                                        here.empty() 
                                else:
                                    placeholder=st.empty()
                                    placeholder.error('No record to update !')
                                    time.sleep(2)
                                    placeholder.empty() 
                    
                # Add the suspects 
                    with s1.popover('Add Suspect',use_container_width=True,disabled=st.session_state.case_closed):
                        with st.form('Suspect',clear_on_submit=True,border=False):
                            suspect_id=str() 
                            suspect_id=st.text_input('suspect_id',placeholder="Add New or Add existing to update")
                            suspect_name = st.text_input("Name: ")
                            suspect_nickname = st.text_input("Nickname: ")
                            suspect_gender = st.selectbox("Gender: ", ["Male", "Female", "Other"],index=None)
                            suspect_address = st.text_input("Address:") 
                            suspect_contact = st.text_input("Contact Information:")
                            suspect_statement = st.text_area("Statement:")
                            suspect_image=st.file_uploader(label='Upload Image',type=['jpg','jpeg','png','gif'])
                            suspect_img=None 
                            if suspect_image:    
                                suspect_img=suspect_image.read() 
                            else:
                                image_path = 'icons/suspect.jpg'
                                with open(image_path, 'rb') as file:
                                    suspect_img = file.read() 
                            if st.form_submit_button('Update'):
                                msg=st.empty()
                                if suspect_id.strip():
                                    conn=db.connect_db()
                                    ids=db.fetch_data(conn,'suspects',f"suspect_id='{suspect_id}'",'name')
                                    if ids:
                                        update_db(value=suspect_name,query=f"Update suspects set name='{suspect_name}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_nickname,query=f"Update suspects set nickname='{suspect_nickname}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_gender,query=f"Update suspects set gender='{suspect_gender}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_address,query=f"Update suspects set address='{suspect_address}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_contact,query=f"Update suspects set contact='{suspect_contact}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_statement,query=f"Update suspects set statement='{suspect_statement}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                        update_db(value=suspect_img,query=f"Update suspects set image={psycopg2.Binary(suspect_img)} where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    else:
                                        query = f"""
                                            INSERT INTO suspects 
                                            (caseid,suspect_id, name, nickname, gender, contact, address, statement, image) 
                                            VALUES 
                                            ('{selected_case_data[1]}','{suspect_id}', '{suspect_name}', '{suspect_nickname}', '{suspect_gender}', '{suspect_contact}', '{suspect_address}', '{suspect_statement}', {psycopg2.Binary(suspect_img)})
                                        """          
                                        conn=db.connect_db()
                                        db.run_query(conn,query,msg="Added Successfully",slot=msg)
                                        time.sleep(2)
                                        msg.empty() 
                                else:
                                    placeholder=st.empty()
                                    placeholder.error('No record to update !')
                                    time.sleep(2)
                                    placeholder.empty() 
                    
                    # Add the evidences 
                    with s2.popover('Add Evidence ',use_container_width=True,disabled=st.session_state.case_closed):
                        with st.form('evidence *',border=False,clear_on_submit=True):
                            evidence_name=str() 
                            description=str() 
                            evidence_name=st.text_input('Evidence Identification',placeholder='Name/ Type of evidence')
                            description=st.text_area('Description',placeholder='Describe the evidence')
                            image=st.file_uploader('Evidence Image',type=['jpg','jpeg','png','gif'])
                            if image:
                                image=image.read()
                            else:
                                image_path = 'icons/evidence.jpg'
                                with open(image_path, 'rb') as file:
                                    image = file.read() 
                            if st.form_submit_button('Update'):
                                label=st.empty() 
                                if evidence_name.strip() and description.strip():
                                    conn=db.connect_db()
                                    db.run_query(conn,f'''insert into evidence(case_id,name,description) values('{selected_case_data[1]}','{evidence_name}','{description}');
                                                insert into case_timeline(date,caseid,activity) values ('{datetime.datetime.now()}','{selected_case_data[1]}','Evidence Added: {evidence_name}');
                                                Update evidence set image={psycopg2.Binary(image)} where case_id='{selected_case_data[1]}' and name='{evidence_name}' and description='{description}';
                                                ''',msg='Added Successfully',slot=label)
                                else:
                                    label.error('Fill the required fields')
                                    time.sleep(2)
                                    label.empty() 
                    
                # view the saved case images 
                    with st.popover('View Images',use_container_width=True):
                        conn=db.connect_db() 
                        images_data=db.fetch_data(conn,'case_images',check_attributes=f"caseid='{selected_case_data[1]}'",fetch_attributes='image,description,id',data='all')
                        st.write('<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Images</p>', unsafe_allow_html=True)

                        if images_data:
                            for bytea,description,id in images_data:
                                with st.container(border=True):    
                                    st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                                    <img src="data:image/png;base64,{base64.b64encode(bytea).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                                    <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {id}</p>""",unsafe_allow_html=True)
                                    case_des=st.text_area("description",value=description,label_visibility='collapsed',key=f'{id}image')
                                    slot=st.empty() 
                                    if st.button("Update",key=f'update_image_{id}'):
                                        if case_des.strip():
                                            conn=db.connect_db() 
                                            db.run_query(conn,f"Update case_images set description='{case_des}' where id='{id}'",msg="Updated",slot=slot)
                                            time.sleep(2)
                                            st.rerun() 
                        else:
                            st.write('No Images')

            #### Right Column Contents from here                 
                with col2:
                    #writes the description of the selected case to the dashboard 
                    st.write(f'''
                        <p style="color:white; border-bottom: 1px solid white; font-weight:bold; font-size: 25px; margin-left: 100px; margin-top: 0px; line-height: 2; margin-bottom: 15px;">Case No.: {selected_case_data[0]}</p>
                        <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Case_ID      : {selected_case_data[1]}</p>
                        <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Date         : {selected_case_data[2]}</p>
                        <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Nature       : {selected_case_data[3]}</p>
                        <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Status       : {selected_case_data[8]}</p>
                            ''',unsafe_allow_html=True)
                    st.write('')
                    sub1,sub2=st.columns([0.5,4])
                    # Investigators Involved in the cases 
                    with sub2.popover('Investigators',use_container_width=True):
                        st.write('<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Investigators</p>', unsafe_allow_html=True)
                        conn=db.connect_db() 
                        current_investigators=db.get_all(conn,f"""
                                                         Select id, name, contact, email, image, case_assigned_on from
                                                         officer_record off INNER JOIN officer_and_cases oc ON off.id=oc.officer_id
                                                         WHERE case_id='{selected_case_data[1]}' and status='ongoing' and enrollment='active'
                                                         """)
                        conn=db.connect_db() 
                        former_investigators=db.get_all(conn,f"""
                                                         Select distinct id, name, contact, email, image, case_assigned_on,case_left_on from
                                                         officer_record off INNER JOIN officer_and_cases oc ON off.id=oc.officer_id
                                                         WHERE case_id='{selected_case_data[1]}' and ((status='ongoing' and enrollment='archive') or status!='ongoing')
                                                         """)
                        current,former=st.tabs(['Current','Former'])
                        with current:
                            if current_investigators:
                                for officer in current_investigators:
                        # Display image of the victim
                                # with st.container(border=False):    
                                    st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                            <img src="data:image/png;base64,{base64.b64encode(officer[4]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                            <p style='margin-bottom: 5px; font-size: 15px; font-family: sans-serif; color: green; font-weight: bold'> {officer[1]}</p>""",unsafe_allow_html=True)
                                
                                    with st.expander('View Details'):
                                        st.write(f"""
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Contact:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Email:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Case Assigned On:</b> {officer[5]}</p>
                                            
                                            """, unsafe_allow_html=True)
                            else:
                                st.write('No records')

                        with former:
                            if former_investigators:
                                for officer in former_investigators:
                        # Display image of the victim
                                # with st.container(border=False):    
                                    st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                            <img src="data:image/png;base64,{base64.b64encode(officer[4]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                            <p style='margin-bottom: 5px; font-size: 15px; font-family: sans-serif; color: green; font-weight: bold'> {officer[1]}</p>""",unsafe_allow_html=True)
                                
                                    with st.expander('View Details'):
                                        st.write(f"""
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Contact:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Email:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Case Assigned On:</b> {officer[5]}</p>
                                                <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Case Left On:</b> {officer[6]}</p>
                                            
                                            """, unsafe_allow_html=True)
                            else:
                                st.write('No records')

                    with sub2.popover('Case Description',use_container_width=True):
                        st.write(f'<p style="color:red; text-align: justify">{selected_case_data[4]}</p>',unsafe_allow_html=True)
                    
                    with sub2.popover('Victim Info',use_container_width=True):
                        st.write('<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Victims</p>', unsafe_allow_html=True)

                        conn=db.connect_db()
                        db_victims=db.fetch_data(conn,table_name='victims',check_attributes=f"caseid='{selected_case_data[1]}'",data='all')
                        if db_victims:
                            for victim in db_victims:
                    # Display image of the victim
                            # with st.container(border=False):    
                                st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                        <img src="data:image/png;base64,{base64.b64encode(victim[8]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                        <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color: green; font-weight: bold'> {victim[2]}</p>""",unsafe_allow_html=True)
                               
                                with st.expander('View Details'):
                                    st.write(f"""
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> id:</b> {victim[1]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Nickname:</b> {victim[3]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Gender:</b> {victim[4]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Contact:</b> {victim[5]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Address:</b> {victim[6]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Statement:</b> {victim[7]}</p>
                                         
                                         """, unsafe_allow_html=True)
                        else:
                            st.write('No records')
                        
                    
                    with sub2.popover('Suspects',use_container_width=True,):
                        st.write('<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Suspects</p>', unsafe_allow_html=True)
                        conn=db.connect_db()
                        db_suspects=db.fetch_data(conn,table_name='suspects',check_attributes=f"caseid='{selected_case_data[1]}'",data='all')
                        if db_suspects:
                            for victim in db_suspects:
                                st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                        <img src="data:image/png;base64,{base64.b64encode(victim[8]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                        <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color: green; font-weight: bold'> {victim[2]}</p>""",unsafe_allow_html=True)
                               
                                with st.expander('View Details'):
                                    st.write(f"""
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> id:</b> {victim[1]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Nickname:</b> {victim[3]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Gender:</b> {victim[4]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Contact:</b> {victim[5]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Address:</b> {victim[6]}</p>
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style="color:grey"> Statement:</b> {victim[7]}</p>
                                         
                                         """, unsafe_allow_html=True)
                        else:
                            st.write('No records')
                    
                    with sub2.popover('Gathered Evidences',use_container_width=True):
                        st.write('<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Case Evidences</p>', unsafe_allow_html=True)
                        conn=db.connect_db()
                        evidences=db.fetch_data(conn,table_name='evidence',check_attributes=f"case_id='{selected_case_data[1]}'",data='all')
                        if evidences:
                            for evidence in evidences:
                                st.write(f"""<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                        <img src="data:image/png;base64,{base64.b64encode(evidence[2]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                        <p style='margin-bottom: 5px; font-size: 16px; font-family: sans-serif; color: green; font-weight: bold'> {evidence[4]}</p>
                                        """,unsafe_allow_html=True)
                               
                                with st.expander('Description'):
                                    st.write(f"""
                                             <p style='margin-bottom: 2px; font-size: 12px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: white;'><b style='color: grey'>id: </b>{evidence[0]}</p>
                                             <p style='margin-bottom: 2px; font-size: 14px; font-weight: regular; text-align: justify;  color: white;'> {evidence[3]}</p>
                                         """, unsafe_allow_html=True)
                        else:
                            st.write('No records')

                    with sub2.popover('Similar Cases',use_container_width=True):
                        st.write('''<p style="color: green; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Similar to this case:</p>''', unsafe_allow_html=True)
                        conn=db.connect_db() 
                        same_nature_cases=db.get_all(conn,f"select caseid, case_description,case_date from caseReports where nature_of_case='{selected_case_data[3]}' and caseid !='{selected_case_data[1]}'")
                        conn=db.connect_db()
                        same_victim_cases=db.get_all(conn,f'''
                                                SELECT victims.caseid,case_description,case_date
                                                FROM caseReports
                                                JOIN victims ON caseReports.caseid = victims.caseid
                                                WHERE victims.name IN (
                                                    SELECT name
                                                    FROM victims
                                                    WHERE caseid = '{selected_case_data[1]}'
                                                )
                                                AND caseReports.caseid != '{selected_case_data[1]}';
                                            ''')
                        conn=db.connect_db()
                        same_suspects_cases=db.get_all(conn,f'''
                                                SELECT suspects.caseid,case_description,case_date
                                                FROM caseReports
                                                JOIN suspects ON caseReports.caseid = suspects.caseid
                                                WHERE suspects.name IN (
                                                    SELECT name
                                                    FROM suspects
                                                    WHERE caseid = '{selected_case_data[1]}'
                                                )
                                                AND caseReports.caseid != '{selected_case_data[1]}';
                                            ''')
                        
                        with st.expander('Same Nature'):
                            if same_nature_cases:    
                                for case in same_nature_cases:
                                    st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                            f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                            f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                            '<hr>',unsafe_allow_html=True)
                            else:
                                st.write('No similar cases')

                        with st.expander('Same Victim'):
                            if same_victim_cases:
                                for case in same_victim_cases:
                                    st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                            f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                            f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                            '<hr>',unsafe_allow_html=True)
                            else:
                                st.write('No similar cases')

                        with st.expander('Same Suspects'):
                            if same_suspects_cases:
                                for case in same_suspects_cases:
                                    st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                            f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                            f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                            '<hr>',unsafe_allow_html=True)
                            else:
                                st.write('No similar cases')
                                
                    #update the case activity. What's going on ??
                    with sub2.form('timeline',clear_on_submit=True,border=False):
                        timeline=st.text_area('Remarks','',label_visibility="collapsed",placeholder="Case Timeline Update. \n What's going on ??",disabled=st.session_state.case_closed,height=120)
                        slot=sub2.empty() 
                        submit_timeline=st.form_submit_button('Add To Timeline',disabled=st.session_state.case_closed)                
                    if submit_timeline:
                        if timeline !='':
                            conn=db.connect_db() 
                        # Updates the case status and adds the report to timeline 
                            db.run_query(conn,f'''
                                            Insert into case_timeline(caseid,date,activity) values('{selected_case_data[1]}','{datetime.datetime.now()}','{timeline}::{username}')
                                            ''',msg="Updated to timeline",slot=slot)
                            time.sleep(2)
                            st.rerun() 
                        else:
                            slot.error('Fill required field')
                            time.sleep(2)
                            slot.empty() 
                    # displays the case timeline inside a popover.
                    with sub2.popover('View Timeline'):
                        conn=db.connect_db()
                        fetched_timeline=db.fetch_data(conn,table_name='case_timeline',check_attributes=f"caseid='{selected_case_data[1]}'",fetch_attributes='date,activity',add='order by date ASC',data='all')
                        html_content = "<style> .date { color: #3498DB; } .activity { color: #2ECC71; } </style>"
                        # Adding a title for the section
                        html_content += "<h4 style='border-bottom: 1px solid grey; line-height: 0; margin-bottom: 10px;'>Case Timeline</h4>"

                        # Iterating over each entry in the timeline
                        for c_date, activity in fetched_timeline:
                            date=f'{c_date.date()}[{c_date.hour}:{c_date.minute}]'
                            # Formatting each entry with colored span tags
                            html_content += f"<p style='margin-bottom: 5px;'><span class='date'><b>{date}</b></span>: <span class='activity'>{activity}</span></p>"

                        st.markdown(html_content, unsafe_allow_html=True)
            else:     
                st.write('No case Selected')
                # emp_col,s_col1,s_col2,emp_col2=st.columns([2,2,3,2])
                # with s_col1:
                #     st.image('icons\icon.png',width=200)
                # with s_col2:
                #     st.image('icons\dashboard_empty.png',use_column_width=True)
    except Exception as e:
        st.warning(f'Something wrong with database: {e}')
    
    db.footer() 
        

if __name__=="__main__":
    case_investigation('31jay')