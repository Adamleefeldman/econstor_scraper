import aiofiles 
from pydantic import BaseModel, Field 
from typing import Optional, List, Tuple
from datetime import datetime
from pathlib import Path 
 
 
class Paper(BaseModel):  # individual paper
    id: str 
    title: Optional[List[str]] = None 
    creator_name: Optional[List[str]] = None
    identifier_url: Optional[List[str]] = None
    date: Optional[List[str]] = None
    abstract: Optional[List[str]] = None
    subject: Optional[List[str]] = None


    def get_pdf_url(self) -> Optional[str]: 
        if self.identifier_url and len(self.identifier_url)>0: #extract first PDF URL
            return self.identifier_url[0]

        return None




class SearchHits(BaseModel): # search results 
    total: int 
    hits: List[Paper]




class EconBizResponse(BaseModel): # complete API response
    hits: SearchHits
    facets: Optional[dict] = None
    query: str = ""
    search_params: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def get_papers(self) -> List[Paper]:
        return self.hits.hits


    def get_pdf_urls(self) -> List[Tuple[str, str]]:
        results = []

        for paper in self.get_papers():
            pdf_url = paper.get_pdf_url()

            if pdf_url:
                results.append((paper.id, pdf_url))
        return results

    
    async def save(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents = True, exist_ok = True)
        async with aiofiles.open(filepath, 'w', encoding = 'utf-8') as f:
            await f.write(self.model_dump_json(indent = 2))


    @classmethod
    async def load(cls, filepath: Path) -> 'EconBizResponse':
        async with aiofiles.open(filepath, 'r', encoding = 'utf-8') as f:
            content = await f.read()
        return cls.model_validate_json(content)
