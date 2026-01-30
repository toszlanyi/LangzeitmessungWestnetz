import socket
import struct
import time
import csv
import os

# --- KONFIGURATION ---
SOLIS_IP = "192.168.178.105"
SOLIS_PORT = 502
UDP_IP = "0.0.0.0"
UDP_PORT = 14502
REPORT_INTERVALL = 10
CSV_INTERVALL = 120
CSV_FILE = "solar_log_v3_minmax.csv"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

east_buffer = {"u": [], "i": [], "p": [], "pf": [], "p_tot": []}
# Min/Max Speicher für das aktuelle CSV-Intervall
u_min = [999.0, 999.0, 999.0]
u_max = [0.0, 0.0, 0.0]

solis_data = {
    "v": [0.0,0.0,0.0], "p_ac": [0.0,0.0,0.0],
    "soc": 0, "strings": [0.0,0.0,0.0,0.0],
    "batt_p": 0.0, "batt_v": 0.0, "batt_i": 0.0
}

last_poll_time = time.time()
last_report_time = time.time()
last_csv_time = time.time()
last_reg = None

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "U_L1_Avg", "U_L1_Min", "U_L1_Max", "I_L1", "PF_L1",
            "U_L2_Avg", "U_L2_Min", "U_L2_Max", "I_L2", "PF_L2",
            "U_L3_Avg", "U_L3_Min", "U_L3_Max", "I_L3", "PF_L3",
            "P_Netz_Gesamt", "P_Haus", "PV_Watt", "Batt_Watt", "SOC"
        ])

def get_solis_data():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((SOLIS_IP, SOLIS_PORT))
        s.send(b'\x00\x01\x00\x00\x00\x06\x01\x04\x81\x19\x00\x16')
        r1 = s.recv(1024)
        s.send(b'\x00\x01\x00\x00\x00\x06\x01\x04\x81\x2f\x00\x46')
        r2 = s.recv(1024)
        s.send(b'\x00\x01\x00\x00\x00\x06\x01\x04\x81\x6d\x00\x08')
        r3 = s.recv(1024)
        s.close()
        if r1 and len(r1) > 10:
            d = r1[9:]
            raw_s = [(int.from_bytes(d[i*4:i*4+2],'big')/10 * int.from_bytes(d[i*4+2:i*4+4],'big')/10) for i in range(4)]
            solis_data['strings'] = [v if v < 11000 else 0.0 for v in raw_s]
        if r2 and len(r2) > 32:
            d = r2[9:]
            solis_data['v'] = [int.from_bytes(d[4:6],'big')/10, int.from_bytes(d[6:8],'big')/10, int.from_bytes(d[8:10],'big')/10]
            for i in range(3):
                p_bytes = d[20+(i*4):24+(i*4)]
                solis_data['p_ac'][i] = float(struct.unpack('>i', p_bytes)[0])
            solis_data['soc'] = int.from_bytes(d[136:138], 'big')
        if r3 and len(r3) > 10:
            d = r3[9:]
            solis_data['batt_v'] = int.from_bytes(d[0:2], 'big') / 10
            solis_data['batt_i'] = struct.unpack('>h', d[2:4])[0] / 10
            solis_data['batt_p'] = solis_data['batt_v'] * solis_data['batt_i']
    except: pass

def get_avg(key, is_list=True):
    samples = east_buffer[key]
    if not samples: return [0.0, 0.0, 0.0] if is_list else 0.0
    total_time = sum(s[1] for s in samples)
    if total_time == 0: return [0.0, 0.0, 0.0] if is_list else 0.0
    if is_list:
        return [sum(s[0][p] * s[1] for s in samples) / total_time for p in range(3)]
    return sum(s[0] * s[1] for s in samples) / total_time

print(f"--- Min/Max Logging gestartet (CSV: {CSV_FILE}) ---")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        now = time.time()
        dt = now - last_poll_time
        last_poll_time = now

        if len(data) == 8 and data[0] == 0x01 and data[1] == 0x04:
            last_reg = (data[2] << 8) + data[3]
            continue
        if len(data) > 5 and data[0] == 0x01 and data[1] == 0x04:
            payload = data[3:3+data[2]]
            floats = [struct.unpack('>f', payload[i:i+4])[0] for i in range(0, len(payload)-3, 4)]
            if last_reg is not None:
                if last_reg == 0:
                    east_buffer["u"].append((floats[:3], dt))
                    # Tracking von Min/Max pro Phase im laufenden Intervall
                    for idx in range(3):
                        if floats[idx] < u_min[idx]: u_min[idx] = floats[idx]
                        if floats[idx] > u_max[idx]: u_max[idx] = floats[idx]
                elif last_reg == 6:  east_buffer["i"].append((floats[:3], dt))
                elif last_reg == 12: east_buffer["p"].append(([v * -1 for v in floats[:3]], dt))
                elif last_reg == 30: east_buffer["pf"].append((floats[:3], dt))
                elif last_reg == 52: east_buffer["p_tot"].append((floats[0] * -1, dt))
                last_reg = None
    except BlockingIOError: pass

    now = time.time()

    if now - last_report_time >= REPORT_INTERVALL:
        get_solis_data()
        cur_u = get_avg("u")
        cur_p = get_avg("p")
        cur_i = get_avg("i")
        cur_pf = get_avg("pf")
        cur_p_tot = get_avg("p_tot", False)
        pv_p = sum(solis_data['strings'])
        haus_last = cur_p_tot + sum(solis_data['p_ac'])

        print(f"\n" + "="*95)
        print(f" STATUS {time.strftime('%H:%M:%S')} | SOC: {solis_data['soc']}% | PV: {pv_p:.1f} W")
        print("-" * 95)
        for idx in range(3):
            u_col = "\033[91m" if cur_u[idx] < 212 else ""
            print(f" L{idx+1} | {u_col}{cur_u[idx]:>5.1f} V\033[0m (Min:{u_min[idx]:>5.1f}) | {cur_i[idx]:>5.2f} A | P: {cur_p[idx]:>8.1f} W")
        print("-" * 95)
        print(f" NETZ: {cur_p_tot:>8.2f} W | HAUS: {max(0, haus_last):>8.2f} W")
        last_report_time = now

        if now - last_csv_time >= CSV_INTERVALL:
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                    round(cur_u[0], 2), round(u_min[0], 2), round(u_max[0], 2), round(cur_i[0], 2), round(abs(cur_pf[0]), 3),
                    round(cur_u[1], 2), round(u_min[1], 2), round(u_max[1], 2), round(cur_i[1], 2), round(abs(cur_pf[1]), 3),
                    round(cur_u[2], 2), round(u_min[2], 2), round(u_max[2], 2), round(cur_i[2], 2), round(abs(cur_pf[2]), 3),
                    round(cur_p_tot, 2), round(haus_last, 2), round(pv_p, 2),
                    round(solis_data['batt_p'], 1), solis_data['soc']
                ])
            # Reset Min/Max und Puffer für das nächste Intervall
            u_min = [999.0, 999.0, 999.0]
            u_max = [0.0, 0.0, 0.0]
            for k in east_buffer: east_buffer[k] = []
            last_csv_time = now

    time.sleep(0.01)
