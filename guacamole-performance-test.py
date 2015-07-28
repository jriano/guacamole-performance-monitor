#!/usr/bin/python
#
# Juan C. Riano
#
# Requirements:
# - Linux Kernel 3.13, Debian Family running Guacamole 0.9.6
# - Python 2.7
# - Pygal library (for charts)
# - Sysstat packate (mpstat for measuginf CPU activity)
# - free command (to measure memory usage)
#
# Output:
# This script produces 2 log files and 3 charts.
# - gt_logs.txt (logs step by step activity as it happens)
# - gt_csv_logs.csv (logs memory and cpu values as new connections are added)
# - gt_chart_mixed_svg (Line charts of memory and CPU usage as connections are added)
# - gt_chart_mem.svg (Line chart of memory usage as connections are added)
# - gt_chart_cpu.svg (Line chart of CPU usage as connections are added)


"""
Script to test memory and CPU usage of a Guacamole Gateway installation.

This script is meant to be used in a runnning Guacamole Gateway, and it 
measures memory and CPU usage as RDP, VNC or SSH connections are added.

Each time a new connection is added, the script, which is monitoring 
/var/log/syslog
will proceed to measure memory and CPU usage and store it in 2 log files.

When the script is terminated (ctrl-c) the script proceeds to close the logs and 
to create 3 line charts with the information saved in some lists.

usage:
$ sudo python performanc-test.py /syslog_file_name
where /syslog_file_name is /var/sys/syslog for Debian systems.
"""


from sys import exit
from sys import argv
import time
import re
import subprocess
import pygal
from pygal.style import LightColorizedStyle
import csv

script_name, syslog_file_name = argv

# output files
results_file_name = "gt_logs.txt"
results_csv_file_name = "gt_csv_logs.csv"
mixed_chart_file_name = "gt_chart_mixed.svg"
mem_chart_file_name = "gt_chart_mem.svg"
cpu_chart_file_name = "gt_chart_cpu.svg"

# input and ouput files initialization 
try:
    syslog_file = open(syslog_file_name, "r")
    results_csv_file = open(results_csv_file_name, "w")
    results_file = open(results_file_name, "w")
    mixed_chart_file = open(mixed_chart_file_name, "w")
    mem_chart_file = open(mem_chart_file_name, "w")
    cpu_chart_file = open(cpu_chart_file_name, "w") 
except IOError:
    print("Error opening file, please check that the syslog file location is correct.")
    exit(1)


def increase_connections(connections, list):
    """Increases the number of active connections."""
    list.append(str(connections + 1))
    return connections + 1


def decrease_connections(connections, list):
	"""Decreases the number of active connections."""
    con = 0
    if connections > 1: 
        con = connections - 1
    list.append(str(con))
    return con


def log_line(results_file, line):
	"""Prints a log line to the console, and save it to a log file."""
    outline = line.strip()
    print(outline)
    results_file.write(outline + '\n')


def log_memory(results_file, list):
	"""Creates a log line of memory usage and calls the logger functions to store it."""
    line = subprocess.check_output('free | grep Mem | awk \'{ print $2 " " $3}\'', shell = True)
    words = line.strip('\t\r\n')
    total_mem, used_mem = words.split(' ')
    total_mem = float(total_mem)
    used_mem = float(used_mem)
    mem_usage = round(used_mem * 100.00 / total_mem, 2)
    memory_line = "Memory | Total: %.0f | Used: %.2f%%" % (total_mem, mem_usage)
    log_line(results_file, memory_line)
    list.append(mem_usage)
    return mem_usage


def log_cpu(results_file, list):
	"""Creates a log line of CPU usage and calls the logger functions to store it."""
    line = subprocess.check_output('mpstat -P ALL 1 1 | grep all | grep Average | awk \'NR==1{ print $3 }\'', shell = True)
    word = line.strip(' \n\t\r') 
    cpu_usage = round(float(word), 2)
    cpu_line = "CPU usage: %.2f%%" % cpu_usage 
    log_line(results_file, cpu_line)
    list.append(cpu_usage)
    return cpu_usage


def log_connections(results_file, connections):
	"""Creates a log line with the number of active connections and calls the logger functions to store it."""
    connections_line = "Number of active conections: {0:d}".format(connections)
    log_line(results_file, connections_line)


def is_a_connection(line):
	"""Takes a line from the syslog_file and determines if a new connection is about to happen."""
    match = re.search(r'guacd', line)
    match2 = re.search(r'Connection ID', line)
    if match and match2:
        return True
    return False


def is_established_connection(line):
	"""Takes a line from the syslog_file and determines if a new connection has started."""
    match = re.search(r'guacd', line)
    match2 = re.search(r'Starting client', line)
    if match and match2:
        return True
    return False


def is_disconnection(line):
	"""Takes a line from the syslog_file and determines if a connection was terminated."""
    match = re.search(r'guacd', line)
    match2 = re.search(r'Client disconnected', line)
    if match and match2:
        return True
    return False


def create_mixed_chart(connections, memory, cpu, file_name):
	"""Creates a line chart for memory and CPU usage, and saves it to file_name. 
	Input:
	- connections (list): number of connections (can go up and down)
	- memory (list) with the memory values corresponding to the connections.
	- cpu (list) witht the cpu values corresponding to the connections.
	""" 
    line_chart = pygal.Line(title=u'Guacamole Impact on Server Performance', x_title='Connections', x_label_rotation=45, width=1300, style=LightColorizedStyle)
    line_chart.x_labels = connections
    line_chart.add("Memory_%", memory)
    line_chart.add("CPU_%", cpu, secondary=True)
    line_chart.render_to_file(file_name) 


