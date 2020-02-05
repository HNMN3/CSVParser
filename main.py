import math
import csv

import pandas as pd

CSV_FILE_NAME = 'input.csv'


def get_values(row, truth_arr):
    try:
        return row[truth_arr].reset_index(drop=True)
    except IndexError:
        return pd.Series()


def extract_single_values(row, pattern):
    try:
        value_series = row.str.extract(pattern)[0]
        return value_series[value_series.notna()].reset_index(drop=True)
    except IndexError:
        return pd.Series()


def get_distance(c1, c2):
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def arrange_coordinates(face_coordinates, other_coordinates, distance_threshold):
    face_coordinates_set = set(face_coordinates.values)
    other_coordinates_set = set(other_coordinates.values)

    distance_arr = list()
    for i, face_coordinate in face_coordinates.iteritems():
        for j, other_coordinate in other_coordinates.iteritems():
            distance = get_distance(face_coordinate, other_coordinate)
            distance_arr.append((i, j, face_coordinate, other_coordinate, distance))
    distance_arr.sort(key=lambda x: x[4])

    final_positions = pd.Series([None] * face_coordinates.size)
    position_moved_data = {}
    for i, j, face_coordinate, other_coordinate, distance in distance_arr:
        if (face_coordinate not in face_coordinates_set
                or other_coordinate not in other_coordinates_set
                or distance > distance_threshold):
            continue
        face_coordinates_set.remove(face_coordinate)
        other_coordinates_set.remove(other_coordinate)

        final_positions[i] = other_coordinate
        position_moved_data[j] = i

    remaining_data = pd.Series(list(other_coordinates_set))
    return final_positions, remaining_data, position_moved_data


def extract_two_values(row, pattern):
    try:
        assert pattern  # Return if pattern is empty
        coords_df = row[row.str.match(pattern)].str.extract(pattern)
        coords_df = coords_df.apply(pd.to_numeric)
        return pd.Series(zip(coords_df[0], coords_df[1])).reset_index(drop=True)
    except (IndexError, AssertionError, Exception):
        return pd.Series()


def extract_centers(series_obj, center_pattern):
    try:
        coords_df = series_obj[series_obj.str.match(center_pattern)].str.extract(center_pattern)
        coords_df = coords_df.apply(pd.to_numeric)
        centers_x = (coords_df[0] + coords_df[2]) / 2
        centers_y = (coords_df[1] + coords_df[3]) / 2
        return pd.Series(zip(centers_x, centers_y)).reset_index(drop=True)
    except (IndexError, AssertionError, Exception):
        return pd.Series()


def merge_and_store_result(result_data_frames, output_filename):
    # Merge all data frames
    final_df = pd.concat(result_data_frames)

    # save data frame to file
    final_df.to_csv(output_filename, index=None, header=True)
    print("Saved result to file: {}".format(output_filename))


