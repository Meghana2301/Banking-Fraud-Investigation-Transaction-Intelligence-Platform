import unittest
from src.evaluation import metrics


class EvaluationTests(unittest.TestCase):
    def test_confusion_matrix(self):
        rows = [(90, 1, 100), (80, 0, 50), (20, 1, 10), (10, 0, 5)]
        result = metrics(rows, threshold=65)
        self.assertEqual((result["true_positives"], result["false_positives"], result["true_negatives"], result["false_negatives"]), (1, 1, 1, 1))
        self.assertEqual(result["precision"], 0.5)
        self.assertEqual(result["recall"], 0.5)
        self.assertEqual(result["review_queue_size"], 2)

    def test_empty_input(self):
        result = metrics([], threshold=65)
        self.assertEqual(result["precision"], 0)
        self.assertEqual(result["recall"], 0)
        self.assertEqual(result["review_queue_size"], 0)


if __name__ == "__main__":
    unittest.main()
