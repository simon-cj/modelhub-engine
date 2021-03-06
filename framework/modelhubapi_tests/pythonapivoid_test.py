"""Implements test cases in which smth is wrong with the model setup"""

import unittest
import os
from modelhubapi import ModelHubAPI
from .mockmodels.contrib_src_si.inference import ModelThrowingError


class TestModelHubAPIVoidModel(unittest.TestCase):

    def setUp(self):
        model = ModelThrowingError()
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        void_contrib_src_dir = os.path.join(self.this_dir, "mockmodels", "void_contrib_src")
        self.api = ModelHubAPI(model, void_contrib_src_dir)


    def tearDown(self):
        pass


    def test_get_config_returns_error(self):
        result = self.api.get_config()
        self.assertIn("error", result)


    def test_get_legal_returns_error(self):
        result = self.api.get_legal()
        self.assertIn("error", result)


    def test_get_model_io_returns_error(self):
        result = self.api.get_model_io()
        self.assertIn("error", result)


    def test_get_samples_returns_error(self):
        result = self.api.get_samples()
        self.assertIn("error", result)


    def test_predict_returns_NotImplementedError(self):
        result = self.api.predict("MOCK_MODEL_NEEDS_NO_INPUT_FILE")
        self.assertIn("error", result)
        self.assertIn("NotImplementedError", result["error"])




if __name__ == '__main__':
    unittest.main()
