import pandas as pd
import numpy as np
from collections import OrderedDict
import json
import os

def convert_all_data_to_json(
    poses_3d_with_person_info_df,
    person_positions,
    tray_positions,
    tray_events=None,
    indent=2,
    output_path=None
):
    # Prepare identified 3D pose track data
    poses_3d_with_person_info_df = poses_3d_with_person_info_df.copy()
    poses_3d_with_person_info_df.index.name = 'pose_3d_id'
    poses_3d_with_person_info_df.reset_index(inplace=True)
    poses_3d_with_person_info_df['keypoint_coordinates_3d'] = poses_3d_with_person_info_df['keypoint_coordinates_3d'].apply(lambda x: x.tolist())
    poses_3d_with_person_info_df = poses_3d_with_person_info_df.reindex(columns=[
        'timestamp',
        'pose_3d_id',
        'keypoint_coordinates_3d',
        'pose_track_3d_id',
        'person_id',
        'name',
        'short_name',
        'anonymized_name',
        'anonymized_short_name'
    ])
    # Prepare person position data
    person_positions = person_positions.copy()
    person_positions['sensor_coordinates'] = person_positions['sensor_coordinates'].apply(lambda x: x.tolist())
    person_positions = person_positions.astype('object')
    person_positions = person_positions.where(pd.notnull(person_positions), None)
    # Prepare tray position data
    tray_positions = tray_positions.copy()
    if tray_events is not None:
        tray_positions = add_event_data_to_tray_positions(
            tray_positions=tray_positions,
            tray_events=tray_events
        )
    tray_positions['sensor_coordinates'] = tray_positions['sensor_coordinates'].apply(lambda x: x.tolist())
    tray_positions = tray_positions.astype('object')
    tray_positions = tray_positions.where(pd.notnull(tray_positions), None)
    # Extract timestamps across datasets
    timestamps = sorted(list(
        set(poses_3d_with_person_info_df['timestamp']) |
        set(person_positions['timestamp']) |
        set(tray_positions['timestamp'])
    ))
    # Create consolidated data
    data_dict = OrderedDict()
    for timestamp in timestamps:
        data_dict[timestamp.isoformat()] = {
            'poses': (
                poses_3d_with_person_info_df
                .loc[poses_3d_with_person_info_df['timestamp']==timestamp]
                .drop(columns='timestamp')
                .to_dict(orient='records')
            ),
            'positions': (
                person_positions
                .loc[person_positions['timestamp']==timestamp]
                .drop(columns='timestamp')
                .to_dict(orient='records')
            ),
            'trays': (
                tray_positions
                .loc[tray_positions['timestamp']==timestamp]
                .drop(columns='timestamp')
                .to_dict(orient='records')
            )
        }
    all_data_json = json.dumps(data_dict, indent=indent)
    if output_path is not None:
        output_directory = os.path.dirname(output_path)
        os.makedirs(output_directory, exist_ok=True)
        with open(output_path, 'w') as fp:
            fp.write(all_data_json)
    return all_data_json

def convert_3d_poses_with_person_info_to_json(
    poses_3d_with_person_info_df,
    output_path=None
):
    poses_3d_with_person_info_df = poses_3d_with_person_info_df.copy()
    poses_3d_with_person_info_df.index.name = 'pose_3d_id'
    poses_3d_with_person_info_df.reset_index(inplace=True)
    poses_3d_with_person_info_df.sort_values('timestamp', inplace=True)
    poses_3d_with_person_info_df['timestamp'] = poses_3d_with_person_info_df['timestamp'].apply(lambda x: x.isoformat())
    poses_3d_with_person_info_df['keypoint_coordinates_3d'] = poses_3d_with_person_info_df['keypoint_coordinates_3d'].apply(lambda x: x.tolist())
    poses_3d_with_person_info_df = poses_3d_with_person_info_df.reindex(columns=[
        'timestamp',
        'pose_3d_id',
        'keypoint_coordinates_3d',
        'pose_track_3d_id',
        'person_id',
        'name',
        'short_name'
    ])
    data_dict = OrderedDict()
    for timestamp, timestamp_df in poses_3d_with_person_info_df.groupby('timestamp'):
        data_dict[timestamp] = timestamp_df.to_dict(orient='records')
    poses_3d_with_person_info_json = json.dumps(data_dict, indent=2)
    if output_path is not None:
        output_directory = os.path.dirname(output_path)
        os.makedirs(output_directory, exist_ok=True)
        with open(output_path, 'w') as fp:
            fp.write(poses_3d_with_person_info_json)
    return poses_3d_with_person_info_json

def convert_person_positions_to_json(
    person_positions,
    output_path=None
):
    person_positions = person_positions.copy()
    person_positions.sort_values('timestamp', inplace=True)
    person_positions['timestamp'] = person_positions['timestamp'].apply(lambda x: x.isoformat())
    person_positions['sensor_coordinates'] = person_positions['sensor_coordinates'].apply(lambda x: x.tolist())
    person_positions = person_positions.astype('object')
    person_positions = person_positions.where(pd.notnull(person_positions), None)
    data_dict = OrderedDict()
    for timestamp, timestamp_df in person_positions.groupby('timestamp'):
        data_dict[timestamp] = timestamp_df.to_dict(orient='records')
    person_positions_json = json.dumps(data_dict, indent=2)
    if output_path is not None:
        output_directory = os.path.dirname(output_path)
        os.makedirs(output_directory, exist_ok=True)
        with open(output_path, 'w') as fp:
            fp.write(person_positions_json)
    return person_positions_json

def convert_tray_positions_to_json(
    tray_positions,
    output_path=None
):
    tray_positions = tray_positions.copy()
    tray_positions.sort_values('timestamp', inplace=True)
    tray_positions['timestamp'] = tray_positions['timestamp'].apply(lambda x: x.isoformat())
    tray_positions['sensor_coordinates'] = tray_positions['sensor_coordinates'].apply(lambda x: x.tolist())
    tray_positions = tray_positions.astype('object')
    tray_positions = tray_positions.where(pd.notnull(tray_positions), None)
    data_dict = OrderedDict()
    for timestamp, timestamp_df in tray_positions.groupby('timestamp'):
        data_dict[timestamp] = timestamp_df.to_dict(orient='records')
    tray_positions_json = json.dumps(data_dict, indent=2)
    if output_path is not None:
        output_directory = os.path.dirname(output_path)
        os.makedirs(output_directory, exist_ok=True)
        with open(output_path, 'w') as fp:
            fp.write(tray_positions_json)
    return tray_positions_json

def add_event_data_to_tray_positions(
    tray_positions,
    tray_events
):
    tray_positions_with_event_data = tray_positions.copy()
    tray_positions_with_event_data['tray_event'] = False
    tray_positions_with_event_data['tray_event_type'] = None
    for idx, event in tray_events.iterrows():
        tray_positions_with_event_data.loc[
            (
                (tray_positions_with_event_data['timestamp'] >= event['start']) &
                (tray_positions_with_event_data['timestamp'] <= event['end']) &
                (tray_positions_with_event_data['tray_id'] == event['tray_id'])
            ),
            'tray_event'
        ] = True
        tray_positions_with_event_data.loc[
            (
                (tray_positions_with_event_data['timestamp'] >= event['start']) &
                (tray_positions_with_event_data['timestamp'] <= event['end']) &
                (tray_positions_with_event_data['tray_id'] == event['tray_id'])
            ),
            'tray_event_type'
        ] = event['interaction_type']
    return tray_positions_with_event_data
