import pytest 
from models import Paper
from utils import format_paper_info

class TestFormatPaper:

    """ Tests for the format_paper_info utility function """

    def test_format_minimal_paper(self, minimal_paper): # Paper with only ID - function handles minimal data
        
        result = format_paper_info(minimal_paper)

        assert "Paper ID: test_minimal" in result
        assert "PDF: Not Available" in result
        assert "Title:" not in result


    def test_format_complete_paper(self, complete_paper): # Paper with all fields populated 

        result = format_paper_info(complete_paper)

        # Check all fields are present
        expected_content = [
            "Paper ID: test_complete",
            "Machine Learning in Economics",
            "Smith, John A.",
            "Johnson, Mary B.",
            "Date: 2024",
            "PDF: Available",
            "Machine Learning"
        ]
        
        missing = [item for item in expected_content if item not in result]
        assert not missing, f"Missing from output: {missing}\nActual:\n{result}"


    def test_format_many_authors(self, paper_with_many_authors): # Truncation check - authors 
        
        result = format_paper_info(paper_with_many_authors)

        expected_authors = [f"Author {i}" for i in range(3)]
        missing = [auth for auth in expected_authors if auth not in result]
        assert not missing, f"Missing authors: {missing}    Output: {result}"
        
        # Check truncation message
        assert "(and 7 more)" in result
        
        # Check later authors are NOT shown
        assert "Author 9" not in result, "Last author should be hidden"


    def test_format_many_subjects(self, paper_with_many_subjects): # Truncation check - subjects

        result = format_paper_info(paper_with_many_subjects)

        # Check first 3 subjects are shown
        expected_subjects = [f"Subject {i}" for i in range(3)]
        missing = [subj for subj in expected_subjects if subj not in result]
        assert not missing, f"Missing subjects: {missing}\nOutput:\n{result}"


        # Check ellipsis is shown
        assert "..." in result, "Ellipsis should indicate more subjects"
        
        # Verify later subjects are hidden
        for i in range(5, 10):
            assert f"Subject {i}" not in result, \
                f"Subject {i} should be hidden but was found in output"
    
