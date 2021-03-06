import unittest
import os
import numpy
import json 
import shutil
from modelhubapi import ModelHubAPI
from .apitestbase import TestAPIBase
from .mockmodels.contrib_src_si.inference import Model
from .mockmodels.contrib_src_si.inference import ModelReturnsOneNumpyArray
from .mockmodels.contrib_src_si.inference import ModelReturnsListOfOneNumpyArray, ModelReturnsListOfOneLabelList
from .mockmodels.contrib_src_mi.inference import ModelReturnsOneLabelList, ModelNeedsTwoInputs

class TestModelHubAPI(TestAPIBase):

    def setUp(self):
        model = Model()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_si")
        self.api = ModelHubAPI(model, contrib_src_dir)
        self.setup_self_temp_output_dir()
        self.api.output_folder = self.temp_output_dir


    def tearDown(self):
        shutil.rmtree(self.temp_output_dir, ignore_errors=True)
        pass


    def test_get_config_returns_no_error(self):
        config = self.api.get_config()
        self.assertNotIn("error", config)


    def test_get_config_returns_correct_dict(self):
        config = self.api.get_config()
        self.assert_config_contains_correct_dict(config)


    def test_get_legal_returns_expected_keys(self):
        legal = self.api.get_legal()
        self.assert_legal_contains_expected_keys(legal)


    def test_get_legal_returns_expected_mock_values(self):
        legal = self.api.get_legal()
        self.assert_legal_contains_expected_mock_values(legal)


    def test_get_model_io_returns_expected_mock_values(self):
        model_io = self.api.get_model_io()
        self.assert_model_io_contains_expected_mock_values(model_io)


    def test_get_samples_returns_path_to_mock_samples(self):
        samples = self.api.get_samples()
        self.assertEqual(self.this_dir + "/mockmodels/contrib_src_si/sample_data", samples["folder"])
        samples["files"].sort()
        self.assertListEqual(["testimage_ramp_4x2.jpg",
                              "testimage_ramp_4x2.png"],
                             samples["files"])


    def test_predict_returns_expected_mock_prediction_list(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png", numpyToFile=False)
        self.assert_predict_contains_expected_mock_prediction(result, expectList=True)

    def test_predict_returns_expected_mock_prediction_url(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png", numpyToFile=True)
        self.assert_predict_contains_expected_mock_prediction(result)

    def test_predict_returns_expected_mock_meta_info(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png")
        self.assert_predict_contains_expected_mock_meta_info(result)


    def test_predict_returns_correct_output_format(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png", numpyToFile=False)
        self.assertIsInstance(result["output"], list)
        self.assertIsInstance(result["output"][0]["prediction"], list)
        self.assertIsInstance(result["output"][0]["prediction"][0], dict)
        self.assertIsInstance(result["output"][0]["prediction"][1], dict)
        self.assertIsInstance(result["output"][1]["prediction"], list)


    def test_predict_output_types_match_config(self):
        model_io = self.api.get_model_io()
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png")
        self.assertEqual(len(model_io["output"]), len(result["output"]))
        for i in range(len(model_io["output"])):
            self.assertEqual(model_io["output"][i]["type"], result["output"][i]["type"])

# test cases for nultiple inputs
class TestModelHUBAPIMultiInput(unittest.TestCase):
    def setUp(self):
        model = ModelNeedsTwoInputs()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_mi")
        self.api = ModelHubAPI(model, contrib_src_dir)

    def tearDown(self):
        pass

    def test_predict_accepts_and_processes_valid_json(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_mi/sample_data/valid_input_list.json")
        self.assertEqual(result["output"][0]["prediction"][0], True)
    
    def test_predict_accepts_and_processes_valid_dict(self):
        with open(self.this_dir + "/mockmodels/contrib_src_mi/sample_data/valid_input_list.json", "r") as f:
            input_dict = json.load(f)
        result = self.api.predict(input_dict)
        self.assertEqual(result["output"][0]["prediction"][0], True)

    def test_predict_rejects_invalid_file(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png")
        self.assertIn("error", result)


class TestModelHubAPIModelReturnsOneNumpyArray(unittest.TestCase):

    def setUp(self):
        model = ModelReturnsOneNumpyArray()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_si")
        self.api = ModelHubAPI(model, contrib_src_dir)


    def tearDown(self):
        pass


    def test_predict_returns_expected_mock_prediction_list(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png", numpyToFile=False)
        self.assertListEqual([[0,1,1,0],[0,2,2,0]], result["output"][0]["prediction"])


    def test_predict_returns_correct_output_format(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png", numpyToFile=False)
        self.assertIsInstance(result["output"], list)
        self.assertIsInstance(result["output"][0]["prediction"], list)



class TestModelHubAPIModelReturnsListOfOneNumpyArray(TestModelHubAPIModelReturnsOneNumpyArray):

    def setUp(self):
        model = ModelReturnsListOfOneNumpyArray()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_si")
        self.api = ModelHubAPI(model, contrib_src_dir)

class TestModelHubAPIUtitilyFunctions(unittest.TestCase):

    def setUp(self):
        model = ModelReturnsOneLabelList()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        # load config version 2 with only one output specified
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_mi")
        self.api = ModelHubAPI(model, contrib_src_dir)


    def tearDown(self):
        pass

    def test_json_write_fails_for_invalid_path(self):
        result = self.api._write_json({"some":"key"}, "this/does/not/exist/johndoe.json")
        self.assertIn("error", result)

class TestModelHubAPIModelReturnsOneLabelList(unittest.TestCase):

    def setUp(self):
        model = ModelReturnsOneLabelList()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        # load config version 2 with only one output specified
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_mi")
        self.api = ModelHubAPI(model, contrib_src_dir)


    def tearDown(self):
        pass


    def test_predict_returns_expected_mock_prediction(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png")
        self.assertEqual(0.3, result["output"][0]["prediction"][0]["probability"])
        self.assertEqual("class_1", result["output"][0]["prediction"][1]["label"])
        self.assertEqual(0.7, result["output"][0]["prediction"][1]["probability"])
        self.assertEqual("class_0", result["output"][0]["prediction"][0]["label"])


    def test_predict_returns_correct_output_format(self):
        result = self.api.predict(self.this_dir + "/mockmodels/contrib_src_si/sample_data/testimage_ramp_4x2.png")
        self.assertIsInstance(result["output"], list)
        self.assertIsInstance(result["output"][0]["prediction"], list)
        self.assertIsInstance(result["output"][0]["prediction"][0], dict)
        self.assertIsInstance(result["output"][0]["prediction"][1], dict)



class TestModelHubAPIModelReturnsListOfOneLabelList(TestModelHubAPIModelReturnsOneLabelList):

    def setUp(self):
        model = ModelReturnsListOfOneLabelList()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "contrib_src_si")
        self.api = ModelHubAPI(model, contrib_src_dir)




if __name__ == '__main__':
    unittest.main()
