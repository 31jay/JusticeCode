import streamlit as st  
import database as db 
import datetime 
import pandas as pd 
import base64 
import time 
import binascii
import psycopg2
import bcrypt
 
ROLES=['Investigator']

def get_confirmation():
    st.session_state.confirmation_pwd=True  


def get_dataframe():
    conn=db.connect_db() 
    auth_users=db.fetch_data(conn,table_name='authorized',fetch_attributes='id,username,role,last_logged_in',data='all')
    users_df = pd.DataFrame(auth_users, columns=['UserID', 'username', 'Role', 'last_logged_in'],)
    allUsers=[user[1] for user in auth_users]
    return users_df, allUsers

def auth_interface(user):
    try:
        st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Authorized Users</p>', unsafe_allow_html=True)
        conn=db.connect_db()
        system_admin=db.from_db(conn,f"""select name,role,image,last_logged_in,email,contact 
                                from authorized INNER JOIN officer_record 
                                ON authorized.id=officer_record.id
                                where username='{user}'""")
        # Fetch data for the authorized users dataframe
        data, allUsers = get_dataframe() 
        
        # Split the page into two columns
        left_column, right_column = st.columns(2)
        
        # Right column: Options for update: To update the credential 
        if system_admin[1] != 'Administrator':
            st.info('Contact Administrator for further')

    # Add New Users to the table 
        if system_admin[1]=='Administrator':
            add,update,delete=right_column.tabs(['Add Investigator','Update Investigators','Delete Investigator'])
            with add.form("Add",border=True,clear_on_submit=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Add User</p>', unsafe_allow_html=True)
                joined_date=st.date_input('Joined Date *',max_value=datetime.datetime.now().date(),value=None)
                name=st.text_input('Name',placeholder='Full Name',label_visibility='collapsed')
                username=st.text_input('User Name',placeholder='User Name',label_visibility='collapsed')
                key=st.text_input('Passkey',placeholder='Pass Key',label_visibility='collapsed',type='password')
                email=st.text_input('Email',placeholder='email',label_visibility='collapsed')
                contact=st.text_input('Contact',placeholder='contact',label_visibility='collapsed')
                image=st.file_uploader('Image',type=['jpg','jpeg','png'])
                if st.form_submit_button('Add User',use_container_width=True):
                    placeholder=st.empty() 
                    if name.strip() and username.strip() and key.strip() and email.strip() and contact.strip and image:
                        password=db.hash_generator(key)
                        hashed=binascii.hexlify(password).decode('utf-8')
                        image=image.read() 
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        insert into officer_record(name,contact,email,joined_date,image) values('{name}','{contact}','{email}','{joined_date}',{psycopg2.Binary(image)}); 
                                    """,placeholder,"Added Successfully")
                        conn=db.connect_db() 
                        id=db.from_db(conn,f"Select max(id) from officer_record")
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        insert into authorized(id,username,password,role) values({id[0]},'{username}','{hashed}','Investigator'); 
                                    """,placeholder,"User Created")
                    
                    else:   
                        placeholder.error('All Fields Required')
                    time.sleep(3)
                    placeholder.empty() 
            #Update Investigator Form 
            with update.container(border=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Update Details</p>', unsafe_allow_html=True)
                username=st.selectbox('Select User ',placeholder='Select Investigator to update',options=allUsers,label_visibility='collapsed',index=allUsers.index(user))
                conn=db.connect_db() 
                userdata=db.from_db(conn,f"Select id,password,role from authorized where username='{username}'")
                conn=db.connect_db()
                userdetail=db.from_db(conn,f"""
                                        SELECT name, image, email, contact from officer_record where id={userdata[0]};
                                    """)

                name=st.text_input('Name',placeholder="Full Name",label_visibility='collapsed',value=userdetail[0])
                key=st.text_input('Passkey',placeholder='Pass Key',label_visibility='collapsed',type='password')
                email=st.text_input('Email',placeholder='email',label_visibility='collapsed',value=userdetail[2])
                contact=st.text_input('Contact',placeholder='contact',label_visibility='collapsed',value=userdetail[3])
                image=st.file_uploader('Image',type=['jpg','jpeg','png'])
                
                if st.button('Update',use_container_width=True) and username:
                    placeholder=st.empty() 
                
                    if key.strip():
                        if bcrypt.checkpw(key.encode(),  binascii.unhexlify(userdata[1])):
                            placeholder.error('Same as old password')
                        else:
                            password=db.hash_generator(key)
                            hashed=binascii.hexlify(password).decode('utf-8')
                            db.run_query(conn,f"""
                                            update authorized set password='{hashed}' where username='{username}'; 
                                        """,placeholder,"Added Successfully")

                    if contact.strip():
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        update officer_record set contact='{contact}' where id={userdata[0]}; 
                                    """,placeholder,"Added Successfully")

                    if email.strip():
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        update officer_record set email='{email}' where id={userdata[0]}; 
                                    """,placeholder,"Added Successfully")
                    if image:
                        image=image.read() 
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        update officer_record set image={psycopg2.Binary(image)} where id={userdata[0]}; 
                                    """,placeholder,"Added Successfully")

                    if not image and not email.strip() and not contact.strip() and not key.strip():   
                        placeholder.error('NO records to update')

            with delete.container(border=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Remove User</p>', unsafe_allow_html=True)
                conn=db.connect_db()
                db_users=db.get_all(conn,"select username from authorized where role != 'Administrator'")
                if db_users:    
                    remove_opt=[users[0] for users in db_users]
                    to_remove=st.selectbox('UserName',placeholder='Select User to remove',options=remove_opt)
                    conn=db.connect_db() 
                    remove_user_detail=db.from_db(conn,f"""select name,role,image,last_logged_in,email,contact,authorized.id
                                from authorized INNER JOIN officer_record 
                                ON authorized.id=officer_record.id
                                where authorized.username='{to_remove}'""")
                    st.write(
                        f"""
                                <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                        <img src="data:image/png;base64,{base64.b64encode(remove_user_detail[2]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                        <p style='margin-bottom: 5px; font-size: 20px; font-weight: bold;'>{remove_user_detail[1]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Name:</b> {remove_user_detail[0]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Username:</b> {to_remove}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>email:</b> {remove_user_detail[4]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Contact:</b> {remove_user_detail[5]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Last Logged In:</b> {remove_user_detail[3]}</p>
                        <p>  </p>
                        
                    </div>
                    """,
                    unsafe_allow_html=True
                    )
                    placeholder=st.empty() 
                    st.write('')
                    conn=db.connect_db()
                    live_case=db.from_db(conn,f"""
                                        Select count (case_id) from officer_and_cases where officer_id={remove_user_detail[6]} and status='ongoing' and enrollment='active'
                                """)
                    if st.button('Remove',use_container_width=True):
                        if live_case[0]==0:
                            conn=db.connect_db() 
                            db.run_query(conn,f"""Delete from authorized where username='{to_remove}';
                                                insert into officer_archive(id,left_date) values({remove_user_detail[6]},'{datetime.datetime.now().date()}');
                                        """,placeholder,"Removed Successfully")
                        else:
                            placeholder.error(f'Unable to Remove: {remove_user_detail[0]} has {live_case[0]} enrolled cases.')
                        time.sleep(3)
                        placeholder.empty() 
                else:
                    st.write('No Users available')


                
        # Left column: Details of the LoggedInUser
        with left_column.container(border=True):
            st.write(
                f"""
                    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                    <img src="data:image/png;base64,{base64.b64encode(system_admin[2]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                    <p style='margin-bottom: 5px; font-size: 20px; font-weight: bold;'>{system_admin[1]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Name:</b> {system_admin[0]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Username:</b> {user}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>email:</b> {system_admin[4]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Contact:</b> {system_admin[5]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Last Logged In:</b> {system_admin[3]}</p>
                    <p>  </p>
                    
                </div>
                """,
                unsafe_allow_html=True
            )

            if system_admin[1] == 'Administrator':
                c1,c2,c3=st.columns([1,2,1])
                with c2.popover('Handover',use_container_width=True):
                    conn=db.connect_db()
                    db_users=db.get_all(conn,"select username from authorized where role != 'Administrator'")
                    if db_users:    
                        opt=[users[0] for users in db_users]
                        to_user=st.selectbox('Assign Administrator',options=opt,index=None,placeholder='Select Administrator')
                        state=st.radio('Assign',['Assign Only','Assign and Leave'],label_visibility='collapsed')
                        placeholder=st.empty() 
                        if st.button(state,use_container_width=True):
                            if to_user:
                                conn=db.connect_db() 
                                if state=='Assign Only':
                                    db.run_query(conn,f"""
                                                    update authorized set role='Administrator' where username='{to_user}';
                                                    update authorized set role='Investigator' where username='{user}';
                                                """,placeholder,"Updated Successfully")
                                else:
                                    db.run_query(conn,f"""
                                                    update authorized set role='Administrator' where username='{to_user}';
                                                    delete from authorized where username='{user}';
                                                """,placeholder,"Updated Successfully")
                                    st.session_state.logged_in=False 
                                time.sleep(3)
                                placeholder.empty() 
                                st.rerun()  
                            else:
                                placeholder.error('No user selected.')

        # Display the authorized users dataframe // User Log Display Section 
        if system_admin[1]=='Administrator':
            left_column.write('<p style="color: white; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">User Logs</p>', unsafe_allow_html=True)
            left_column.dataframe(data, hide_index=True,use_container_width=True,height=144)

        #Display the information of system administrator 
        if system_admin[1] !='Administrator':
            conn=db.connect_db() 
            system_admin=db.from_db(conn,f"""select name,role,image,last_logged_in,email,contact 
                        from authorized INNER JOIN officer_record 
                        ON authorized.id=officer_record.id
                        where authorized.role='Administrator'""")
            with right_column.container(border=True):
                st.write(
                    f"""
                        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                        <img src="data:image/png;base64,{base64.b64encode(system_admin[2]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                        <p style='margin-bottom: 5px; font-size: 20px; font-weight: bold;'>{system_admin[1]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Name:</b> {system_admin[0]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Username:</b> {user}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>email:</b> {system_admin[4]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Contact:</b> {system_admin[5]}</p>
                        <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Last Logged In:</b> {system_admin[3]}</p>
                        <p>  </p>
                        
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    except Exception as e:
        st.error(f'Something Wrong with database: {e}')
    
    db.footer() 

if __name__=='__main__':
    auth_interface('jay') 