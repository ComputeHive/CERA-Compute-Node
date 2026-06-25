import app.executor.utils.worker as worker_module
from app.executor.utils.worker import worker, worker_init


class TestWorker:
    def setup_method(self):
        worker_module._fn_cache = {}

    def test_worker_init_and_single_kwargs(self, sample_flattened_code):
        sample_flattened_code.function_name = "double"
        worker_init(sample_flattened_code)
        assert worker("double", {"x": 5}) == 10

    def test_worker_batch_list_kwargs(self, sample_flattened_code):
        sample_flattened_code.function_name = "double"
        worker_init(sample_flattened_code)
        assert worker("double", [{"x": 1}, {"x": 2}, {"x": 3}]) == [2, 4, 6]

    def test_worker_named_kwargs_function(self, sample_flattened_code):
        sample_flattened_code.function_name = "add"
        worker_init(sample_flattened_code)
        assert worker("add", {"a": 2, "b": 3}) == 5
