# OSWDataQC
This repository is a standalone, perhaps eventually folded into a middle layer, for quality control of sidewalk data (entity-based, per the OSW schema) in OpenStreetMap.

## How to get started?
1. create an environment to run the project and install the required packages. To use conda for this:
```
conda create -n osw_conf python=3.10
conda activate osw_conf
pip install -r requirements.txt
```
2. Confidence score calculation is handled by `analyze_area` function under `scripts\new_get_metrics.py` file. To run the script, one needs to have an account on OSM and have access to the OSM API. Update the lines USERNAME = "", PASSWORD = "" in the `scripts\new_get_metrics.py`
3. See the `new_get_metrics.py` last line on how to invoke the calculations. (This can be improved)

