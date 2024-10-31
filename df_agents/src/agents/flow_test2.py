#!/usr/bin/env python
import os
import json
import asyncio
from typing import List
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

from agents.crews.crew_welcomer.crew_welcomer import WelcomerCrew

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel

class WelcomeMessageState(BaseModel):
    overview: str = ""


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


# LOGIC FOR THE ACTUAL FLOW

class LeadScoreFlow(Flow[WelcomeMessageState]):
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    initial_state = WelcomeMessageState

    @start()
    async def load_job_document(self):
        print("Loading job document...")
        
        job_details = fetch_job_details(self.job_id)
        
        if job_details:
            print("&&&&&&&&&&&&&")
            print(f"Job Document for JOB ID {self.job_id}:")
            print(job_details)
            print("&&&&&&&&&&&&&")
        else:
            print(f"Errore: Impossibile recuperare i dettagli per JOB ID {self.job_id}")

    @listen("load_job_document")
    async def step2(self):
        print(f"BBBBBBBBBB")

    @listen("step2")
    async def step3(self):
        print("About to start the crew")
        print(f"################# Using Job ID: {self.job_id}")

        job_id = self.job_id

        async def score_single_candidate(job_id):
            conn = None
            try:
                result = await (
                    WelcomerCrew()
                    .crew()
                    .kickoff_async(
                        # inputs={
                        #     "something": "else",
                        # }
                    )
                )
                # print("RESULT BELOW")
                # print(result)
                # print("PYDANTIC RESULT BELOW")
                
                result_json = result.pydantic.dict() if hasattr(result.pydantic, 'dict') else {"overview": result.pydantic.overview}

                update_successful = update_job_status(self.job_id, "Completed", result=result_json)
                if update_successful:
                    print(f"Job {self.job_id} aggiornato con successo.")
                else:
                    print(f"Errore nell'aggiornamento del job {self.job_id}.")

            except Exception as e:
                print(f"An error occurred: {e}")
                error_result = {"error": str(e)}
                update_job_status(self.job_id, "Failed", result=error_result)

        asyncio.create_task(score_single_candidate(job_id))

        print("FINISHED EXECUTING CREW")


    @listen("step3")
    async def step4(self):
        print(f"CCCCCCCCCC")


def kickoff():
    """
    Run the flow.
    """
    lead_score_flow = LeadScoreFlow()
    lead_score_flow.kickoff()


def plot():
    """
    Plot the flow.
    """
    lead_score_flow = LeadScoreFlow()
    lead_score_flow.plot()


if __name__ == "__main__":
    kickoff()