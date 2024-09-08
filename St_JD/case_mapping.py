import streamlit as st 
from streamlit_folium import st_folium
from streamlit_folium import folium  
import branca 
import database as db 
   
def lat_long(query):
    conn=db.connect_db() 
    data=db.get_all(conn,query)
    return data

def map_lat_long(query,Additional=''):
    data=lat_long(query) 
    m = folium.Map(location=[27.724502,85.339213], zoom_start=14,height=800,width=400,control_scale=True,zoom_control=True) 
    if data:
        for location in data:
            conn = db.connect_db()
            cases = db.get_all(conn, f"select caseid,case_date,nature_of_case,case_description,casestatus from caseReports where lat={location[0]} and lng={location[1]} {Additional}")
            case_details = ""
            case_details = []
            if cases:
                for case in cases:
                    case_detail = f"""
                        <details>
                            <summary style="cursor: pointer; margin-bottom: 10px;">Case ID: {case[0]}</summary>
                            <div style="padding: 5px;">
                                <div style="border: 1px solid #ccc; border-radius: 5px; padding: 10px;">
                                    <p><strong>Date:</strong> {case[1]}</p>
                                    <p><strong>Nature of Case:</strong> {case[2]}</p>
                                    <p><strong>Description:</strong> {case[3]}</p>
                                    <p><strong>Status:</strong> {case[4]}</p>
                                </div>
                            </div>
                        </details>
                        """
                    case_details.append(case_detail)
                all_case_details = "\n".join(case_details)
            else:
                all_case_details = "<p>No cases found at this location</p>"
            iframe = branca.element.IFrame(html=all_case_details, width=250, height=150)
            popup = folium.Popup(iframe, max_width=500)
            folium.Marker([location[0],location[1]],popup=popup).add_to(m)
        all_lat = ", ".join(str(location[0]) for location in data)
        all_lng = ", ".join(str(location[1]) for location in data)
        conn=db.connect_db() 
        total_cases=db.from_db(conn,f"select count (caseid) from caseReports where  lat IN ({all_lat}) and lng IN ({all_lng}) {Additional}")
        conn=db.connect_db() 
        ongoing_cases=db.from_db(conn,f"select count (caseid) from caseReports where lat IN ({all_lat}) and lng IN ({all_lng}) {Additional} and casestatus='ongoing'")
        conn=db.connect_db() 
        closed_cases=db.from_db(conn,f"select count (caseid) from caseReports where  lat IN ({all_lat}) and lng IN ({all_lng}) {Additional} and casestatus='closed'")
        conn=db.connect_db() 
        solved_cases=db.from_db(conn,f"select count (caseid) from caseReports where  lat IN ({all_lat}) and lng IN ({all_lng}) {Additional} and casestatus='solved'")
        html_content = f"""
                <div style="display: flex; justify-content: center; background-color: #f0f0f0; padding: 5px; transparency: 50%; border-radius: 0px; align-items: center;">
                    <div style="display: inline-block; margin-right: 50px; text-align: center;">
                        <p style="color: #333333; margin-top: 8px;  line-height: 0.5">Total Cases: {total_cases[0]}</p>
                    </div>
                    <div style="display: inline-block; margin-right: 50px; text-align: center;">
                        <p style="color: #333333; margin-top: 8px;  line-height: 0.5">Ongoing Cases: {ongoing_cases[0]}</p>
                    </div>
                    <div style="display: inline-block; margin-right: 50px; text-align: center;">
                        <p style="color: #333333; margin-top: 8px; line-height: 0.5">Solved Cases: {solved_cases[0]}</p>
                    </div>
                    <div style="display: inline-block; margin-right: 50px; text-align: center;">
                        <p style="color: #333333; margin-top: 8px; line-height: 0.5">Closed Cases: {closed_cases[0]}</p>
                    </div>
                </div>

                    """

        st.markdown(html_content, unsafe_allow_html=True)
        st_folium(m, use_container_width=True,height=600,returned_objects=[])
    else:
        st.warning('No records Found')

def main(): 
    st.write(f'<p style="color: {db.headText}; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Case Mapping</p>', unsafe_allow_html=True)
    conn=db.connect_db() 
    db_cases=db.get_all(conn,"Select nature_of_case from nature_of_case where case_count>0")
    try :
        nature_of_case=[case[0] for case in db_cases]
        filters=st.multiselect("Filter by Nature of Case",placeholder="Select Case Natures",options=nature_of_case,default=None)
        st.write('<br>',unsafe_allow_html=True)
        if filters:
            filters_str = "'" + "', '".join(filters) + "'"
            query = f"SELECT lat, lng FROM caseReports WHERE nature_of_case IN ({filters_str})"
            map_lat_long(query,f"and nature_of_case IN ({filters_str})")
        else:
            map_lat_long("select lat, lng from caseReports") 
    except Exception as e:
        st.warning(f'Something went wrong: {e}')
    db.footer() 
    
if __name__=="__main__":
    main()