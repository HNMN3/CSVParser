import csv
from datetime import datetime

import pandas as pd
import sys

# Update below variables to change the name of output files
CSV_OUTPUT_FILE_NAME = 'output.csv'
STATS_OUTPUT_FILE_NAME = 'statistics.csv'


def write_data(data, fram_count, subject, timestamp, writer):
    date_fmt = "%a %b  %d %H:%M:%S %Y"
    try:
        assert timestamp
        datetime_obj = datetime.strptime(timestamp, date_fmt)
        date = datetime_obj.strftime('%d-%m-%Y')
        time = datetime_obj.strftime('%H:%M:%S')
    except (AssertionError, ValueError):
        date, time = None, None

    while any(data):
        row = [fram_count]
        for var in data:
            row.append(var.pop(0) if var else None)
        row.append(subject)
        row.append(date)
        row.append(time)
        writer.writerow(row)


def main(input_file_name):
    file_obj = open(input_file_name)
    out_file_obj = open(CSV_OUTPUT_FILE_NAME, 'w')
    field_names = ['fram_count', 'faces', 'face_name', 'head_pose', 'emotion',
                   'action', 'subject', 'date', 'time']
    writer = csv.writer(out_file_obj)
    writer.writerow(field_names)

    for line in file_obj:
        line = line.strip()
        if not line or 'Next Fram' in line or 'Failed to insert data' in line:
            continue
        values = line.split('-')
        prev_val = None
        fram_count = None
        faces = list()
        face_names = list()
        head_poses = list()
        emotions = list()
        actions = list()
        subject = None
        timestamp = None
        for val in values:
            if not prev_val:
                prev_val = val
                continue
            prev_val = prev_val.strip(', ')
            if 'faces' in val:
                data = [faces, face_names, head_poses, emotions, actions]
                if fram_count:
                    write_data(data, fram_count, subject, timestamp, writer)
                    fram_count = None
                    subject = None
                    timestamp = None
                faces.append(prev_val)
                key = 'faces'
            elif 'fram_count' in val:
                fram_count = prev_val
                key = 'fram_count'
            elif 'name_and_action' in val:
                name, action = prev_val.split('(')
                face_names.append(name)
                actions.append(action[:-1])
                key = 'name_and_action'
            elif 'head_pose' in val:
                head_poses.append(prev_val)
                key = 'head_pose'
            elif 'emotion' in val:
                emotions.append(prev_val)
                key = 'emotion'
            elif 'subject' in val:
                subject = prev_val
                key = 'subject'
            elif 'time' in val:
                timestamp = prev_val
                key = 'time'
            else:
                key = ''
            prev_val = val[len(key):]

        data = [faces, face_names, head_poses, emotions, actions]
        write_data(data, fram_count, subject, timestamp, writer)

    out_file_obj.close()
    print("CSV file saved!!")
    prepare_statistics()


def prepare_statistics():
    # Reading file with parsed date time
    df = pd.read_csv(CSV_OUTPUT_FILE_NAME, parse_dates={'timestamp': ["date", "time"]})
    df = df[df.timestamp != 'nan nan']  # Removing rows with null date time
    df['timestamp_hour'] = (pd.to_datetime(df.timestamp)
                            .apply(lambda x: x.replace(minute=0, second=0)))
    fdf = df.groupby(['face_name', 'timestamp_hour']).apply(group_values)
    fdf.reset_index(drop=True).to_csv(STATS_OUTPUT_FILE_NAME, index=False)
    print("Statistics saved!!")


def group_values(df):
    face_name, day_time = df.name
    keys_to_evaluate = ['head_pose', 'emotion', 'action', ]
    final_data = {'total_fram': [len(df)],
                  'face_name': [face_name],
                  'subject': [df.subject.reset_index(drop=True)[0]],
                  'day_time': [day_time]}
    max_len = 1
    for key in keys_to_evaluate:
        stats = df[key].value_counts()
        stats_list = []
        for stat_key, stat_val in zip(stats.index, stats):
            stats_list.append('{}, {} time(s)'.format(stat_key, stat_val))
        final_data[key] = stats_list
        max_len = max(max_len, len(stats_list))
    columns = ['total_fram', 'face_name'] + keys_to_evaluate + ['subject', 'day_time']
    for col in columns:
        curr_size = len(final_data[col])
        if curr_size < max_len:
            padding = max_len - curr_size
            final_data[col] += [''] * padding
    return pd.DataFrame(final_data, columns=columns)


if __name__ == '__main__':
    file_name = sys.argv[1]
    main(file_name)
