import psycopg2
import bcrypt 
from fuzzywuzzy import process
from streamlit_folium import st_folium
import folium 
import streamlit as st 

PROJECT = "CrimeNetX"
headText = "#66CCFF"

//DATABASE_CONFIG = {
    'user': 'postgres',
    'password': 'ahjd',
    'host': 'localhost',
    'port': '5432',
    'database': 'criminovadb'
}
# Fetch DATABASE_URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    st.error("DATABASE_URL environment variable is not set")

def hash_generator(password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return password_hash

def connect_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def fetch_data(conn,table_name,check_attributes,fetch_attributes,data):
    cursor = conn.cursor()
    cursor.execute(f"SELECT {fetch_attributes} FROM {table_name} WHERE {check_attributes}")
    if data == 'one':
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()
    cursor.close()
    return result

def fetch_data(conn, table_name, check_attributes=None,fetch_attributes='*',add='',data='one'):
    """
Fetches data from a specified table and attributes in a PostgreSQL database using psycopg2.

Parameters:
- conn: A psycopg2 connection object to the database.
- table_name: The name of the table from which to fetch data.
- check_attributes: A dictionary containing attributes and values for the WHERE condition.
- fetch_attributes: A list of strings representing the column names to fetch.
- data: Specifies whether to fetch 'one' record or 'all' records.

Returns:
- A list of tuples containing the requested data.
"""

    if data not in ('one', 'all'):
        raise ValueError("Invalid command. The command must be 'one' or 'all'.")

    try:
        values = tuple()
        if check_attributes is not None:
            query = f"SELECT {fetch_attributes} FROM {table_name} WHERE {check_attributes} {add}"
        else:
            query = f"SELECT {fetch_attributes} FROM {table_name}"
        with conn.cursor() as cur:
            cur.execute(query, values)
            if data == 'all':
                result = cur.fetchall()
            else:  # data == 'one'
                result = cur.fetchone()
            return result
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(error)
    except ValueError as e:
        st.error(e)
    finally:
        if conn is not None:
            cur.close()
            conn.close()


def run_query(conn, query,slot,msg=None):
    """
Manipulate the database with appropriate query 
Basically for inserting to databse and for those operations that returns nothing. 
Parameters:
- conn: A psycopg2 connection object to the database.
- query: Complete Valid SQL query--> str
- msg: A str message to pop with st.success after completion 
"""
    try: 
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit() 
            if msg is not None:
                slot.success(msg)
    except (Exception, psycopg2.DatabaseError) as e:
        slot.error(e)
    except ValueError as e:
        slot.error(e)
    finally:
        if conn is not None:
            cur.close()
            conn.close()


def from_db(conn, query):
    """
    Execute a query on the database and return the result.

    For those query that expects a single value like: count, sum, AVG, etc 

    Parameters:
    - conn: A psycopg2 connection object to the database.
    - query: Complete valid SQL query as a string.
    - msg: A str message to pop with st.success after completion 
    
    Returns:
    - result: The result of the query execution.
    """
    result = None
    try: 
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()  # Assuming the query returns a single value
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(error)
    except ValueError as e:
        st.error(e)
    finally:
        if conn is not None:
            cur.close()
            conn.close()
    return result


def get_all(conn, query):
    """
    Execute a query on the database and return the result.

    For those query that expects a single value like: count, sum, AVG, etc 

    Parameters:
    - conn: A psycopg2 connection object to the database.
    - query: Complete valid SQL query as a string.
    - msg: A str message to pop with st.success after completion 
    
    Returns:
    - result: The result of the query execution.
    """
    result = None
    try: 
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchall()  # Assuming the query returns a single value
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(error)
    except ValueError as e:
        st.error(e)
    finally:
        if conn is not None:
            cur.close()
            conn.close()
    return result



def lat_long():
    '''
        This function will use the streamlit_floium to display and manipulate the map and allows user to retrieve the latitude and longitude of the marker spot.

        Parameters: 
        No any parameters 

        Returns: 
        Two floating values for latitude and Longitude of the marker spot. 
    '''
    if 'last_lat' not in st.session_state:
        st.session_state.last_lat=27.724502
    if 'last_lng' not in st.session_state: 
        st.session_state.last_lng=85.339213

    m = folium.Map(location=[st.session_state.last_lat,st.session_state.last_lng], zoom_start=15,height=200,width=200) 
    folium.Marker([st.session_state.last_lat,st.session_state.last_lng]).add_to(m)

    st_data = st_folium(m, width=400,height=450)

    if st_data["last_clicked"] is not None:
        st.session_state.last_lat=st_data["last_clicked"]['lat']
        st.session_state.last_lng=st_data["last_clicked"]['lng']
        st.rerun()
    return st.session_state.last_lat, st.session_state.last_lng 


def check_for_duplicates(user_input, existing_cases):
    """
    Check if the user_input is a duplicate of any existing case nature.

    Parameters:
    - user_input: str, the nature of case entered by the user.
    - existing_cases: list, a list of strings containing existing case natures.

    Returns:
    - bool, str where the bool indicates if a duplicate was found,
      and the str is the name of the existing case nature that matches.
    """
    # Setting a threshold for considering a match as a duplicate
    threshold = 70  # This can be adjusted based on how strict you want the matching to be
    
    # Using fuzzywuzzy to find the closest match and its score
    closest_match, score = process.extractOne(user_input, existing_cases)
    
    # Checking if the closest match score exceeds our threshold
    if score >= threshold:
        return True, closest_match
    else:
        return False, ""
    
    
def footer():
    st.markdown("""
                <br>
                <hr>
                <p style="text-align:center;align-items:baseline;">Copyright@ CrimeNetX, 2023</p>
                """,unsafe_allow_html=True)    
