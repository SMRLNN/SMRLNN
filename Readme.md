# Python implementation of the paper: Structure Maintained Representation Learning Neural Network for Causal Inference

## To run the pipeline for training and evaluation on SMRLNN, here is an example (e.g. simulation data from outcome model 3):

1. Create/Modify config file in "configs" (e.g. n1000out3pps2.txt), where to update the input/output file paths and model hyperparameters.

2. Create/Modify sh file (e.g. n1000out3pps2.sh) to call the config files in step 1.

3. Run .sh file in step 2. (e.g. “sh n1000out3pps2.sh”)

4. Add output file paths into results_collector.py, and run it to extract all the ITE prediction errors in PEHE.txt (e.g. “python results_collector.py”)



