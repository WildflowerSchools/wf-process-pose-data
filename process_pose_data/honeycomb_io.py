import minimal_honeycomb
import pandas as pd
import numpy as np
import tqdm
import datetime
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

def fetch_2d_pose_data(
    start=None,
    end=None,
    environment_id=None,
    environment_name=None,
    camera_ids=None,
    camera_device_types=None,
    camera_part_numbers=None,
    camera_names=None,
    camera_serial_numbers=None,
    pose_model_id=None,
    pose_model_name=None,
    pose_model_variant_name=None,
    inference_ids=None,
    inference_names=None,
    inference_models=None,
    inference_versions=None,
    return_track_label=False,
    return_person_id=False,
    return_inference_id=False,
    return_pose_model_id=True,
    return_pose_quality=False,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    camera_ids_from_environment = fetch_camera_ids_from_environment(
        start=start,
        end=end,
        environment_id=environment_id,
        environment_name=environment_name,
        camera_device_types=camera_device_types,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    camera_ids_from_camera_properties = fetch_camera_ids_from_camera_properties(
        camera_ids=camera_ids,
        camera_device_types=camera_device_types,
        camera_part_numbers=camera_part_numbers,
        camera_names=camera_names,
        camera_serial_numbers=camera_serial_numbers,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    pose_model_id = fetch_pose_model_id(
        pose_model_id=pose_model_id,
        pose_model_name=pose_model_name,
        pose_model_variant_name=pose_model_variant_name,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    inference_ids = fetch_inference_ids(
        inference_ids=inference_ids,
        inference_names=inference_names,
        inference_models=inference_models,
        inference_versions=inference_versions,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Building query list for 2D pose search')
    query_list = list()
    if start is not None:
        query_list.append({
            'field': 'timestamp',
            'operator': 'GTE',
            'value': minimal_honeycomb.to_honeycomb_datetime(start)
        })
    if end is not None:
        query_list.append({
            'field': 'timestamp',
            'operator': 'LTE',
            'value': minimal_honeycomb.to_honeycomb_datetime(end)
        })
    if camera_ids_from_environment is not None:
        query_list.append({
            'field': 'camera',
            'operator': 'IN',
            'values': camera_ids_from_environment
        })
    if camera_ids_from_camera_properties is not None:
        query_list.append({
            'field': 'camera',
            'operator': 'IN',
            'values': camera_ids_from_camera_properties
        })
    if pose_model_id is not None:
        query_list.append({
            'field': 'pose_model',
            'operator': 'EQ',
            'value': pose_model_id
        })
    if inference_ids is not None:
        query_list.append({
            'field': 'source',
            'operator': 'IN',
            'values': inference_ids
        })
    return_data= [
        'pose_id',
        'timestamp',
        {'camera': [
            'device_id'
        ]},
        'track_label',
        {'pose_model': [
            'pose_model_id'
        ]},
        {'keypoints': [
            'coordinates',
            'quality'
        ]},
        'quality',
        {'person': [
            'person_id'
        ]},
        {'source': [
            {'... on InferenceExecution': [
                'inference_id'
            ]}
        ]}
    ]
    result = search_2d_poses(
        query_list=query_list,
        return_data=return_data,
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    data = list()
    logger.info('Parsing {} returned poses'.format(len(result)))
    for datum in result:
        data.append({
            'pose_id_2d': datum.get('pose_id'),
            'timestamp': datum.get('timestamp'),
            'camera_id': (datum.get('camera') if datum.get('camera') is not None else {}).get('device_id'),
            'track_label_2d': datum.get('track_label'),
            'person_id': (datum.get('person') if datum.get('person') is not None else {}).get('person_id'),
            'inference_id': (datum.get('source') if datum.get('source') is not None else {}).get('inference_id'),
            'pose_model_id': (datum.get('pose_model') if datum.get('pose_model') is not None else {}).get('pose_model_id'),
            'keypoint_coordinates_2d': np.asarray([keypoint.get('coordinates') for keypoint in datum.get('keypoints')], dtype=np.float),
            'keypoint_quality_2d': np.asarray([keypoint.get('quality') for keypoint in datum.get('keypoints')], dtype=np.float),
            'pose_quality_2d': datum.get('quality')
        })
    poses_2d_df = pd.DataFrame(data)
    poses_2d_df['keypoint_coordinates_2d'] = poses_2d_df['keypoint_coordinates_2d'].apply(lambda x: np.where(x == 0.0, np.nan, x))
    poses_2d_df['timestamp'] = pd.to_datetime(poses_2d_df['timestamp'])
    if poses_2d_df['pose_model_id'].nunique() > 1:
        raise ValueError('Returned poses are associated with multiple pose models')
    if (poses_2d_df.groupby(['timestamp', 'camera_id'])['inference_id'].nunique() > 1).any():
        raise ValueError('Returned poses have multiple inference IDs for some camera IDs at some timestamps')
    poses_2d_df.set_index('pose_id_2d', inplace=True)
    return_columns = [
        'timestamp',
        'camera_id'
    ]
    if return_track_label:
        return_columns.append('track_label_2d')
    if return_person_id:
        return_columns.append('person_id')
    if return_inference_id:
        return_columns.append('inference_id')
    if return_pose_model_id:
        return_columns.append('pose_model_id')
    return_columns.extend([
        'keypoint_coordinates_2d',
        'keypoint_quality_2d'
    ])
    if return_pose_quality:
        return_columns.append('pose_quality_2d')
    poses_2d_df = poses_2d_df.reindex(columns=return_columns)
    return poses_2d_df

def search_2d_poses(
    query_list,
    return_data,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    logger.info('Searching for 2D poses that match the specified parameters')
    result = search_objects(
        request_name='searchPoses2D',
        query_list=query_list,
        return_data=return_data,
        id_field_name='pose_id',
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
    )
    logger.info('Fetched {} poses'.format(len(result)))
    return result

def fetch_3d_pose_data(
    start=None,
    end=None,
    pose_model_id=None,
    pose_model_name=None,
    pose_model_variant_name=None,
    inference_ids=None,
    inference_names=None,
    inference_models=None,
    inference_versions=None,
    return_keypoint_quality=False,
    return_coordinate_space_id=False,
    return_track_label=False,
    return_poses_2d=True,
    return_person_id=False,
    return_inference_id=False,
    return_pose_model_id=False,
    return_pose_quality=False,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    pose_model_id = fetch_pose_model_id(
        pose_model_id=pose_model_id,
        pose_model_name=pose_model_name,
        pose_model_variant_name=pose_model_variant_name,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    inference_ids = fetch_inference_ids(
        inference_ids=inference_ids,
        inference_names=inference_names,
        inference_models=inference_models,
        inference_versions=inference_versions,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Building query list for 3D pose search')
    query_list = list()
    if start is not None:
        query_list.append({
            'field': 'timestamp',
            'operator': 'GTE',
            'value': minimal_honeycomb.to_honeycomb_datetime(start)
        })
    if end is not None:
        query_list.append({
            'field': 'timestamp',
            'operator': 'LTE',
            'value': minimal_honeycomb.to_honeycomb_datetime(end)
        })
    if pose_model_id is not None:
        query_list.append({
            'field': 'pose_model',
            'operator': 'EQ',
            'value': pose_model_id
        })
    if inference_ids is not None:
        query_list.append({
            'field': 'source',
            'operator': 'IN',
            'values': inference_ids
        })
    return_data= [
        'pose_id',
        'timestamp',
        'track_label',
        {'pose_model': [
            'pose_model_id'
        ]},
        {'keypoints': [
            'coordinates',
            'quality'
        ]},
        {'coordinate_space': [
            'space_id'
        ]},
        'quality',
        'poses_2d',
        {'person': [
            'person_id'
        ]},
        {'source': [
            {'... on InferenceExecution': [
                'inference_id'
            ]}
        ]}
    ]
    result = search_3d_poses(
        query_list=query_list,
        return_data=return_data,
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    data = list()
    logger.info('Parsing {} returned poses'.format(len(result)))
    for datum in result:
        data.append({
            'pose_id_3d': datum.get('pose_id'),
            'timestamp': datum.get('timestamp'),
            'track_label_3d': datum.get('track_label'),
            'pose_ids_2d': datum.get('poses_2d'),
            'person_id': (datum.get('person') if datum.get('person') is not None else {}).get('person_id'),
            'inference_id': (datum.get('source') if datum.get('source') is not None else {}).get('inference_id'),
            'pose_model_id': (datum.get('pose_model') if datum.get('pose_model') is not None else {}).get('pose_model_id'),
            'keypoint_coordinates_3d': np.asarray([keypoint.get('coordinates') for keypoint in datum.get('keypoints')], dtype=np.float),
            'keypoint_quality_3d': np.asarray([keypoint.get('quality') for keypoint in datum.get('keypoints')], dtype=np.float),
            'coordinate_space_id': datum.get('coordinate_space').get('space_id'),
            'pose_quality_3d': datum.get('quality')
        })
    poses_3d_df = pd.DataFrame(data)
    poses_3d_df['timestamp'] = pd.to_datetime(poses_3d_df['timestamp'])
    if poses_3d_df['pose_model_id'].nunique() > 1:
        raise ValueError('Returned poses are associated with multiple pose models')
    if (poses_3d_df.groupby('timestamp')['inference_id'].nunique() > 1).any():
        raise ValueError('Returned poses have multiple inference IDs for timestamps')
    poses_3d_df.set_index('pose_id_3d', inplace=True)
    return_columns = [
        'timestamp'
    ]
    if return_track_label:
        return_columns.append('track_label_3d')
    if return_poses_2d:
        return_columns.append('pose_ids_2d')
    if return_person_id:
        return_columns.append('person_id')
    if return_inference_id:
        return_columns.append('inference_id')
    if return_pose_model_id:
        return_columns.append('pose_model_id')
    return_columns.append('keypoint_coordinates_3d')
    if return_keypoint_quality:
        return_columns.append('keypoint_quality_3d')
    if return_pose_quality:
        return_columns.append('pose_quality_3d')
    if return_coordinate_space_id:
        return_columns.append('coordinate_space_id')
    poses_3d_df = poses_3d_df.reindex(columns=return_columns)
    return poses_3d_df

def search_3d_poses(
    query_list,
    return_data,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    logger.info('Searching for 3D poses that match the specified parameters')
    result = search_objects(
        request_name='searchPoses3D',
        query_list=query_list,
        return_data=return_data,
        id_field_name='pose_id',
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
    )
    logger.info('Fetched {} poses'.format(len(result)))
    return result

def search_objects(
    request_name,
    query_list,
    return_data,
    id_field_name,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    result = client.bulk_query(
        request_name=request_name,
        arguments={
            'query': {
                'type': 'QueryExpression!',
                'value': {
                    'operator': 'AND',
                    'children': query_list
                }
            }
        },
        return_data=return_data,
        id_field_name=id_field_name,
        chunk_size=chunk_size
    )
    return result

def fetch_3d_pose_track_data(
    inference_ids=None,
    inference_names=None,
    inference_models=None,
    inference_versions=None,
    return_track_label=False,
    return_inference_id=False,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    inference_ids = fetch_inference_ids(
        inference_ids=inference_ids,
        inference_names=inference_names,
        inference_models=inference_models,
        inference_versions=inference_versions,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Building query list for 3D pose track search')
    query_list = list()
    if inference_ids is not None:
        query_list.append({
            'field': 'source',
            'operator': 'IN',
            'values': inference_ids
        })
    return_data = [
        'pose_track_id',
        'poses_3d',
        'track_label',
        {'source': [
            {'... on InferenceExecution': [
                'inference_id'
            ]}
        ]}
    ]
    result = search_3d_pose_tracks(
        query_list=query_list,
        return_data=return_data,
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    data = list()
    logger.info('Parsing {} returned pose tracks'.format(len(result)))
    for datum in result:
        data.append({
            'pose_track_3d_id': datum.get('pose_track_id'),
            'pose_id_3ds': datum.get('poses_3d'),
            'track_label_3d': datum.get('track_label'),
            'inference_id': (datum.get('source') if datum.get('source') is not None else {}).get('inference_id')
        })
    pose_tracks_3d_df = pd.DataFrame(data)
    pose_tracks_3d_df.set_index('pose_track_3d_id', inplace=True)
    return_columns = [
        'pose_id_3ds'
    ]
    if return_track_label:
        return_columns.append('track_label_3d')
    if return_inference_id:
        return_columns.append('inference_id')
    pose_tracks_3d_df = pose_tracks_3d_df.reindex(columns=return_columns)
    return pose_tracks_3d_df

def search_3d_pose_tracks(
    query_list,
    return_data,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    logger.info('Searching for 3D pose tracks that match the specified parameters')
    result = search_objects(
        request_name='searchPoseTracks3D',
        query_list=query_list,
        return_data=return_data,
        id_field_name='pose_track_id',
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
    )
    logger.info('Fetched {} pose tracks'.format(len(result)))
    return result

def fetch_camera_ids_from_environment(
    start=None,
    end=None,
    environment_id=None,
    environment_name=None,
    camera_device_types=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if camera_device_types is None:
        camera_device_types = [
            'PI3WITHCAMERA',
            'PIZEROWITHCAMERA'
        ]
    environment_id = fetch_environment_id(
        environment_id=environment_id,
        environment_name=environment_name,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    if environment_id is None:
        return None
    logger.info('Fetching camera assignments for specified environment and time span')
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    result = client.request(
        request_type='query',
        request_name='getEnvironment',
        arguments={
            'environment_id': {
                'type': 'ID!',
                'value': environment_id
            }
        },
        return_object=[
            {'assignments': [
                'start',
                'end',
                {'assigned': [
                    {'... on Device': [
                        'device_id',
                        'device_type'
                    ]}
                ]}
            ]}
        ]
    )
    filtered_assignments = minimal_honeycomb.filter_assignments(
        assignments=result.get('assignments'),
        start_time=start,
        end_time=end
    )
    camera_device_ids = list()
    for assignment in filtered_assignments:
        device_type = assignment.get('assigned').get('device_type')
        if device_type is not None and device_type in camera_device_types:
            camera_device_ids.append(assignment.get('assigned').get('device_id'))
    if len(camera_device_ids) == 0:
        raise ValueError('No camera devices found in specified environment for specified time span')
    logger.info('Found {} camera assignments for specified environment and time span'.format(len(camera_device_ids)))
    return camera_device_ids

def fetch_environment_id(
    environment_id=None,
    environment_name=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if environment_id is not None:
        if environment_name is not None:
            raise ValueError('If environment ID is specified, environment name cannot be specified')
        return environment_id
    if environment_name is not None:
        logger.info('Fetching environment ID for specified environment name')
        client = minimal_honeycomb.MinimalHoneycombClient(
            uri=uri,
            token_uri=token_uri,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret
        )
        result = client.bulk_query(
            request_name='findEnvironments',
            arguments={
                'name': {
                    'type': 'String',
                    'value': environment_name
                }
            },
            return_data=[
                'environment_id'
            ],
            id_field_name='environment_id'
        )
        if len(result) == 0:
            raise ValueError('No environments match environment name {}'.format(
                environment_name
            ))
        if len(result) > 1:
            raise ValueError('Multiple environments match environment name {}'.format(
                environment_name
            ))
        environment_id = result[0].get('environment_id')
        logger.info('Found environment ID for specified environment name')
        return environment_id
    return None

def fetch_camera_ids_from_camera_properties(
    camera_ids=None,
    camera_device_types=None,
    camera_part_numbers=None,
    camera_names=None,
    camera_serial_numbers=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if camera_ids is not None:
        if camera_names is not None or camera_part_numbers is not None or camera_serial_numbers is not None:
            raise ValueError('If camera IDs are specified, camera names/part numbers/serial numbers cannot be specified')
        return camera_ids
    if camera_names is not None or camera_part_numbers is not None or camera_serial_numbers is not None:
        query_list=list()
        if camera_device_types is not None:
            query_list.append({
                'field': 'device_type',
                'operator': 'IN',
                'values': camera_device_types
            })
        if camera_part_numbers is not None:
            query_list.append({
                'field': 'part_number',
                'operator': 'IN',
                'values': camera_part_numbers
            })
        if camera_names is not None:
            query_list.append({
                'field': 'name',
                'operator': 'IN',
                'values': camera_names
            })
        if camera_serial_numbers is not None:
            query_list.append({
                'field': 'serial_number',
                'operator': 'IN',
                'values': camera_serial_numbers
            })
        logger.info('Fetching camera IDs for cameras with specified properties')
        client = minimal_honeycomb.MinimalHoneycombClient(
            uri=uri,
            token_uri=token_uri,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret
        )
        result = client.bulk_query(
            request_name='searchDevices',
            arguments={
                'query': {
                    'type': 'QueryExpression!',
                    'value': {
                        'operator': 'AND',
                        'children': query_list
                    }
                }
            },
            return_data=[
                'device_id'
            ],
            id_field_name='device_id'
        )
        if len(result) == 0:
            raise ValueError('No devices match specified device types/part numbers/names/serial numbers')
        camera_ids = [datum.get('device_id') for datum in result]
        logger.info('Found {} camera IDs that match specified properties'.format(len(camera_ids)))
        return camera_ids
    return None

def fetch_pose_model_id(
    pose_model_id=None,
    pose_model_name=None,
    pose_model_variant_name=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if pose_model_id is not None:
        if pose_model_name is not None or pose_model_variant_name is not None:
            raise ValueError('If pose model ID is specified, pose model name/variant name cannot be specified')
        return pose_model_id
    if pose_model_name is not None or pose_model_variant_name is not None:
        arguments=dict()
        if pose_model_name is not None:
            arguments['model_name'] = {
                'type': 'String',
                'value': pose_model_name
            }
        if pose_model_variant_name is not None:
            arguments['model_variant_name'] = {
                'type': 'String',
                'value': pose_model_variant_name
            }
        logger.info('Fetching pose model ID for pose model with specified properties')
        client = minimal_honeycomb.MinimalHoneycombClient(
            uri=uri,
            token_uri=token_uri,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret
        )
        result = client.bulk_query(
            request_name='findPoseModels',
            arguments=arguments,
            return_data=[
                'pose_model_id'
            ],
            id_field_name='pose_model_id'
        )
        if len(result) == 0:
            raise ValueError('No pose models match specified model name/model variant name')
        if len(result) > 1:
            raise ValueError('Multiple pose models match specified model name/model variant name')
        pose_model_id = result[0].get('pose_model_id')
        logger.info('Found pose model ID for pose model with specified properties')
        return pose_model_id
    return None

def fetch_pose_model(
    pose_id_2d,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    logger.info('Fetching pose model information for specified pose')
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    result = client.request(
        request_type='query',
        request_name='getPose2D',
        arguments={
            'pose_id': {
                'type': 'ID!',
                'value': pose_id_2d
            }
        },
        return_object=[
            {'pose_model': [
                'pose_model_id',
                'model_name',
                'model_variant_name',
                'keypoint_names',
                'keypoint_descriptions',
                'keypoint_connectors'
            ]}
        ])
    pose_model = result.get('pose_model')
    return pose_model

def fetch_pose_model_by_pose_model_id(
    pose_model_id,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    logger.info('Fetching pose model information for specified pose model ID')
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    result = client.request(
        request_type='query',
        request_name='getPoseModel',
        arguments={
            'pose_model_id': {
                'type': 'ID!',
                'value': pose_model_id
            }
        },
        return_object=[
            'pose_model_id',
            'model_name',
            'model_variant_name',
            'keypoint_names',
            'keypoint_descriptions',
            'keypoint_connectors'
        ])
    pose_model = result
    return pose_model

def fetch_inference_ids(
    inference_ids=None,
    inference_names=None,
    inference_models=None,
    inference_versions=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if inference_ids is not None:
        if inference_names is not None or inference_models is not None or inference_versions is not None:
            raise ValueError('If inference IDs are specified, inference names/models/versions cannot be specified')
        return inference_ids
    if inference_names is not None or inference_models is not None or inference_versions is not None:
        query_list=list()
        if inference_names is not None:
            query_list.append({
                'field': 'name',
                'operator': 'IN',
                'values': inference_names
            })
        if inference_models is not None:
            query_list.append({
                'field': 'model',
                'operator': 'IN',
                'values': inference_models
            })
        if inference_versions is not None:
            query_list.append({
                'field': 'version',
                'operator': 'IN',
                'values': inference_versions
            })
        logger.info('Fetching inference IDs for inference runs with specified properties')
        client = minimal_honeycomb.MinimalHoneycombClient(
            uri=uri,
            token_uri=token_uri,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret
        )
        result = client.bulk_query(
            request_name='searchInferenceExecutions',
            arguments={
                'query': {
                    'type': 'QueryExpression!',
                    'value': {
                        'operator': 'AND',
                        'children': query_list
                    }
                }
            },
            return_data=[
                'inference_id'
            ],
            id_field_name='inference_id'
        )
        if len(result) == 0:
            raise ValueError('No inference executions match specified inference names/models/versions')
        inference_ids = [datum.get('inference_id') for datum in result]
        logger.info('Found {} inference runs that match specified properties'.format(len(inference_ids)))
        return inference_ids
    return None

def fetch_camera_names(
    camera_ids,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Fetching camera names for specified camera device IDs')
    result = client.bulk_query(
        request_name='searchDevices',
        arguments={
            'query': {
                'type': 'QueryExpression!',
                'value': {
                    'field': 'device_id',
                    'operator': 'IN',
                    'values': camera_ids
                }
            }
        },
        return_data=[
            'device_id',
            'name'
        ],
        id_field_name = 'device_id',
        chunk_size=chunk_size
    )
    camera_names = {device.get('device_id'): device.get('name') for device in result}
    logger.info('Fetched {} camera names'.format(len(camera_names)))
    return camera_names

def fetch_camera_calibrations(
    camera_ids,
    start=None,
    end=None,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    intrinsic_calibrations = fetch_intrinsic_calibrations(
        camera_ids=camera_ids,
        start=start,
        end=end,
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    extrinsic_calibrations = fetch_extrinsic_calibrations(
        camera_ids=camera_ids,
        start=start,
        end=end,
        chunk_size=chunk_size,
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    camera_calibrations = dict()
    for camera_id in camera_ids:
        if camera_id not in intrinsic_calibrations.keys():
            logger.warning('No intrinsic calibration found for camera ID {}'.format(
                camera_id
            ))
            continue
        if camera_id not in extrinsic_calibrations.keys():
            logger.warning('No extrinsic calibration found for camera ID {}'.format(
                camera_id
            ))
            continue
        camera_calibrations[camera_id] = {**intrinsic_calibrations[camera_id], **extrinsic_calibrations[camera_id]}
    return camera_calibrations

def fetch_intrinsic_calibrations(
    camera_ids,
    start=None,
    end=None,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Fetching intrinsic calibrations for specified camera device IDs and time span')
    result = client.bulk_query(
        request_name='searchIntrinsicCalibrations',
        arguments={
            'query': {
                'type': 'QueryExpression!',
                'value': {
                    'field': 'device',
                    'operator': 'IN',
                    'values': camera_ids
                }
            }
        },
        return_data=[
            'intrinsic_calibration_id',
            'start',
            'end',
            {'device': [
                'device_id'
            ]},
            'camera_matrix',
            'distortion_coefficients',
            'image_width',
            'image_height'
        ],
        id_field_name = 'intrinsic_calibration_id',
        chunk_size=chunk_size
    )
    logger.info('Fetched {} intrinsic calibrations for specified camera IDs'.format(len(result)))
    filtered_result = minimal_honeycomb.filter_assignments(
        result,
        start,
        end
    )
    logger.info('{} intrinsic calibrations are consistent with specified start and end times'.format(len(filtered_result)))
    intrinsic_calibrations = dict()
    for datum in filtered_result:
        camera_id = datum.get('device').get('device_id')
        if camera_id in intrinsic_calibrations.keys():
            raise ValueError('More than one intrinsic calibration found for camera {}'.format(
                camera_id
            ))
        intrinsic_calibrations[camera_id] = {
            'camera_matrix': np.asarray(datum.get('camera_matrix')),
            'distortion_coefficients': np.asarray(datum.get('distortion_coefficients')),
            'image_width': datum.get('image_width'),
            'image_height': datum.get('image_height')
        }
    return intrinsic_calibrations

def fetch_extrinsic_calibrations(
    camera_ids,
    start=None,
    end=None,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Fetching extrinsic calibrations for specified camera device IDs and time span')
    result = client.bulk_query(
        request_name='searchExtrinsicCalibrations',
        arguments={
            'query': {
                'type': 'QueryExpression!',
                'value': {
                    'field': 'device',
                    'operator': 'IN',
                    'values': camera_ids
                }
            }
        },
        return_data=[
            'extrinsic_calibration_id',
            'start',
            'end',
            {'device': [
                'device_id'
            ]},
            {'coordinate_space': [
                'space_id'
            ]},
            'translation_vector',
            'rotation_vector'
        ],
        id_field_name = 'extrinsic_calibration_id',
        chunk_size=chunk_size
    )
    logger.info('Fetched {} extrinsic calibrations for specified camera IDs'.format(len(result)))
    filtered_result = minimal_honeycomb.filter_assignments(
        result,
        start,
        end
    )
    logger.info('{} extrinsic calibrations are consistent with specified start and end times'.format(len(filtered_result)))
    extrinsic_calibrations = dict()
    space_ids = list()
    for datum in filtered_result:
        camera_id = datum.get('device').get('device_id')
        space_id = datum.get('coordinate_space').get('space_id')
        space_ids.append(space_id)
        if camera_id in extrinsic_calibrations.keys():
            raise ValueError('More than one extrinsic calibration found for camera {}'.format(
                camera_id
            ))
        extrinsic_calibrations[camera_id] = {
            'space_id': space_id,
            'rotation_vector': np.asarray(datum.get('rotation_vector')),
            'translation_vector': np.asarray(datum.get('translation_vector'))
        }
    if len(np.unique(space_ids)) > 1:
        raise ValueError('More than one coordinate space found among fetched calibrations')
    return extrinsic_calibrations

def fetch_camera_device_id_lookup(
    assignment_ids,
    client=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if client is None:
        client = minimal_honeycomb.MinimalHoneycombClient(
            uri=uri,
            token_uri=token_uri,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret
        )
    result = client.bulk_query(
        request_name='searchAssignments',
        arguments={
            'query': {
                'type': 'QueryExpression!',
                'value': {
                    'field': 'assignment_id',
                    'operator': 'IN',
                    'values': assignment_ids
                }
        }},
        return_data=[
            'assignment_id',
            {'assigned': [
                {'... on Device': [
                    'device_id'
                ]}
            ]}
        ],
        id_field_name='assignment_id'
    )
    camera_device_id_lookup = dict()
    for datum in result:
        camera_device_id_lookup[datum.get('assignment_id')] = datum.get('assigned').get('device_id')
    return camera_device_id_lookup

def create_inference_execution(
    execution_start=None,
    name=None,
    notes=None,
    model=None,
    version=None,
    data_sources=None,
    data_results=None,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    if execution_start is None:
        execution_start = minimal_honeycomb.to_honeycomb_datetime(datetime.datetime.now(tz=datetime.timezone.utc))
    else:
        execution_start = minimal_honeycomb.to_honeycomb_datetime(execution_start)
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Creating inference execution')
    result = client.request(
        request_type='mutation',
        request_name='createInferenceExecution',
        arguments={
            'inferenceExecution': {
                'type': 'InferenceExecutionInput',
                'value': {
                    'execution_start': execution_start,
                    'name': name,
                    'notes': notes,
                    'model': model,
                    'version': version,
                    'data_sources': data_sources,
                    'data_results': data_results
                }
            }
        },
        return_object=[
            'inference_id'
        ]
    )
    try:
        inference_id = result['inference_id']
    except:
        raise ValueError('Received unexpected response from Honeycomb: {}'.format(result))
    return inference_id

def write_3d_pose_data(
    poses_3d_df,
    coordinate_space_id=None,
    pose_model_id=None,
    source_id=None,
    source_type=None,
    chunk_size=100,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None
):
    poses_3d_df_honeycomb = poses_3d_df.copy()
    if coordinate_space_id is None:
        if 'coordinate_space_id' not in poses_3d_df_honeycomb.columns:
            raise ValueError('Coordinate space ID must either be included in data frame or specified')
    else:
        poses_3d_df_honeycomb['coordinate_space_id'] = coordinate_space_id
    if pose_model_id is None:
        if 'pose_model_id' not in poses_3d_df_honeycomb.columns:
            raise ValueError('Pose model ID must either be included in data frame or specified')
    else:
        poses_3d_df_honeycomb['pose_model_id'] = pose_model_id
    if source_id is None:
        if 'source_id' not in poses_3d_df_honeycomb.columns:
            raise ValueError('Source ID must either be included in data frame or specified')
    else:
        poses_3d_df_honeycomb['source_id'] = source_id
    if source_type is None:
        if 'source_type' not in poses_3d_df_honeycomb.columns:
            raise ValueError('Source type must either be included in data frame or specified')
    else:
        poses_3d_df_honeycomb['source_type'] = source_type
    poses_3d_df_honeycomb['timestamp'] = poses_3d_df_honeycomb['timestamp'].apply(
        lambda x: minimal_honeycomb.to_honeycomb_datetime(x.to_pydatetime())
    )
    poses_3d_df_honeycomb['keypoint_coordinates_3d'] = poses_3d_df_honeycomb['keypoint_coordinates_3d'].apply(
        lambda x: np.where(np.isnan(x), None, x)
    )
    poses_3d_df_honeycomb['keypoint_coordinates_3d'] = poses_3d_df_honeycomb['keypoint_coordinates_3d'].apply(
        lambda x: [{'coordinates': x[i, :].tolist()} for i in range(x.shape[0])]
    )
    poses_3d_df_honeycomb = poses_3d_df_honeycomb.reindex(columns=[
        'timestamp',
        'coordinate_space_id',
        'pose_model_id',
        'keypoint_coordinates_3d',
        'pose_ids_2d',
        'source_id',
        'source_type'
    ])
    poses_3d_df_honeycomb.rename(
        columns={
            'coordinate_space_id': 'coordinate_space',
            'pose_model_id': 'pose_model',
            'keypoint_coordinates_3d': 'keypoints',
            'pose_ids_2d': 'poses_2d',
            'source_id': 'source'
        },
        inplace=True
    )
    poses_3d_list_honeycomb = poses_3d_df_honeycomb.to_dict(orient='records')
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Writing 3D pose data')
    result = client.bulk_mutation(
        request_name='createPose3D',
        arguments={
            'pose3D': {
                'type': 'Pose3DInput',
                'value': poses_3d_list_honeycomb
            }
        },
        return_object=[
            'pose_id'
        ],
        chunk_size=chunk_size
    )
    try:
        pose_ids_3d = [datum['pose_id'] for datum in result]
    except:
        raise ValueError('Received unexpected result from Honeycomb:\n{}'.format(result))
    return pose_ids_3d

def write_3d_pose_tracks(
    poses_3d_df,
    source_id,
    source_type,
    uri=None,
    token_uri=None,
    audience=None,
    client_id=None,
    client_secret=None,
    chunk_size=100
):
    poses_3d_df_copy = poses_3d_df.copy()
    current_index_name = poses_3d_df_copy.index.name
    poses_3d_df_copy = poses_3d_df_copy.reset_index().rename(columns={current_index_name: 'pose_id_3d'})
    pose_tracks_3d_df = poses_3d_df_copy.groupby('pose_track_3d_id').agg(
        poses_3d = pd.NamedAgg(
            column='pose_id_3d',
            aggfunc = lambda x: x.tolist()
        )
    )
    pose_tracks_3d_df['source'] = source_id
    pose_tracks_3d_df['source_type'] = source_type
    pose_tracks_3d_list = pose_tracks_3d_df.to_dict(orient='records')
    client = minimal_honeycomb.MinimalHoneycombClient(
        uri=uri,
        token_uri=token_uri,
        audience=audience,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info('Writing 3D pose tracks')
    result = client.bulk_mutation(
        request_name='createPoseTrack3D',
        arguments={
            'poseTrack3D': {
                'type': 'PoseTrack3DInput',
                'value': pose_tracks_3d_list
            }
        },
        return_object=[
            'pose_track_id'
        ],
        chunk_size=chunk_size
    )
    try:
        pose_track_ids = [datum['pose_track_id'] for datum in result]
    except:
        raise ValueError('Received unexpected result from Honeycomb:\n{}'.format(result))
    return pose_track_ids
