# process_pose_data

Tools for fetching, processing, visualizing, and analyzing Wildflower human pose data

## Task list

* Add ability to overlay 3D poses on videos (without using `geom_render`)
* Incorporate `tqdm.auto` to get rid of all of the `if` statements for notebook mode
* Implement `tqdm` progress bars for `groupby(...).apply(...)` loops
* Add progress bars to all pipeline functions
* Restructure `process_poses_by_timestamp` to use `groupby(...).apply(...)` pattern
* Figure out inconsistent behavior of groupby-apply (under what conditions does it add grouping variables to index?)
* For functions that act on dataframes, make it optional to check dataframe structure (e.g., only one timestamp and camera pair)
* For functions than iterate over previous functions, making naming and approach consistent (e.g., always use apply?)
* For functions that act on dataframes, be consistent about `inplace` option
* Create combined pipeline function that goes from 2D poses to 3D poses
* Create function which creates `pose_3d_range` based on room boundaries, height limits
* Add ability to upload 3D poses to Honeycomb
* Clean out unused code
* Be consistent about whether to convert track labels to integers (where possible)
* Be consistent about accepting timestamp arguments in any format parseable by `pd.to_datetime()`
* Fix up _y_ axis inversion for images (go back to `cv_utils`?)
* Add option of specifying Honeycomb client info for visualization functions that require Honeycomb
* Reinstate `sns.set()` for Seaborn plots without making it spill over into non-Seaborn plots (see [here](https://stackoverflow.com/questions/26899310/python-seaborn-to-reset-back-to-the-matplotlib))
* Refactor code in `visualize` to make it less repetitive (same pattern over and over for `[verb]_by_camera`)
* Fix up legend on pose track timelines
* Add visualization for number of poses per camera per timestamp
* Fix up `fetch` module to match design of `wf-video-io`
  - Allow user to supply Honeycomb client
  - Clean up default setting
  - Other?
* Replace `cv.triangulatePoints()` to increase speed (and hopefully accuracy)
* Get pose video overlays working again (for data with track labels)
* Rewrite geom rendering functions to handle the possibility of no track labels
* Rewrite function which overlays geoms on videos so that user can specify a time span that it is a subset of the geoms and/or the video
