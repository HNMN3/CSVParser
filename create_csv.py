import csv
from collections import defaultdict
from datetime import datetime
import sys


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
    out_file_obj = open('output.csv', 'w')
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


if __name__ == '__main__':
    file_name = sys.argv[1]
    main(file_name)
