# backend/agents/query_runner.py
import os
import openai
from langchain import LLMChain, PromptTemplate
from langchain.sql_database import SQLDatabase
from langchain.sql_database import SQLDatabaseChain
from sqlalchemy import text
from db import SessionLocal
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

async def query_runner_agent(nl_query: str, user: str = "anonymous"):
    """
    1. Use LangChain SQLDatabaseChain to convert NL → SQL (given PostgreSQL).
    2. Execute SQL and return results + simple viz hint.
    """
    # 1. Build SQLDatabase
    #    We pass the sync connection string here; LangChain will use its own engine.
    database_url = os.getenv("DATABASE_URL").replace("+psycopg2", "").replace("+asyncpg", "")
    db = SQLDatabase.from_uri(database_url)

    # 2. Create SQLDatabaseChain
    #    We include the column_dictionary as context in the prompt.
    #    For brevity, we use the default prompt from LangChain.
    llm = openai.ChatCompletion  # using OpenAI via LangChain’s wrapper
    db_chain = SQLDatabaseChain.from_llm(
        llm=llm,
        database=db,
        verbose=False
    )

    # 3. Run the chain
    #    result contains both the SQL and the “answer” (we only need SQL to execute ourselves)
    chain_output = await asyncio.get_event_loop().run_in_executor(
        None, lambda: db_chain.run(nl_query)
    )
    # LangChain returns a string with both SQL and text. We’ll parse out the SQL
    # by looking for the first occurrence of “```sql\n…```”
    sql_start = chain_output.find("```sql")
    sql_end = chain_output.find("```", sql_start + 5)
    if sql_start != -1 and sql_end != -1:
        generated_sql = chain_output[sql_start + 5 : sql_end].strip()
    else:
        # fallback: assume entire output is SQL
        generated_sql = chain_output.strip()

    # 4. Execute generated_sql
    async with SessionLocal() as session:
        try:
            result = await session.execute(text(generated_sql))
            rows = result.fetchall()
            cols = result.keys()
            data = [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            return {"error": str(e)}

    # 5. Return: data + the SQL that was used
    return {
        "sql": generated_sql,
        "data": data
    }
