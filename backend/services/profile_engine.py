"""Profile learning engine for processing documents and building user context."""
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    WebBaseLoader
)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document as LangchainDocument

from sqlalchemy.orm import Session
from models import UserProfile, Document
from config import settings
from services.llm_clients import LLMClientFactory


class ProfileEngine:
    """Engine for learning user profiles from documents and generating context."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the profile learning engine.
        
        Args:
            db_session: Database session for storing results
        """
        self.db = db_session
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
    async def process_document(
        self, 
        document_id: int, 
        file_path: str, 
        file_type: str
    ) -> bool:
        """
        Process a single document and extract information.
        
        Args:
            document_id: Database ID of the document record
            file_path: Path to the document file
            file_type: Type of document (pdf, docx, txt, url)
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Update status
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                return False
            
            doc.embedding_status = "processing"
            self.db.commit()
            
            # Load document based on type
            langchain_docs = await self._load_document(file_path, file_type)
            
            if not langchain_docs:
                doc.embedding_status = "failed"
                self.db.commit()
                return False
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(langchain_docs)
            
            # Create or update vector store for this user
            user_profile = doc.user_profile
            vector_store_path = self._get_vector_store_path(user_profile.id)
            
            # Store embeddings
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(vector_store_path),
                collection_name=f"user_{user_profile.id}"
            )
            
            # Update document status
            doc.embedding_status = "completed"
            doc.processed = True
            doc.processed_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error processing document {document_id}: {str(e)}")
            if doc:
                doc.embedding_status = "failed"
                self.db.commit()
            return False
    
    async def _load_document(
        self, 
        file_path: str, 
        file_type: str
    ) -> List[LangchainDocument]:
        """
        Load document using appropriate loader.
        
        Args:
            file_path: Path to file or URL
            file_type: Type of document
            
        Returns:
            List of LangChain document objects
        """
        try:
            if file_type == "pdf":
                loader = PyPDFLoader(file_path)
            elif file_type == "txt":
                loader = TextLoader(file_path)
            elif file_type == "docx":
                loader = Docx2txtLoader(file_path)
            elif file_type == "url":
                loader = WebBaseLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Load in executor to avoid blocking
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, loader.load)
            return docs
            
        except Exception as e:
            print(f"Error loading document: {str(e)}")
            return []
    
    async def generate_profile_summary(self, user_profile_id: int) -> Optional[str]:
        """
        Generate a comprehensive profile summary from all documents.
        
        Args:
            user_profile_id: ID of the user profile
            
        Returns:
            Generated profile summary or None if failed
        """
        try:
            user_profile = self.db.query(UserProfile).filter(
                UserProfile.id == user_profile_id
            ).first()
            
            if not user_profile:
                return None
            
            # Get all processed documents
            processed_docs = self.db.query(Document).filter(
                Document.user_profile_id == user_profile_id,
                Document.processed == True
            ).all()
            
            if not processed_docs:
                return "No documents processed yet."
            
            # Query vector store for representative content
            vector_store_path = self._get_vector_store_path(user_profile_id)
            
            if not vector_store_path.exists():
                return "Vector store not initialized."
            
            vector_store = Chroma(
                persist_directory=str(vector_store_path),
                embedding_function=self.embeddings,
                collection_name=f"user_{user_profile_id}"
            )
            
            # Get diverse samples from the vector store
            # We'll query for different aspects
            queries = [
                "professional experience and expertise",
                "skills and strengths",
                "goals and aspirations",
                "decision making style and preferences"
            ]
            
            all_contexts = []
            for query in queries:
                results = vector_store.similarity_search(query, k=2)
                all_contexts.extend([doc.page_content for doc in results])
            
            # Combine context
            combined_context = "\n\n".join(all_contexts[:8])  # Limit to avoid token limits
            
            # Use Gemini to generate summary
            llm_client = LLMClientFactory.create_client("gemini", "gemini-2.5-flash")
            
            summary_prompt = f"""Based on the following information about a user, create a comprehensive profile summary that includes:
1. Professional background and expertise areas
2. Key skills and strengths
3. Decision-making style and preferences
4. Risk tolerance (low/moderate/high)
5. Notable goals or aspirations

Keep the summary concise (under 300 words) but informative.

User Information:
{combined_context}

Generate a well-structured profile summary:"""
            
            summary = await llm_client.generate(
                prompt=summary_prompt,
                temperature=0.3,  # Lower temperature for more factual
                max_tokens=400
            )
            
            # Update user profile
            user_profile.profile_summary = summary
            self.db.commit()
            
            return summary
            
        except Exception as e:
            print(f"Error generating profile summary: {str(e)}")
            return None
    
    async def extract_expertise_areas(self, user_profile_id: int) -> List[str]:
        """
        Extract key expertise areas from user documents.
        
        Args:
            user_profile_id: ID of the user profile
            
        Returns:
            List of expertise areas
        """
        try:
            vector_store_path = self._get_vector_store_path(user_profile_id)
            
            if not vector_store_path.exists():
                return []
            
            vector_store = Chroma(
                persist_directory=str(vector_store_path),
                embedding_function=self.embeddings,
                collection_name=f"user_{user_profile_id}"
            )
            
            # Query for expertise
            results = vector_store.similarity_search(
                "skills, expertise, proficiency, experience in",
                k=5
            )
            
            context = "\n".join([doc.page_content for doc in results])
            
            # Use LLM to extract structured expertise areas
            llm_client = LLMClientFactory.create_client("gemini", "gemini-2.5-flash")
            
            extraction_prompt = f"""Based on the following text, extract a list of 3-7 key expertise areas or domains. Return ONLY a comma-separated list of areas, nothing else.

Text:
{context}

Expertise areas (comma-separated):"""
            
            response = await llm_client.generate(
                prompt=extraction_prompt,
                temperature=0.2,
                max_tokens=100
            )
            
            # Parse response
            expertise_areas = [
                area.strip() 
                for area in response.split(',') 
                if area.strip()
            ]
            
            # Update user profile
            user_profile = self.db.query(UserProfile).filter(
                UserProfile.id == user_profile_id
            ).first()
            
            if user_profile:
                user_profile.expertise_areas = expertise_areas
                self.db.commit()
            
            return expertise_areas
            
        except Exception as e:
            print(f"Error extracting expertise: {str(e)}")
            return []
    
    def get_relevant_context(
        self, 
        user_profile_id: int, 
        query: str, 
        k: int = 3
    ) -> List[str]:
        """
        Retrieve relevant context for a query.
        
        Args:
            user_profile_id: ID of the user profile
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant text chunks
        """
        try:
            vector_store_path = self._get_vector_store_path(user_profile_id)
            
            if not vector_store_path.exists():
                return []
            
            vector_store = Chroma(
                persist_directory=str(vector_store_path),
                embedding_function=self.embeddings,
                collection_name=f"user_{user_profile_id}"
            )
            
            results = vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
            
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
            return []
    
    def _get_vector_store_path(self, user_profile_id: int) -> Path:
        """Get path for user's vector store."""
        base_path = Path(settings.chroma_persist_directory)
        return base_path / f"user_{user_profile_id}"