def fix_csv():
    with open(CSV_FILE_NAME, 'r') as file:
        lines = list(csv.reader(file))

    # Get max len
    max_len = 0
    for line in lines:
        max_len = max(len(line), max_len)

    # Append extra cols
    for line in lines:
        line_len = len(line)
        extra_cols = [""] * (max_len - line_len)
        line += extra_cols

    # Write rows
    with open(CSV_FILE_NAME, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(lines)


def main(distance_threshold=30):
    fix_csv()
    df = pd.read_csv(CSV_FILE_NAME, header=None, error_bad_lines=False)
    column_names = ["frame_id", "face_id", "from_face_coordinates", "genders", "emotions", "emotion_coordinates",
                    "si_coordinates", "not_learning_coordinates", "learning_coordinates", "rh_coordinates",
                    "left_turn_coordinates", "right_turn_coordinates", "st_coordinates", "end_speaking_coordinates",
                    "from_sleeping_coordinates", ]

    pattern = r"^\(\d+ \d+\) \(\d+ \d+\)$"

    data_frames_step1 = []
    data_frames_step2 = []
    for i, row in df.iterrows():
        # Drop the NA Values
        row.dropna(inplace=True)

        # Get the frame id
        frame_id = ''
        frame_query = row[row.str.match(r'\d+\_FRAM')]
        if not frame_query.empty:
            frame_id = frame_query[0]

        # Get the emotion data
        emotion_data_index = (list(row[row == "Male"].index) +
                              list(row[row == "Female"].index))
        if emotion_data_index:
            # process emotion data
            min_emotion_index = min(emotion_data_index)
            max_emotion_index = max(emotion_data_index) + 3
            index_range = pd.Series(range(min_emotion_index, max_emotion_index, 3))
            genders = row.loc[index_range].reset_index(drop=True)
            index_range += 1
            emotions = row[index_range].reset_index(drop=True)
            index_range += 1
            emotion_coordinates = row[index_range].reset_index(drop=True)
        else:
            genders = pd.Series()
            emotions = pd.Series()
            emotion_coordinates = pd.Series()

        # Get the Si Values
        si_coordinates = get_values(row, row.str.find("Si ") != -1)

        # Get the Not Learning Values
        not_learning_coordinates = get_values(row, row.str.match("^Not Learning"))

        # Get the Learning Values
        learning_coordinates = get_values(row, row.str.match("^Learning"))

        # Get end speaking values
        end_speaking_coordinates = get_values(row, row.str.match(pattern))

        # Get the face_id Values
        face_id = get_values(row, row.str.find("face_id") != -1)

        # Get from face_coordinates
        from_face_coordinates = get_values(row, row.str.find("from face_coordiantes") != -1)

        # Get from from sleeping coordinates
        from_sleeping_coordinates = get_values(row, row.str.find("from sleeping") != -1)

        # Get from from Rh coordinates
        rh_coordinates = get_values(row, row.str.find("Rh ") != -1)

        # Get the Left turn coordinates
        left_turn_coordinates = get_values(row, row[row == "Left turn"].index + 1)

        # Get the Right turn coordinates
        right_turn_coordinates = get_values(row, row[row == "Right turn"].index + 1)

        # Get the ST coordinates
        st_coordinates = get_values(row, row.str.find("st coordinates") != -1)

        all_columns_step1 = [face_id, from_face_coordinates, genders, emotions, emotion_coordinates,
                             si_coordinates, not_learning_coordinates, learning_coordinates,
                             rh_coordinates, left_turn_coordinates, right_turn_coordinates,
                             st_coordinates, end_speaking_coordinates, from_sleeping_coordinates]
        column_sizes = map(lambda x: x.size, all_columns_step1)
        max_rows = max(column_sizes)

        # Adding the frame id
        frame_id_series = pd.Series([frame_id] * max_rows)
        all_columns_step1.insert(0, frame_id_series)

        # Merge all columns
        row_df_step1 = pd.concat(all_columns_step1, axis=1)

        # Add to all row data frames
        row_df_step1.columns = column_names
        data_frames_step1.append(row_df_step1)

        # modifications for step 2
        face_id_pattern = r'(.+) face_id'
        face_id2 = extract_single_values(face_id, face_id_pattern)

        from_face_coordinates_patten = r'(\d+) (\d+) from face_coordiantes'
        from_face_coordinates2 = extract_two_values(from_face_coordinates,
                                                    from_face_coordinates_patten)
        emotion_coordinates_pattern = r'\((\d+) (\d+)\)'
        emotion_coordinates2 = extract_two_values(emotion_coordinates,
                                                  emotion_coordinates_pattern)

        si_coordinates_pattern = r'Si \((\d+) (\d+)\)'
        si_coordinates2 = extract_two_values(si_coordinates, si_coordinates_pattern)

        not_learning_coordinates_pattern = r'Not Learning \((\d+) (\d+)\)'
        not_learning_coordinates2 = extract_two_values(not_learning_coordinates,
                                                       not_learning_coordinates_pattern)

        learning_coordinates_pattern = r'Learning \((\d+) (\d+)\)'
        learning_coordinates2 = extract_two_values(learning_coordinates,
                                                   learning_coordinates_pattern)

        rh_coordinates_pattern = r'Rh \((\d+) (\d+)\)'
        rh_coordinates2 = extract_two_values(rh_coordinates,
                                             rh_coordinates_pattern)

        left_turn_coordinates_pattern = emotion_coordinates_pattern
        left_turn_coordinates2 = extract_two_values(left_turn_coordinates,
                                                    left_turn_coordinates_pattern)

        right_turn_coordinates_pattern = emotion_coordinates_pattern
        right_turn_coordinates2 = extract_two_values(right_turn_coordinates,
                                                     right_turn_coordinates_pattern)

        st_coordinates_pattern = r''  # No pattern known # TODO: update the pattern here
        st_coordinates2 = extract_two_values(st_coordinates, st_coordinates_pattern)

        end_speaking_center_pattern = r"^\((\d+) (\d+)\) \((\d+) (\d+)\)$"
        centers_end_speaking = extract_centers(end_speaking_coordinates,
                                               end_speaking_center_pattern)

        from_sleeping_center_pattern = r'\((\d+) (\d+)\) \((\d+) (\d+)\) from sleeping'
        centers_from_sleeping = extract_centers(from_sleeping_coordinates,
                                                from_sleeping_center_pattern)

        all_columns_step2 = [frame_id_series, face_id2, from_face_coordinates2, genders, emotions, emotion_coordinates2,
                             si_coordinates2, not_learning_coordinates2, learning_coordinates2, rh_coordinates2,
                             left_turn_coordinates2, right_turn_coordinates2, st_coordinates2, centers_end_speaking,
                             centers_from_sleeping]

        emotion_coordinates3, emotion_coordinates_other, positions = arrange_coordinates(
            from_face_coordinates2, emotion_coordinates2, distance_threshold
        )
        genders_rearranged = pd.Series([None] * emotion_coordinates3.size)
        emotions_rearranged = pd.Series([None] * emotion_coordinates3.size)
        for key, val in positions.items():
            genders_rearranged[val] = genders[key]
            emotions_rearranged[val] = emotions[key]

        final_coordinates = [frame_id_series, face_id2, from_face_coordinates2,
                             genders_rearranged, emotions_rearranged, emotion_coordinates3]
        other_coordinates = [pd.Series(), pd.Series(), pd.Series(),
                             emotion_coordinates_other, ]

        for coordinates_var in all_columns_step2[6:]:
            coordinates_var_rearranged, coordinates_var_other, _ = arrange_coordinates(
                from_face_coordinates2, coordinates_var, distance_threshold
            )
            final_coordinates.append(coordinates_var_rearranged)
            other_coordinates.append(coordinates_var_other)

        other_col_column_sizes = map(lambda x: x.size, other_coordinates)
        other_col_max_rows = max(other_col_column_sizes)

        # Adding the frame id
        other_frame_id_series = pd.Series([frame_id] * other_col_max_rows)
        other_face_id_series = pd.Series(["Uncategorized"] * other_col_max_rows)

        other_coordinates = [other_frame_id_series, other_face_id_series] + other_coordinates

        # Merge all columns
        final_coordinates_df = pd.concat(final_coordinates, axis=1)
        other_coordinates_df = pd.concat(other_coordinates, axis=1)
        final_coordinates_df.columns = column_names
        other_coordinates_df.columns = column_names

        # Merge final_coordinates and other coordinates
        row_df_step2 = pd.concat([final_coordinates_df, other_coordinates_df])

        # Add to all row data frames
        row_df_step2.columns = column_names
        data_frames_step2.append(row_df_step2)
        print("Completed..{}".format(i), end='\r')

    # Stores the steps results
    merge_and_store_result(data_frames_step1, 'output_step1.csv')
    merge_and_store_result(data_frames_step2, 'output_step2.csv')


if __name__ == '__main__':
    main()
