import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

def load_data():
    cases_df = pd.read_csv('data/cases.csv')
    rotas_df = pd.read_csv('data/rotas.csv')
    return cases_df, rotas_df

def preprocess_data(cases_df, rotas_df):
    cases_df = cases_df[cases_df['rslid'] != "none"]
    cases_df['rslid'] = cases_df['rslid'].astype(int)
    merged_df = pd.merge(cases_df, rotas_df, left_on=["rslid", "cons_username"], right_on=["rslid", "adastra"]).drop_duplicates()
    return merged_df


def calculate_clinician_performance(merged_df):

    clinician_performance = (
        merged_df
        .groupby(['date', 'value'])
        .agg(
            Number_of_Cases=('rslid', 'count'),
            Total_Value=('value', 'mean')
        )
        .reset_index()
    )
    
    clinician_performance['Value_Per_Case'] = clinician_performance['Total_Value'] / clinician_performance['Number_of_Cases']

    return clinician_performance

def plot_clinician_value_per_case_over_time(consultant, data):
    fig = go.Figure()
    consultant_data = calculate_clinician_performance(data)
    fig.add_trace(go.Scatter(x=consultant_data['date'], y=consultant_data['Value_Per_Case'], mode='lines+markers', name=consultant))

    fig.update_layout(
        height=500,
        width=800,
        title=dict(text='Clinician Value Per Case Over Time', x=0.5, font=dict(size=16)),
        xaxis_title='Shift Date',
        yaxis_title='Value Per Case',
        legend_title='Consultant',
        font=dict(size=12),
        xaxis=dict(
            tickmode='linear',
            tick0=consultant_data['date'].min(),
        ),
        margin=dict(t=50, b=50, l=50, r=50)
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_cases_per_shift(merged_df):
    avg_case_shift = merged_df.groupby('date').size()
    
    merged_df["cons_start_time"] = pd.to_datetime(merged_df["cons_start_time"])
    merged_df["cons_end_time"] = pd.to_datetime(merged_df["cons_end_time"])
    merged_df['cons_time'] = merged_df['cons_end_time'] - merged_df['cons_start_time']
    constime_df = merged_df.groupby('date')['cons_time'].mean().reset_index()
    merged_df['duration_y'] = pd.to_timedelta(merged_df['duration_y'] + ":00")
    consumtime_df = merged_df.groupby(['timestart','date']).agg(
        cons_time_sum=('cons_time', 'sum'),
        mean_duration=('duration_y', 'mean')
    ).reset_index()
    consumtime_df['idle_time'] = consumtime_df['mean_duration'] - consumtime_df['cons_time_sum']
    
    consumtime_df['cons_time_sum_sec'] = consumtime_df['cons_time_sum'].dt.total_seconds()
    consumtime_df['mean_duration_sec'] = consumtime_df['mean_duration'].dt.total_seconds()
    consumtime_df['idle_time_sec'] = consumtime_df['idle_time'].dt.total_seconds()

    consumtime_df['total_time_sec'] = consumtime_df['cons_time_sum_sec'] + consumtime_df['idle_time_sec']
    consumtime_df['idle_time_pct'] = (consumtime_df['idle_time_sec'] / consumtime_df['total_time_sec']) * 100
    consumtime_df['consult_time_pct'] = (consumtime_df['cons_time_sum_sec'] / consumtime_df['total_time_sec']) * 100
    melted_df = consumtime_df.melt(id_vars=['date'], value_vars=['idle_time_pct', 'consult_time_pct'],
                               var_name='Time Type', value_name='Percentage')
    
    perc_timefig = px.bar(melted_df, x='date', y='Percentage', color='Time Type', 
             title='Percentage of Idle Time and Consulting Time Over Dates',
             labels={'Percentage': 'Percentage (%)', 'date': 'Date'})


    cons_fig = go.Figure()
    constime_df['cons_time'] = constime_df['cons_time'].dt.total_seconds() / 60

    cons_fig.add_trace(go.Scatter(x=constime_df['date'], y=constime_df['cons_time'], mode='lines+markers'))

    cons_fig.update_yaxes(
        tickformat=".2f",  # Format y-axis ticks as floating-point numbers with 2 decimal places
        tickfont_size=10
    )

    cons_fig.update_layout(
        height=500,
        width=800,
        title=dict(text='Average Consulting Time Per Shift', x=0.5, font=dict(size=16)),
        xaxis_title='Shift Date',
        yaxis_title='Consulting Time Per Shift (minutes)',
        font=dict(size=12),
        xaxis=dict(
            tickmode='linear',
            tick0=constime_df['date'].min(),
        ),
        margin=dict(t=50, b=50, l=50, r=50)
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Average Cases per Shift", f"{avg_case_shift.mean():.2f}")
    c2.metric("Total Cases", merged_df.shape[0])
    c3.metric("Total Shifts", avg_case_shift.count())
    shiftcat = merged_df['shiftcategory'].value_counts().reset_index()
    pie_fig = px.pie(shiftcat, values='count', names='shiftcategory', 
                    title='Shift Distribution',
                    color_discrete_sequence=px.colors.qualitative.Pastel)

    pie_fig.update_traces(textposition='inside', textinfo='percent+label')
    pie_fig.update_layout(
        showlegend=True,
        height=500,
        legend_title="Shift"
    )

    zones = merged_df['zone'].value_counts().reset_index()
    pie_fig_2 = px.pie(zones, values='count', names='zone', 
                    title='Zone Distribution',
                    color_discrete_sequence=px.colors.qualitative.Pastel)

    pie_fig_2.update_traces(textposition='inside', textinfo='percent+label')
    pie_fig_2.update_layout(
        showlegend=True,
        height=500,
        legend_title="zones"
    )


    cases_per_shift = avg_case_shift.reset_index(name='Number of Cases')
    fig = px.bar(
                 cases_per_shift, x='date', 
                 y='Number of Cases', 
                 title='Cases per Shift', 
                 labels={'date': 'Shift Date', 'Number of Cases': 'Number of Cases'},
                 )

    fig.update_layout(
        height=400,
        width=500,
        title=dict(x=0.5, font=dict(size=16)),
        xaxis_title='Shift Date',
        yaxis_title='Number of Cases',
        showlegend=False,
        font=dict(size=12),
        xaxis=dict(
            tickmode='linear',
            tick0=cases_per_shift['date'].min(),
            ),
        margin=dict(t=50, b=50, l=50, r=50)
    )

    st.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    col1.plotly_chart(pie_fig, use_container_width=True)
    col2.plotly_chart(pie_fig_2, use_container_width=True)
    st.plotly_chart(cons_fig, use_container_width=True)
    st.plotly_chart(perc_timefig, use_container_width=True)




def display_clinician_scoreboard(merged_df):
    rating_criteria = {
        'Extremely Satisfied': 5,
        'Satisfied': 4,
        'Neither Satisfied nor Dissatisfied': 3,
        'Dissatisfied': 2,
        'Extremely Dissatisfied': 1
    }

    merged_df['rating'] = merged_df['patient_satisfaction'].map(rating_criteria)
    unique_shifts_per_group = merged_df.groupby(['adastra', 'role']).apply(
            lambda group: len(group[['date', 'timestart']].drop_duplicates())
        ).reset_index(name='Total Shifts')
    clinician_performance = merged_df.groupby(['adastra', 'role']).agg(
        Total_Cases=('rslid', 'size'),
        Average_Rating=('rating', 'mean')
    )
    clinician_performance = pd.merge(clinician_performance, unique_shifts_per_group, on=['adastra', 'role'])
    clinician_performance['Average_Cases_Per_Shift'] = clinician_performance['Total_Cases'] / clinician_performance['Total Shifts']


    df_sorted = clinician_performance.sort_values(by='Average_Cases_Per_Shift', ascending=False).reset_index(drop=True)
    st.subheader("Clinician Scoreboard")
    st.dataframe(df_sorted.style.format({'Average_Cases_Per_Shift': '{:.2f}', 'Average_Rating': '{:.2f}'}), use_container_width=True)

def ensure_duration_format(duration_str):
    parts = duration_str.split(":")
    if len(parts) == 2:
        return duration_str + ":00"
    return duration_str

def plot_daily_hours_cost(data):
    data['duration_y'] = data['duration_y'].apply(ensure_duration_format)
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data['duration_hours'] = pd.to_timedelta(data['duration_y'], errors='coerce').dt.total_seconds() / 3600

    grouped_data = data.groupby(['date', 'role'], as_index=False).agg(
        total_hours=('duration_hours', 'sum'),
        total_cost=('value', 'sum')
    )

    fig_hours = px.line(grouped_data, x='date', y='total_hours', color='role',
                        title='Total Hours per Day by Role')

    fig_cost = px.line(grouped_data, x='date', y='total_cost', color='role',
                    title='Total Cost per Day by Role')

    st.subheader("Daily Hours and Cost by Role")
    st.plotly_chart(fig_hours)
    st.plotly_chart(fig_cost)

def plot_avg_case_type(df):
    average_cases_by_type = df['case_type'].value_counts().reset_index()
    average_cases_by_type.columns = ['Case_Type', 'Total_Cases']

    fig = px.bar(average_cases_by_type, 
                x='Total_Cases', 
                y='Case_Type', 
                title='Average Cases by Type of Case',
                labels={'Total_Cases': 'Number of Cases', 'Case_Type': 'Type of Case'}) 
                # color_continuous_scale='viridis')
    fig.update_layout( yaxis=dict(
                            tickmode='linear',
                            ),)

    st.title('Clinician Cases Dashboard')
    st.plotly_chart(fig)

def main():
    st.logo("BARDOC-Transparent-LOGO-350-x-100.webp")
    st.set_page_config(layout="wide", page_title="Clinician Performance Dashboard")
    st.title('Clinician Performance Dashboard')

    cases_df, rotas_df = load_data()
    merged_df = preprocess_data(cases_df, rotas_df)
    del cases_df, rotas_df

    role_headers = merged_df['role'].unique().tolist()
    role_headers.insert(0, '(All)')
    selected_role = st.sidebar.selectbox('Select Role', role_headers)
    if selected_role != "(All)":
        role_df = merged_df[merged_df['role'] == selected_role]
    else:
        role_df = merged_df
    
    del merged_df
    adastra_headers = role_df['adastra'].unique()
    selected_adastra = st.sidebar.selectbox('Select Clinician', adastra_headers)

    filtered_df = role_df[role_df['adastra'] == selected_adastra]

    display_clinician_scoreboard(role_df)
    plot_daily_hours_cost(role_df)
    plot_avg_case_type(role_df)

    if not filtered_df.empty:
        st.subheader(f'Performance for : {selected_adastra}')
        plot_cases_per_shift(filtered_df)
        plot_clinician_value_per_case_over_time(selected_adastra, filtered_df)
            
    else:
        st.write('No data available for the selected Adastra header.')

if __name__ == "__main__":
    main()