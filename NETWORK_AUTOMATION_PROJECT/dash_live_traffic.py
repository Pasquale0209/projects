import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import time
import re

# App Dash
app = dash.Dash(__name__)

# Dati di esempio (sostituisci con i dati reali da iperf)
x_data = []
y_data = []
seen_times = set()  # Set per tenere traccia dei tempi già letti
start_time = time.time()  # Inizio del monitoraggio
flag = False

# Dati Jitter
x_data_jitter = []
y_data_jitter = []
seen_times_jitter = set()

def update_thr_data():
    # Leggi i dati dal file iperf_output.txt
    with open('iperf_h1.txt', 'r') as f:
        lines = f.readlines()
        for line in lines[:-2]:
            if 'Mbits/sec' in line:  # Cerca la metrica di throughput
                parts = line.strip().split()
                print(parts)
                if len(parts) > 6:
                    
                    idx_1 = parts.index('Mbits/sec')
                    idx_2 = parts.index('sec')
                    throughput = float(parts[idx_1 - 1])  # Esempio, Mbits/sec
                    #print(throughput)
                    if '-' in parts[idx_2 - 1]:
                        # Gestisci l'intervallo (0.0-1.0 sec)
                        time_interval = parts[idx_2 - 1].split('-')
                        print(time_interval)
                        end_time = float(time_interval[1])  # Fine dell'intervallo
                        print(end_time)
                    else:
                        # Gestisci la riga finale (0.0-50.0 sec)
                        end_time = float(parts[idx_2 - 1])  # Estrai l'ultimo tempo
                        print(end_time)

                    if end_time not in seen_times:
                        print(f'thr: {seen_times}')
                        seen_times.add(end_time)
                        #print(seen_times)
                        print(end_time)
                        x_data.append(end_time)
                        y_data.append(throughput)

def update_jitter_data():
    try:
        with open('iperf_h2.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'sec' in line and 'KBytes' in line and 'ms' in line:
                    parts = line.strip().split()
                    interval = parts[2]
                    start_str, end_str = interval.split('-')
                    end_time = float(end_str)

                    jitter_idx = parts.index('ms') - 1
                    jitter = float(parts[jitter_idx])

                    if end_time not in seen_times_jitter:
                        print(f'jitter:{seen_times_jitter}')
                        seen_times_jitter.add(end_time)
                        print(end_time)
                        x_data_jitter.append(end_time)
                        y_data_jitter.append(jitter)
    except FileNotFoundError:
        pass

if flag == False:
    app.layout = html.Div([
        html.H1("UDP Live Traffic Monitor (iPerf)"),
        html.Div([
            dcc.Graph(id='throughput-graph', style={'width': '90%', 'height': '300px'}),
            dcc.Graph(id='jitter-graph', style={'width': '90%', 'height': '300px'})
        ]),
        dcc.Interval(id='interval-update', interval=1000, n_intervals=0)
    ])
    flag = True

# Callback per aggiornare entrambi i grafici
@app.callback(
    [Output('throughput-graph', 'figure'),
     Output('jitter-graph', 'figure')],
    [Input('interval-update', 'n_intervals')]
)
def update_graphs(n):
    update_thr_data()
    update_jitter_data()

    fig_thr = go.Figure()
    fig_thr.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers', name='Throughput (Mbps)'))
    fig_thr.update_layout(title="Throughput (Mbit/s)", xaxis_title="Time (s)", yaxis_title="Throughput (Mbps)")

    fig_jitter = go.Figure()
    fig_jitter.add_trace(go.Scatter(x=x_data_jitter, y=y_data_jitter, mode='lines+markers', name='Jitter (ms)', line=dict(color='green')))
    fig_jitter.update_layout(title="Jitter (ms)", xaxis_title="Time (s)", yaxis_title="Jitter (ms)")

    return fig_thr, fig_jitter

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)







