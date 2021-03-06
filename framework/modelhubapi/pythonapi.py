import os
import io
import json
import time
from datetime import datetime
import numpy
import h5py

class ModelHubAPI:
    """
    Generic interface to access a model.
    """

    def __init__(self, model, contrib_src_dir):
        self.model = model
        self.output_folder = '/output'
        self.contrib_src_dir = contrib_src_dir
        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.framework_dir = os.path.normpath(os.path.join(this_dir, ".."))


    def get_config(self):
        """
        Returns:
            dict: Model configuration.
        """
        config_file_path = self.contrib_src_dir + "/model/config.json"
        return self._load_json(config_file_path)


    def get_legal(self):
        """
        Returns:
            dict:
                All of modelhub's, the model's, and the sample data's
                legal documents as dictionary. If one (or more) of the legal
                files don't exist, the error  will be logged with the
                corresponding key. Dictionary keys are:

                - modelhub_license
                - modelhub_acknowledgements
                - model_license
                - sample_data_license
        """
        contrib_license_dir = self.contrib_src_dir + "/license"
        legal = self._load_txt_as_dict(self.framework_dir + "/LICENSE", "modelhub_license")
        legal.update(self._load_txt_as_dict(self.framework_dir + "/NOTICE", "modelhub_acknowledgements"))
        legal.update(self._load_txt_as_dict(contrib_license_dir + "/model", "model_license"))
        legal.update(self._load_txt_as_dict(contrib_license_dir + "/sample_data", "sample_data_license"))
        return legal


    def get_model_io(self):
        """
        Returns:
            dict:
                The model's input/output sizes and types as dictionary.
                Convenience function, as this is a subset of what
                :func:`~get_config` returns
        """
        config_file_path = self.contrib_src_dir + "/model/config.json"
        config = self._load_json(config_file_path)
        if "error" in config:
            return config
        else:
            return config["model"]["io"]


    def get_samples(self):
        """
        Returns:
            dict:
                Folder and file names of sample data bundled with this model.
                The diconary key "folder" holds the absolute path to the
                sample data folder in the model container. The key "files"
                contains a list of all file names in that folder. Join these
                together to get the full path to the sample files.
        """
        try:
            sample_data_dir = self.contrib_src_dir + "/sample_data"
            _, _, sample_files = next(os.walk(sample_data_dir))
            return  {"folder": sample_data_dir,
                     "files": sample_files}
        except Exception as e:
            return {'error': repr(e)}


    def predict(self, input_file_path, numpyToFile=True, url_root=""):
        """
        Preforms the model's inference on the given input.

        Args:
            input_file_path (str or dict): Path to input file to run inference on.
                Either a direct input file or a json containing paths to all
                input files needed for the model to predict. The appropriate
                structure for the json can be found in the documentation.
                If used directly, you can also pass a dict with the keys.
            numpyToFile (bool): Only effective if prediction is a numpy array.
                Indicates if numpy outputs should be saved and a path to it is
                returned. If false, a json-serializable list representation of
                the numpy array is returned instead. List representations is
                very slow with large numpy arrays.
            url_root (str): Url root added by the rest api.

        Returns:
            dict, list, or numpy array:
                Prediction result on input data. Return type/foramt as
                specified in the model configuration (see :func:`~get_model_io`).
                In case of an error, returns a dictionary
                with error info.
        """
        try:
            config = self.get_config()
            start = time.time()
            input = self._unpack_inputs(input_file_path)
            output = self.model.infer(input)
            output = self._correct_output_list_wrapping(output, config)
            end = time.time()
            output_list = []
            for i, o in enumerate(output):
                name = config["model"]["io"]["output"][i]["name"]
                shape = list(o.shape) if isinstance(o, numpy.ndarray) else [len(o)]
                if isinstance(o, numpy.ndarray):
                    o = url_root + "api" + self._save_output(o, name) if numpyToFile else o.tolist()
                output_list.append({
                    'prediction': o,
                    'shape': shape,
                    'type': config["model"]["io"]["output"][i]["type"],
                    'name': name,
                    'description': config["model"]["io"]["output"][i]["description"]
                    if "description" in config["model"]["io"]["output"][i].keys() else ""
                })
            return {'output': output_list,
                    'timestamp': datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"),
                    'processing_time': round(end-start, 3),
                    'model':
                        { "id": config["id"],
                          "name": config["meta"]["name"]
                        }
                    }
        except Exception as e:
            print(e)
            return {'error': repr(e)}


    # -------------------------------------------------------------------------
    # Private helper functions
    # -------------------------------------------------------------------------

    def _unpack_inputs(self, file_path):
        """
        This utility function returns a dictionary with the inputs if a
        json file with multiple input files is specified, otherwise it just
        returns the file_path unchanged for single inputs
        It also converts the fileurl to a valid string (avoids html escaping)
        """
        if isinstance(file_path, dict):
            return self._check_input_compliance(file_path)
        elif file_path.lower().endswith('.json'):
            input_dict = self._load_json(file_path)
            for key, value in input_dict.items():
                if key == "format":
                    continue
                input_dict[key]["fileurl"] = str(value["fileurl"])
            return self._check_input_compliance(input_dict)
        else:
            return file_path


    def _check_input_compliance(self, input_dict):
        """
        Checks if the input dictionary has all the files needed as specified
        in the model config file and returns an error if not.
        * TODO: Check the other way round?
        """
        config = self.get_config()["model"]["io"]["input"]
        for key in config.keys():
            if key not in input_dict:
                raise IOError("The input json does not match the input schema in the " \
                                "configuration file")
        return input_dict


    def _load_txt_as_dict(self, file_path, return_key):
        try:
            with io.open(file_path, mode='r', encoding='utf-8') as f:
                txt = f.read()
                return {return_key: txt}
        except Exception as e:
            return {'error': str(e)}


    def _load_json(self, file_path):
        try:
            with io.open(file_path, mode='r', encoding='utf-8') as f:
                loaded_dict = json.load(f)
                return loaded_dict
        except Exception as e:
            return {'error': str(e)}

    def _write_json(self, file_path, output_dict):
        try:
            with open(file_path, mode='w') as f:
                json.dump(output_dict, f, ensure_ascii=False)
        except Exception as e:
            return {'error': str(e)}

    def _correct_output_list_wrapping(self, output, config):
        if not isinstance(output, list):
            return [output]
        elif isinstance(output, list) and len(config["model"]["io"]["output"])==1:
            return [output]
        elif isinstance(output, list) and len(config["model"]["io"]["output"])>1:
            return output
        else:
            return [{'error': "output formatting does not match output specifications in config file"}]

    def _save_output(self, output, name):
        now = datetime.now()
        path = os.path.join(self.output_folder,
                                 "%s.%s" % (now.strftime("%Y-%m-%d-%H-%M-%S-%f"),
                                 "h5"))
        h5f = h5py.File(path, 'w')
        dataset = h5f.create_dataset(name, data=output)
        dataset.attrs["type"] = numpy.string_(str(output.dtype))
        h5f.close()
        return path
