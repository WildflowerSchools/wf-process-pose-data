# Local disk directory structure
DEFAULT_BASE_DATA_DIRECTORY = '/data'
DEFAULT_POSE_DETECTION_2D_OUTPUT_SUBDIRECTORY='prepared'
DEFAULT_POSE_PROCESSING_SUBDIRECTORY = 'pose_processing'


# 2D pose detection output structure version encodes a wide range of different choices:
# local tree structure, whether cameras are identified by assignment IDs or device IDs,
# whether pose objects are created for every frame or only for frames with poses (requiring
# inspection of image files to determine frame count for each video), whether output files contain lists or dicts, what information is included in output (versus inferred from tree structure and filenames), etc.
DEFAULT_POSE_DETECTION_2D_OUTPUT_STRUCTURE = 'gamma'

POSE_DETECTION_2D_OUTPUT_STRUCTURES = {
    'gamma': {
        'camera_identifier': 'device_id',
        'output_filename': 'alphapose-results.json'
    }
}
SUPPORTED_POSE_DETECTION_2D_OUTPUT_STRUCTURES = list(POSE_DETECTION_2D_OUTPUT_STRUCTURES.keys())

DEFAULT_ADJUST_TIMESTAMPS = True

# Batch length for 2D pose detection output structures that group videos into batches
DEFAULT_BATCH_LENGTH_MINUTES = 10

# Video parameters
VIDEO_DURATION_SECONDS = 10
VIDEO_FRAMES_PER_SECOND = 10
VIDEO_FRAMES_PER_VIDEO = 100
VIDEO_FRAME_PERIOD_MICROSECONDS = 100000