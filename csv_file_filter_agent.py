#!/usr/bin/env python3
"""
CSV File Filter Agent

This agent uses OpenAI to identify which CSV files from a results directory
are needed to answer a user query. It analyzes file basenames and returns
a filtered sublist of relevant files.

Usage:
    from csv_file_filter_agent import CSVFileFilterAgent
    
    agent = CSVFileFilterAgent()
    relevant_files = agent.filter_csv_files(user_query, csv_file_basenames)
"""
import os
import json
from typing import List
import os
from openai import OpenAI
from dotenv import load_dotenv
from langchain_experimental.agents import create_csv_agent
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

class CSVAgent:
    def __init__(self, openai_api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialize the CSV File Filter Agent.
        
        Args:
            openai_api_key: OpenAI API key. If None, will try to get from environment.
            model: OpenAI model to use for filtering decisions.
        """
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.langchain_model = ChatOpenAI(model_name=model)

    def filter_csv_files(self, user_query: str, csv_file_basenames: List[str]) -> List[str]:
        """
        Filter CSV files based on user query relevance.
        
        Args:
            user_query: The user's question or query
            csv_file_basenames: List of CSV file basenames to filter
            
        Returns:
            List of relevant CSV file basenames
        """
        if not csv_file_basenames:
            return []
        
        # Create the filtering prompt
        system_prompt = """You are a CSV file filtering agent. Your task is to identify which CSV files are most relevant to answer a given user query.

You will be provided with:
1. A user query/question
2. A list of CSV file basenames

Your job is to analyze the file names and determine which ones are likely to contain data relevant to answering the user's question.

Rules:
- Only return file basenames that are likely relevant to the query
- Consider keywords, financial terms, dates, and content types when matching
- If unsure, err on the side of including potentially relevant files
- Return the exact basenames as provided in the input list
- Return your response as a JSON array of strings

Example:
Query: "What were the revenue numbers for Q4 2024?"
Files: ["page_1_table_1_Q4_2024_Financial_Highlights.csv", "page_3_table_1_Balance_Sheet.csv", "page_5_Cash_Flow.csv"]
Response: ["page_1_table_1_Q4_2024_Financial_Highlights.csv"]"""

        user_prompt = f"""User Query: {user_query}

Available CSV Files:
{chr(10).join([f"- {filename}" for filename in csv_file_basenames])}

Return only the relevant CSV file basenames as a JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            try:
                result_data = json.loads(result_text)
                
                # Handle different JSON formats the model might return
                if isinstance(result_data, list):
                    filtered_files = result_data
                elif isinstance(result_data, dict):
                    # Try common keys
                    filtered_files = (result_data.get('files') or 
                                    result_data.get('relevant_files') or 
                                    result_data.get('csv_files') or 
                                    list(result_data.values())[0] if result_data else [])
                else:
                    filtered_files = []
                
                # Ensure all returned files are in the original list
                filtered_files = [f for f in filtered_files if f in csv_file_basenames]
                
                return filtered_files
                
            except json.JSONDecodeError:
                # Fallback: try to extract filenames from the response text
                filtered_files = []
                for filename in csv_file_basenames:
                    if filename in result_text:
                        filtered_files.append(filename)
                return filtered_files
                
        except Exception as e:
            print(f"Error in CSV file filtering: {e}")
            # Fallback: return all files if filtering fails
            return csv_file_basenames

    def filter_csv_files_from_directory(self, user_query: str, csv_directory: str) -> List[str]:
        """
        Filter CSV files from a directory based on user query relevance.
        
        Args:
            user_query: The user's question or query
            csv_directory: Path to directory containing CSV files
            
        Returns:
            List of relevant CSV file full paths
        """

        if not os.path.exists(csv_directory):
            raise FileNotFoundError(f"CSV directory not found: {csv_directory}")
        
        # Get all CSV files in the directory (basenames only for filtering)
        csv_basenames = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]
        
        # Filter using basenames
        filtered_basenames = self.filter_csv_files(user_query, csv_basenames)
        
        # Convert to full paths
        filtered_full_paths = [os.path.join(csv_directory, basename) for basename in filtered_basenames]
        
        return filtered_full_paths

    def analyze_csv_files_using_langchain(self, user_query: str, csv_file_basenames: List[str]) -> str:
        """
        Analyze CSV files using LangChain's CSV agent to answer the user query.

        Args:
            user_query: The user's question or query
            csv_file_basenames: List of CSV file basenames to analyze

        Returns:
            The agent's response to the user query
        """

        # Initialize LangChain OpenAI LLM

        # Create the CSV agent
        agent = create_csv_agent(self.langchain_model, csv_file_basenames, verbose=True, agent_type="openai-tools", allow_dangerous_code=True)

        # Run the agent with the user query
        response = agent.invoke({"input": user_query})

        return response["output"]

    def run(self, csv_directory: str = "pdf_etl_pipeline/results/csv"):
        """
        Run the CSV agent with predefined test queries.
        
        Args:
            csv_directory: Directory containing CSV files to analyze
        """
        # Test queries
        test_queries = [
            "What were the Q4 2024 revenue numbers?",
            "Show me the balance sheet information",
            "What are the cash flow details?",
            "Tell me about segment operating results",
            "What was the free cash flow?"
        ]

        print("CSV File Filter Agent - Test Results")
        print("=" * 50)

        for query in test_queries:
            print(f"\nQuery: {query}")

            relevant_files = self.filter_csv_files_from_directory(query, csv_directory)
            print(f"relevant_files\n{relevant_files}\n\n\n\n\n")
            result = self.analyze_csv_files_using_langchain(query, relevant_files)

            print(f"Response:: {result}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize the agent
    agent = CSVAgent()
    
    # Run the agent with default settings
    agent.run()
