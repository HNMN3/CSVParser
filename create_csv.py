import csv
import sys


def main(input_file_name):
    file_obj = open(input_file_name)
    out_file_obj = open('output.csv', 'w')
    field_names = ['fram_count', 'faces', 'face_name', 'head_pose', 'emotion',
                   'action', ]
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
        for val in values:
            if not prev_val:
                prev_val = val
                continue
            prev_val = prev_val.strip(', ')
            if 'faces' in val:
                data = [faces, face_names, head_poses, emotions, actions]
                if fram_count:
                    while any(data):
                        row = [fram_count]
                        for var in data:
                            row.append(var.pop(0) if var else None)
                        writer.writerow(row)
                    fram_count = None
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
            else:
                key = ''
            prev_val = val[len(key):]

        data = [faces, face_names, head_poses, emotions, actions]
        while any(data):
            row = [fram_count]
            for var in data:
                row.append(var.pop(0) if var else None)
            writer.writerow(row)

    out_file_obj.close()
    print("CSV file saved!!")


if __name__ == '__main__':
    file_name = sys.argv[1]
    main(file_name)
