import database as db 
import streamlit as st
import datetime
import plotly.express as px
import pandas as pd



def get_all_messages():
    conn=db.connect_db() 
    msgs=db.get_all(conn,"select * from messages order by date,time")
    return msgs 

def store_message():
    st.session_state.store_message=True


def msg(user):
    if 'store_message' not in st.session_state:
        st.session_state.store_message=False 
    with st.container(height=400):
        msgs=get_all_messages() 
        image='icons\\chat.jpg' 
        if msgs:
            for date,m_time,message,username in msgs:
                if date==datetime.datetime.now().date():
                    date='Today'
                time=f"{m_time.hour}:{m_time.minute}"
                st.write(f"""<p style="font-size: 10px; color: {db.headText};  margin-bottom: -100px; text-align: center;" >{username}::{date},{time} </p>
                         """,unsafe_allow_html=True) 
                st.chat_message(username,avatar=image).write(f"""<p style="margin-top: -10px" >{message}</p>""",unsafe_allow_html=True)
        else:
            st.chat_message('Begin Conversation',avatar="icons\\criminova.gif").write('Start Messaging')
    your_message=st.chat_input(on_submit=store_message)
    placeholder=st.empty() 
    if st.session_state.store_message:
        your_message=your_message.replace("'","''")
        conn=db.connect_db() 
        db.run_query(conn,f"""Insert into messages(date, time, message, username) 
                            values('{datetime.datetime.now().date()}','{datetime.datetime.now().time()}','{your_message}','{user}')
                    """,slot=placeholder)
        st.session_state.store_message=False 
        st.rerun() 


def hot_cases():
    conn = db.connect_db() 
    hot_cases = db.get_all(conn, """
                     SELECT nature_of_case, case_count FROM nature_of_case WHERE case_count > 0
                     """)
    try:
        cases_df = pd.DataFrame(hot_cases, columns=['Nature of Case', 'Case Count'])
        # Create a Plotly bar chart
        fig = px.bar(cases_df, x='Case Count', y='Nature of Case', orientation='h', 
                    # title='Hot Cases by Nature', 
                    labels={'Nature of Case': 'Nature of Case'},
                    width=500, height=300, 
                    hover_name='Nature of Case',
                    hover_data='Case Count',
                    barmode='overlay', # Group bars together
                    color_discrete_sequence=['#0066ff'], # Set bar color
                    )    
        st.plotly_chart(fig,use_container_width=True)
    except Exception:
        st.error('Insufficient Records to generate')

# Load daily new cases data
def daily_cases():
    conn = db.connect_db() 
    daily_new_cases = db.get_all(conn, """SELECT case_date AS Date, COUNT(*) AS New_Cases
                                           FROM caseReports
                                           GROUP BY case_date
                                           ORDER BY case_date;
                                        """)
    try:
        # Convert the result to a DataFrame with proper column names
        dataframe = pd.DataFrame(daily_new_cases, columns=['Date', 'New_Cases'])
        
        # Ensure that 'Date' column is of datetime type
        dataframe['Date'] = pd.to_datetime(dataframe['Date'])
        # Check if there are valid dates
        if not dataframe['Date'].isnull().all():
            # Reindex the DataFrame to ensure all dates are included
            min_date = dataframe['Date'].min()
            max_date = dataframe['Date'].max()
            if pd.notnull(min_date) and pd.notnull(max_date):
                all_dates = pd.date_range(start=min_date, end=max_date)
                dataframe = dataframe.set_index('Date').reindex(all_dates).fillna(0).reset_index()
                dataframe.columns = ['Date', 'New_Cases']
        
        # Create a line chart using Plotly Express
        fig = px.line(dataframe, x='Date', y='New_Cases', 
                      labels={'Date': 'Date', 'New_Cases': 'New Cases'},
                      width=800, height=400)
        
        # Display the line chart
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f'Something went wrong: {e}')


