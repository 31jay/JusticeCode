import streamlit as st
from streamlit_option_menu import option_menu 
import database as db 
import bcrypt
import datetime
import binascii
import caseReport 
import officers
import authorized
import case_mapping   
import dashboard 
import downloads

st.set_page_config(
    page_icon='icons/icon.png',
    page_title=f'{db.PROJECT}',
    layout='wide'
)

if 'loggedin_user' not in st.session_state:
    st.session_state.loggedin_user=None


def landing_page():
    with st.sidebar:
        st.image("icons\\criminova.gif",use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)  
        selected=option_menu(
            menu_title='',options=['Dashboard','New Report','Case Reports','Investigators','Authorized ','Case Mapping','Downloads'],
            styles={
        "container": {"padding": "0!important", "background-color": " #333333"},
        "icon": {"color": "white", "font-size": "15px"}, 
        "nav-link": {"font-size": "15px", "text-align": "justify", "margin":"0px", "--hover-color": "#595959"},
        "nav-link-selected": {"background-color": " #00334d"}},
        icons=['boxes','file-earmark-plus-fill','file-text-fill','person-lines-fill','person-lines-fill','crosshair2','file-earmark-arrow-down-fill'])

        st.button('Log Out',on_click=logout,use_container_width=True)
    return selected


def new_case_report():
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - New Case Report</p>', unsafe_allow_html=True)
    with st.container(border=True):
        col1,col2=st.columns([1,1],gap='Large')
        with col1:
            conn=db.connect_db()
            case_count=db.from_db(conn,'SELECT MAX(caseNo) FROM CaseReports') 
            case_number=int()
            if case_count[0] is None:
                case_number=1
            else:
                case_number=int(case_count[0]) + 1 
            st.write(f'<h3 style= color:white; align=left; margin-top=0; font=sans-serif><u>Case No : {case_number}</u></h3> ',unsafe_allow_html=True)
            # Input Case Id : Var=case_id 
            case_id=st.text_input('Case Id: *',placeholder=' * Required')
            # Date of incident: Var= case_date 
            case_date=st.date_input('Date of Incident: *',max_value=datetime.datetime.now())
            # Crime Nature: var= nature_of case 

            connection=db.connect_db()
            db_cases=db.fetch_data(connection,fetch_attributes='nature_of_case',table_name='nature_of_case',data='all')
            
            cases=[]
            if db_cases is not None:
                cases = [case[0] for case in db_cases]
            cases.append('Other')
            nature_of_case = st.selectbox('Nature of Case: *', options=cases, placeholder='Select or type',index=None)
            cases.pop()
            if 'other_case' not in st.session_state:
                st.session_state.other_case=True  
            
            if nature_of_case == 'Other':
                st.session_state.other_case=False
                nature_of_case=''
            else:
                st.session_state.other_case=True

            other_nature=st.text_input('Nature of Case *',placeholder=nature_of_case,disabled=st.session_state.other_case)
            is_duplicate=False
            if cases:
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
            # Description of the case: var=case_description 
            case_description=st.text_area('Case Description',placeholder='Describe the case here.',height=20)
        with col2:
            st.write('<br><br>',unsafe_allow_html=True)
            #location of incident: var=lat, long 
            lat,lng=db.lat_long()

            # sub_col1,sub_col2=st.columns([1,1])
            # with sub_col2:
            submitted=st.button('Save Report',use_container_width=True)
        place=st.empty() 
    if submitted:
        warning.empty()
        if nature_of_case not in cases and nature_of_case:
            conn=db.connect_db()
            db.run_query(conn,f'''
            Insert into nature_of_case(nature_of_case) 
            values('{other_nature}')
            ''',slot=place)
            nature_of_case=other_nature

        if case_date and case_id and nature_of_case and lat and lng:
            conn=db.connect_db()
            db.run_query(conn,f'''
                        Insert into caseReports(caseNo,caseId,case_date,nature_of_case,case_description,lat,lng) 
                        values({case_number},'{case_id}','{case_date}','{nature_of_case}','{case_description}',{lat},{lng});
                        UPDATE nature_of_case SET case_count=case_count+1 WHERE nature_of_case='{nature_of_case}';
                        Insert into case_timeline(caseid,date,activity) values('{case_id}','{datetime.datetime.now().date()}','Case Registered')
                        ''',
                        msg='Case Reported Successfully !',slot=place)
        else:
            st.error('Fill all the required fields.')


def login():
    st.session_state.logged_in=True 


def logout():
    st.session_state.logged_in=False


# Main app
def main():
    # Persistent session state to keep track of the user's login status
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False


    # Login form
    if st.session_state['logged_in']==False:
    # 3 columns to center the gif image in the ratio 1:3:1
        col1,col2,col3=st.columns([3,3,3],gap="medium")
        with col2:
            st.markdown("<br><br><br><br>", unsafe_allow_html=True)      
            slot1=st.empty()
            slot1.image('icons/criminova.gif',use_column_width=True)

            st.markdown("<br>", unsafe_allow_html=True)  
            #text input for username  
            slot2=st.empty()   
            username=slot2.text_input('User Name:',type="default",label_visibility='collapsed',placeholder='UserName')
            
            #text input for password
            slot3=st.empty()
            password=slot3.text_input('Password',type="password",label_visibility='collapsed',placeholder='Password')

            sub_column1, sub_column2,sub_column3=st.columns([3,2,3])
            with sub_column2:
                slot4=st.empty()
                submitted=slot4.button('Login',use_container_width=True)
            with col2:
                if submitted:
                    conn=db.connect_db()
                    hashed_password=db.fetch_data(conn,table_name='authorized',check_attributes=f"username='{username}'",fetch_attributes='password',data='one')
                    if hashed_password is not None:  # Check if user exists
                        if bcrypt.checkpw(password.encode(),  binascii.unhexlify(hashed_password[0])):  # Access the hashed password from the fetched result
                            slot5=st.empty()
                            slot5.success('Validation Successful')
                            st.session_state.loggedin_user=username
                            st.session_state.logged_in=True
                            conn=db.connect_db() 
                            db.run_query(conn,f"Update authorized set last_logged_in='{datetime.datetime.now()}' where username='{username}'",slot=slot5)
                            slot1.empty()
                            slot2.empty()
                            slot3.empty()
                            slot4.empty()
                            slot5.empty()
                        else:
                            st.error('Invalid Password')
                    else:
                        st.error('User not found')    
    # After login
    if st.session_state['logged_in']:
        return landing_page()

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

if __name__ == "__main__":

# Call the function and apply CSS globally
    local_css("styles.css")
    user_exist=None 
    selected=main()
    if st.session_state.logged_in:
        conn=db.connect_db() 
        user_exist=db.from_db(conn,f"select id from authorized where username='{st.session_state.loggedin_user}'")
    if user_exist:    
        if selected=='New Report':
            new_case_report()
            db.footer()
        elif selected=='Case Reports':
            caseReport.case_investigation(st.session_state.loggedin_user) 
        elif selected=='Investigators':
            officers.main() 
        elif selected=='Authorized ':
            authorized.auth_interface(st.session_state.loggedin_user) 
        elif selected=='Case Mapping':
            case_mapping.main() 
        elif selected=='Dashboard':
            dashboard.main(st.session_state.loggedin_user) 
        elif selected=='Downloads':
            downloads.main(st.session_state.loggedin_user) 
    else:
        st.session_state.logged_in=False 
    