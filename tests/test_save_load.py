import pytest
from pathlib import Path
from models import Paper, SearchHits, EconBizResponse
from utils import load_saved_responses, list_saved_responses
import json


class TestSaveLoadCycle:

    @pytest.mark.asyncio
    async def test_data_preserved(self, temp_dir, complete_paper, econbiz_response):

        """ Test saving and loading preserves data integrity"""

        
        original = econbiz_response(
            papers=[complete_paper],
            total=100,
            query="test query",
            search_params={"q": "test", "size": 10},
            facets={"language": ["en"]}
        )
        
        # Save
        filepath = temp_dir / "test_response.json"
        await original.save(filepath)
        
        # Load
        loaded = await load_saved_responses(filepath)

        # Verify all fields match after load
        assert loaded.query == original.query
        assert loaded.hits.total == original.hits.total
        assert loaded.search_params == original.search_params
        assert loaded.facets == original.facets

        # Verify papers 
        loaded_papers = loaded.get_papers()
        original_papers = original.get_papers()
        assert len(loaded_papers) == len(original_papers)

        # Verify first paper details
        assert loaded_papers[0].id == original_papers[0].id
        assert loaded_papers[0].title == original_papers[0].title
        assert loaded_papers[0].creator_name == original_papers[0].creator_name
        assert loaded_papers[0].get_pdf_url() == original_papers[0].get_pdf_url()


    @pytest.mark.asyncio
    async def test_parent_directory_created(self, temp_dir, minimal_paper, econbiz_response):
        
        """ Test saving creates a parent directory if does not exist """

        response = econbiz_response(papers=[minimal_paper])

        nested_path = temp_dir / "nested" / "path" / "response.json"

        await response.save(nested_path)
        assert nested_path.exists()
        assert nested_path.parent.exists()


    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, temp_dir):
        
        """ Test loading non-existent file raises correct exception """

        nonexistent_path = temp_dir / "nonexistent.json"

        result = await load_saved_responses(nonexistent_path)

        assert result is None

    def test_list_saved_responses(self, temp_dir):

        """ Test listing ALL saved responses in a directory and in sorted order """

        # Dummy files
        (temp_dir / "response_b_20250117.json").touch()
        (temp_dir / "response_a_20250116.json").touch()
        (temp_dir / "response_c_20250118.json").touch()
        (temp_dir / "not_a_response.txt").touch() # Should be ignored 

        files = list_saved_responses(temp_dir)
        assert len(files) == 3
        assert all(f.name.startswith("response") and f.suffix == ".json" for f in files)

        # Check sorted order by filename
        assert files[0].name == "response_a_20250116.json"
        assert files[1].name == "response_b_20250117.json"
        assert files[2].name == "response_c_20250118.json"

