#!/usr/bin/env python
import os
import json
import asyncio
from typing import List
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

from agents.crews.crew_company_overview.crew_company_overview import CompanyOverviewCrew

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel


# DEFINE UTILITY FUNCTIONS

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = 5432


def get_db_connection():
    """Creates and returns a database connection."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def fetch_job_details(job_id):
    """Reads job details from the database using job_id."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM reports WHERE id = %s;", (job_id,))
            job_details = cur.fetchone()  # Retrieve the job details
        return job_details
    except Exception as e:
        print(f"Error fetching job details: {e}")
        return None
    finally:
        conn.close()


def update_job_status(job_id, status, result=None):
    """Updates the status and result of a job."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE reports
                SET status = %s, result = %s, updated_at = NOW()
                WHERE id = %s;
                """,
                (status, json.dumps(result) if result else None, job_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating job: {e}")
        return False
    finally:
        conn.close()


# DEFINE SCHEMA

class CompetitorResearchState(BaseModel):
    overview: str = ""


# LOGIC FOR THE ACTUAL FLOW

class CompetitorResearchFlow(Flow[CompetitorResearchState]):
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id
        self.job_details = None

    initial_state = CompetitorResearchState

    @start()
    async def load_job_document(self):
        print("Loading job document...")
        
        self.job_details = fetch_job_details(self.job_id)
        
        if self.job_details:
            print(f"Retrieving content for job_id: {self.job_id}:")
            print(self.job_details)
        else:
            print(f"Error: impossible to retrive content from job_id: {self.job_id}")

    
    # BASED ON COMPANY WEBSITE, OPEN WEBSITE AND SCRAPE ITS CONTENT. ADD CONTENT TO STATE
    # CREATE COMPANY OVERVIEW
        # TARGET INDUSTRIES / SECTORS
        # COMPANY SIZES THEY CATER TO
        # GEOGRAPHIC LOCATIONS THEY CATER TO
        # CUSTOMER CHARACTERISTICS
        # PAINPOINTS


    @listen("load_job_document")
    async def call_company_overview_crew(self):
        print("START EXECUTING: COMPANY OVERVIEW CREW")

        job_id = self.job_id
        user_input = self.job_details[5] if self.job_details else None
        print("User input:")
        print(user_input)

        async def generate_company_overview_single_company(user_input):
            conn = None
            try:
                result = await (
                    CompanyOverviewCrew()
                    .crew()
                    .kickoff_async(user_input)
                )
                print("RESULT BELOW")
                print(result)
                # print("PYDANTIC RESULT BELOW")
                
                result_json = result.pydantic.dict() if hasattr(result.pydantic, 'dict') else {"overview": result.pydantic.company_overview}
                self.state.overview = result.pydantic.overview
                
                update_successful = update_job_status(self.job_id, "In Progress", result=result_json)
                if update_successful:
                    print(f"Job {self.job_id} updated successfully.")
                else:
                    print(f"Error: could not update job_id: {self.job_id}.")

            except Exception as e:
                print(f"An error occurred: {e}")
                error_result = {"error": str(e)}
                update_job_status(self.job_id, "Failed", result=error_result)

        asyncio.create_task(generate_company_overview_single_company(user_input))

        print("FINISHED EXECUTING: COMPANY OVERVIEW CREW")

    
    @listen("load_job_document")
    async def call_company_overview_crew(self):
        print("START EXECUTING: COMPANY OVERVIEW CREW")

        job_id = self.job_id
        user_input = self.job_details[5] if self.job_details else None
        print("User input:")
        print(user_input)

        async def generate_company_overview_single_company(user_input):
            conn = None
            try:
                result = await (
                    CompanyOverviewCrew()
                    .crew()
                    .kickoff_async(user_input)
                )
                print("RESULT BELOW")
                print(result)
                # print("PYDANTIC RESULT BELOW")
                
                result_json = result.pydantic.dict() if hasattr(result.pydantic, 'dict') else {"overview": result.pydantic.company_overview}
                self.state.overview = result.pydantic.overview
                
                update_successful = update_job_status(self.job_id, "Completed", result=result_json)
                if update_successful:
                    print(f"Job {self.job_id} updated successfully.")
                else:
                    print(f"Error: could not update job_id: {self.job_id}.")

            except Exception as e:
                print(f"An error occurred: {e}")
                error_result = {"error": str(e)}
                update_job_status(self.job_id, "Failed", result=error_result)

        asyncio.create_task(generate_company_overview_single_company(user_input))

        print("FINISHED EXECUTING: COMPANY OVERVIEW CREW")

    
    # @listen("load_job_document")
    # async def call_competitor_research_crew(self):
    #     print("START EXECUTING CREW")

    #     job_id = self.job_id
    #     user_input = self.job_details[5] if self.job_details else None
    #     print("User input:")
    #     print(user_input)

    #     async def competitor_research_single_company(user_input):
    #         conn = None
    #         try:
    #             result = await (
    #                 WelcomerCrew()
    #                 .crew()
    #                 .kickoff_async(user_input)
    #             )
    #             # print("RESULT BELOW")
    #             # print(result)
    #             # print("PYDANTIC RESULT BELOW")
                
    #             result_json = result.pydantic.dict() if hasattr(result.pydantic, 'dict') else {"overview": result.pydantic.overview}

    #             update_successful = update_job_status(self.job_id, "Completed", result=result_json)
    #             if update_successful:
    #                 print(f"Job {self.job_id} updated successfully.")
    #             else:
    #                 print(f"Error: could not update job_id: {self.job_id}.")

    #         except Exception as e:
    #             print(f"An error occurred: {e}")
    #             error_result = {"error": str(e)}
    #             update_job_status(self.job_id, "Failed", result=error_result)

    #     asyncio.create_task(competitor_research_single_company(user_input))

    #     print("FINISHED EXECUTING CREW")


    @listen("call_company_overview_crew")
    async def step4(self):
        print(f"DONE WITH ENTIRE FLOW")
        print("COMPANY OVERVIEW BELOW")
        print(self.state.overview)
        print("COMPANY OVERVIEW ABOVE")


def kickoff():
    """
    Run the flow.
    """
    lead_score_flow = CompetitorResearchFlow()
    lead_score_flow.kickoff()


def plot():
    """
    Plot the flow.
    """
    lead_score_flow = CompetitorResearchFlow()
    lead_score_flow.plot()


if __name__ == "__main__":
    kickoff()