def cases_over_time():
    conn = db.connect_db() 
    cases_data = db.get_all(conn, """SELECT case_date AS Date,
                                            COUNT(*) AS Total_Cases,
                                            SUM(CASE WHEN casestatus = 'solved' THEN 1 ELSE 0 END) AS Solved_Cases,
                                            SUM(CASE WHEN casestatus = 'closed' THEN 1 ELSE 0 END) AS Closed_Cases
                                     FROM caseReports
                                     GROUP BY case_date
                                     ORDER BY case_date;
                                  """)
    try:
        # Convert the result to a DataFrame with proper column names
        dataframe = pd.DataFrame(cases_data, columns=['Date', 'Total_Cases', 'Solved_Cases', 'Closed_Cases'])
        # Ensure that 'Date' column is of datetime type
        dataframe['Date'] = pd.to_datetime(dataframe['Date'])

        # Sort the dataframe by Date to ensure correct cumulative calculations
        dataframe.sort_values('Date', inplace=True)

        # Calculate cumulative sums for the case counts
        dataframe['Total_Cases'] = dataframe['Total_Cases'].cumsum()
        dataframe['Solved_Cases'] = dataframe['Solved_Cases'].cumsum()
        dataframe['Closed_Cases'] = dataframe['Closed_Cases'].cumsum()

        # Melt the DataFrame to long format for Plotly Express
        melted_df = dataframe.melt(id_vars=['Date'], var_name='Case_Status', value_name='Case_Count')
        
        # Create a line chart using Plotly Express
        fig = px.line(melted_df, x='Date', y='Case_Count', color='Case_Status',
                      labels={'Date': 'Date', 'Case_Count': 'Case Count', 'Case_Status': 'Case Status'},
                      width=800, height=400)
        
        # Display the line chart
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f'Something went wrong: {e}')


def combined_gender_chart():
    conn=db.connect_db() 
    # Get data for victims by gender
    victim_by_gender=db.get_all(conn,"""
                        SELECT gender AS Gender, COUNT(*) AS Total_Cases FROM victims
                        GROUP BY gender
                        ORDER BY gender
                            """)
    # Get data for suspects by gender
    conn=db.connect_db() 
    suspects_by_gender=db.get_all(conn,"""
                        SELECT gender AS Gender, COUNT(*) AS Total_Cases FROM suspects
                        GROUP BY gender
                        ORDER BY gender
                            """)
    try:
        # Convert the query results to DataFrames
        victims_df = pd.DataFrame(victim_by_gender, columns=['Gender', 'Total_Cases'])
        victims_df['Gender'] = victims_df['Gender'].fillna('Unidentified')
        victims_df['Gender'] = victims_df['Gender'].replace('None', 'Unidentified')
        victims_df = victims_df.groupby('Gender', as_index=False).sum()
        suspects_df = pd.DataFrame(suspects_by_gender, columns=['Gender', 'Total_Cases'])
        suspects_df['Gender'] = suspects_df['Gender'].fillna('Unidentified')
        suspects_df['Gender'] = suspects_df['Gender'].replace('None', 'Unidentified')
        suspects_df = suspects_df.groupby('Gender', as_index=False).sum()
        
        if not suspects_df.empty:
            # Merge the DataFrames
            combined_df = pd.merge(victims_df, suspects_df, on='Gender', suffixes=('_Victims', '_Suspects'), how='outer')
            combined_df['Gender'] = combined_df['Gender'].fillna('Unidentified')
            combined_df = combined_df.groupby('Gender', as_index=False).sum()

            # Create a combined clustered bar chart using Plotly Express
            fig = px.bar(combined_df, x='Gender', y=['Total_Cases_Victims', 'Total_Cases_Suspects'], 
                        #  title='Combined Victims and Suspects by Gender', 
                        labels={'Gender': 'Gender', 'value': 'Total Cases'},
                        width=800, height=400,
                        color_discrete_map={'Total_Cases_Victims': '#0066ff', 'Total_Cases_Suspects': 'orange'},
                        barmode='group',
                        )
            
            # Display the combined clustered bar chart
            st.plotly_chart(fig, use_container_width=True, labels={'Gender': 'Gender'})
        else:
            # Display only the available data for victims
            st.warning('Insufficient Data to generate')
    except Exception as e:
        # Display a warning message if any error occurs
        st.warning(f'Something went wrong: {e}')


# Display line chart for daily new cases
def main(user):
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Dashboard</p>', unsafe_allow_html=True)
    c1,c2=st.columns([2,1])
    with c1:
        with st.container(border=True):
            st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Cases Worm Graph </p>', unsafe_allow_html=True)
            cases_over_time() 
    with c2:
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold; text-align: center">ShoutBoard</p>', unsafe_allow_html=True)
        msg(user)
    with st.container(border=True):
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Daily Cases Trend</p>', unsafe_allow_html=True)
        daily_cases()
    with st.container(border=True):
        st.write('<p style="color: white; border-bottom: 1px solid white;font-size: 20px; font-weight: bold">Reported Cases</p>', unsafe_allow_html=True)
        hot_cases() 
    with st.container(border=True):
        st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Victims and Suspects by Gender</p>', unsafe_allow_html=True)
        combined_gender_chart()
    
    db.footer() 


if __name__=="__main__":
    main('31jay')