def create_mem_chart(connections, memory, file_name):
	"""Creates a line chart for memory and CPU usage, and saves it to file_name. 
	Input:
	- connections (list): number of connections (can go up and down)
	- memory (list) with the memory values corresponding to the connections.
	""" 
    line_chart = pygal.Line(title=u'Guacamole Impact on Server Performance', x_title='Connectionss', x_label_rotation=45, width=1300, style=LightColorizedStyle)
    line_chart.x_labels = connections
    line_chart.add("Memory_%", memory)
    line_chart.render_to_file(file_name) 

def create_cpu_chart(connections, cpu, file_name):
	"""Creates a line chart for memory and CPU usage, and saves it to file_name. 
	Input:
	- connections (list): number of connections (can go up and down)
	- cpu (list) witht the cpu values corresponding to the connections.
	""" 
    line_chart = pygal.Line(title=u'Guacamole Impact on Server Performance', x_title='Connections', x_label_rotation=45, width=1300, style=LightColorizedStyle)
    line_chart.x_labels = connections
    line_chart.add("CPU_%", cpu)
    line_chart.render_to_file(file_name) 


def collect_guacamole_logs(logs_file, 
                           out_file, 
                           out_csv_file,
                           mixed_chart_file, 
                           mem_chart_file, 
                           cpu_chart_file):
    """This is the function that drives the log collection. It needs:
    - logs_file: The file of the system logs (default is /sys/log/syslog)
    - out_file (output txt log file)
    - out_csv_file (output log file in .csv format)
    - and the names for the 3 chart files
    """
    # variables with initial values
    number_of_connections = 0
    initial_memory_usage = 0.00
    final_memory_usage = 0.00
    initial_cpu_usage = 0.00
    final_cpu_usage = 0.00
    csv_row = [] # a line of logs to store in the scv file

    # lists to store the values captured after each connection/disconnection.
    # this are the list that will be used to create the charts.
    number_of_connections_list = []
    cpu_usage_list = []
    memory_usage_list = []

    # set csv file for writing
    csv_writer = csv.writer(out_csv_file, delimiter=',')
    csv_writer.writerow(['Connections', 'Memory', 'CPU']) # header names
        
    # sets sys log file current position to start reading
    syslog_file.seek(0,2)
    
    # log current status values to log.
    log_line(out_file, "Start of Guacamole testing log capture:")
    log_line(out_file, "----------")
    log_line(out_file, "Initial memory and cpu usage:")
    initial_memory_usage = log_memory(out_file, memory_usage_list) 
    initial_cpu_usage = log_cpu(out_file, cpu_usage_list)
    log_line(out_file, "----------")

    # This block is the heart of the test. It keeps looking for connections/disconnections
    # in the sys log.
  	# it logs values and closes files when terminated with ctrl-c
    try:
        while True:
            line = logs_file.readline()
            if not line:
                time.sleep(0.1)
                continue
            else:
                if is_a_connection(line):
                    log_line(out_file, line)
                elif is_established_connection(line):
                    number_of_connections = increase_connections(number_of_connections, number_of_connections_list)
                    log_line(out_file, line)
                    final_memory_usage = log_memory(out_file, memory_usage_list)
                    final_cpu_usage = log_cpu(out_file, cpu_usage_list)
                    log_connections(out_file, number_of_connections)
                    log_line(out_file, "----------")
                    csv_writer.writerow([number_of_connections, final_memory_usage, final_cpu_usage])
                elif is_disconnection(line):
                    number_of_connections = decrease_connections(number_of_connections, number_of_connections_list)
                    log_line(out_file, line)
                    final_memory_usage = log_memory(out_file, memory_usage_list)
                    final_cpu_usage = log_cpu(out_file, cpu_usage_list)
                    log_connections(out_file, number_of_connections)
                    log_line(out_file, "----------")
                    csv_writer.writerow([number_of_connections, final_memory_usage, final_cpu_usage])

    except KeyboardInterrupt:
        raw_input() #capture the ctrl-c character so it does not go into log file
        log_line(out_file, "End of Guacamole testing log capture")

        # log capture finished, show initial and final values:
        log_line(out_file, "----------") 
        log_line(out_file, "Initial values:")
        log_line(out_file, "")
        log_line(out_file, "Memory usage: %.2f%%" % initial_memory_usage)
        log_line(out_file, "CPU usage: %.2f%%" % initial_cpu_usage)
        log_line(out_file, "")
        log_line(out_file, "Final values:")
        log_line(out_file, "Memory usage: %.2f%%" % final_memory_usage)
        log_line(out_file, "CPU usage: %.2f%%" % final_cpu_usage)
        log_line(out_file, "----------") 

        # create charts
        create_mixed_chart(number_of_connections_list, memory_usage_list, cpu_usage_list, mixed_chart_file_name)
        create_mem_chart(number_of_connections_list, memory_usage_list, mem_chart_file_name)
        create_cpu_chart(number_of_connections_list, cpu_usage_list, cpu_chart_file_name)



# run program!
collect_guacamole_logs(syslog_file, 
                       results_file, 
                       results_csv_file,
                       mixed_chart_file, 
                       mem_chart_file, 
                       cpu_chart_file)

# we are done! close files
syslog_file.close()
results_file.close()
results_csv_file.close()
print("Good bye...")
