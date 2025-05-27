import openai
import json
import os
import re
from dotenv import load_dotenv

try:
    import tools
except ImportError:
    print("Error: tools.py not found or there's an issue importing it.")
    print("Please ensure tools.py is in the same directory and all its dependencies are installed (chromadb, requests, beautifulsoup4).")
    exit()

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

if not API_KEY:
    print("Error: The OPENAI_API_KEY environment variable is not set.")
    print("Please set it in your .env file or as an environment variable.")
    exit()

try:
    client = openai.OpenAI(api_key=API_KEY)
except openai.OpenAIError as e:
    print(f"OpenAI API client initialization error: {e}")
    exit()

SCRAPE_URL_PREFIX = "TOOL_REQUEST: scrape_url(url="
GET_FROM_VDB_PREFIX = "TOOL_REQUEST: get_from_vdb("
TOOL_REQUEST_SUFFIX = ")"


def parse_scrape_url_request(llm_output: str) -> str | None:
    if llm_output.startswith(SCRAPE_URL_PREFIX) and llm_output.endswith(TOOL_REQUEST_SUFFIX):
        try:
            content_part = llm_output[len(SCRAPE_URL_PREFIX):-len(TOOL_REQUEST_SUFFIX)]
            if content_part.startswith('"') and content_part.endswith('"'):
                return content_part[1:-1]
        except Exception:
            return None
    return None

def parse_get_from_vdb_request(llm_output: str) -> tuple[str, str] | None:
    if llm_output.startswith(GET_FROM_VDB_PREFIX) and llm_output.endswith(TOOL_REQUEST_SUFFIX):
        args_str = llm_output[len(GET_FROM_VDB_PREFIX):-len(TOOL_REQUEST_SUFFIX)]
        query_match = re.search(r'query="([^"]*)"', args_str)
        category_match = re.search(r'category="([^"]*)"', args_str)
        if query_match and category_match:
            query = query_match.group(1)
            category = category_match.group(1)
            return query, category
    return None


def run_chat_loop():
    print(f"Simple Agent CLI (using model: {MODEL_NAME}, with real tools.py)")
    print("Enter a URL for the LLM to consider scraping, or ask a question.")
    print(f"LLM uses: {SCRAPE_URL_PREFIX}\"URL_HERE\"{TOOL_REQUEST_SUFFIX} for scraping.")
    print(f"LLM uses: {GET_FROM_VDB_PREFIX}query=\"QUERY_HERE\", category=\"DERIVED_CATEGORY_HERE\"{TOOL_REQUEST_SUFFIX} for VDB search.")
    print("Type 'exit' or 'quit' to end.")

    system_message_content = (
        f"You are a helpful assistant using the {MODEL_NAME} model. You have two tools available.\n"
        "1. URL Scraper: If the user provides text that you identify as a URL that should be processed (scraped and its content stored for later), "
        f"you MUST respond with ONLY the following exact format: {SCRAPE_URL_PREFIX}\"THE_URL_HERE\"{TOOL_REQUEST_SUFFIX}\n"
        "When a URL is scraped, its content is automatically categorized in the Vector Database (VDB). The category name is derived from the website's hostname by first removing any leading 'www.' prefix, then removing the top-level domain extension (e.g., '.com', '.org', '.edu'). The remaining part is then sanitized (dots become underscores). For example, 'www.fib.upc.edu' would result in a category like 'fib_upc'. Remember this specific naming convention for later queries.\n"
        "2. VDB Search: If the user asks a question and you believe the answer might be in the VDB from previously processed URLs, "
        f"you MUST respond with ONLY the following exact format: {GET_FROM_VDB_PREFIX}query=\"YOUR_SEARCH_QUERY\", category=\"DERIVED_CATEGORY_NAME\"{TOOL_REQUEST_SUFFIX}\n"
        "Replace \"YOUR_SEARCH_QUERY\" with the specific query, and \"DERIVED_CATEGORY_NAME\" with the category name formed according to the rule described above (e.g., for 'www.example.com', the category would be 'example'; for 'www.another.domain.co.uk', it would be 'another_domain_co').\n"
        "IMPORTANT: If you decide to use a tool, your response must consist *only* of the tool request string. Do not add any other text or explanation.\n"
        "If you can answer directly or the input is not a URL to scrape and does not require VDB search, then provide a direct answer to the user."
    )
    conversation_messages = [{"role": "system", "content": system_message_content}]

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print("Exiting agent.")
            break

        if not user_input:
            continue

        current_turn_messages = list(conversation_messages)
        current_turn_messages.append({"role": "user", "content": user_input})
        
        assistant_response_for_history = None

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=current_turn_messages
            )
            llm_initial_response = response.choices[0].message.content.strip()

            parsed_url_to_scrape = parse_scrape_url_request(llm_initial_response)
            parsed_vdb_params = parse_get_from_vdb_request(llm_initial_response)

            if parsed_url_to_scrape:
                print(f"AGENT: LLM identified URL for scraping: {parsed_url_to_scrape}")
                print(f"AGENT_TOOL: Calling tools.scrape_and_embed_website with URL: {parsed_url_to_scrape}")
                doc_ids = tools.scrape_and_embed_website(url=parsed_url_to_scrape)
                if doc_ids:
                    assistant_response_for_history = f"Understood. I have processed the URL {parsed_url_to_scrape}. Its content (found {len(doc_ids)} chunks) has been scraped and stored in the VDB."
                else:
                    assistant_response_for_history = f"I attempted to process the URL {parsed_url_to_scrape}, but failed to scrape or embed any content. It might be inaccessible or have no extractable text."
                print(f"Agent: {assistant_response_for_history}")
            
            elif parsed_vdb_params:
                vdb_query, vdb_category = parsed_vdb_params
                print(f"AGENT: LLM requested VDB search with query: \"{vdb_query}\" in category: \"{vdb_category}\"")
                print(f"AGENT_TOOL: Calling tools.query_information with query: \"{vdb_query}\", category: \"{vdb_category}\"")
                
                vdb_info_dict = tools.query_information(query_text=vdb_query, category=vdb_category)
                
                docs_list = vdb_info_dict.get('documents')
                vdb_results_text = "No specific documents found in VDB for your query in that category."

                if vdb_info_dict.get('error'):
                     vdb_results_text += f" (Error from VDB: {vdb_info_dict.get('error')})"
                elif docs_list and isinstance(docs_list, list) and len(docs_list) > 0 and isinstance(docs_list[0], list) and docs_list[0]:
                    vdb_results_text = "\n---\n".join(docs_list[0])
                    print(f"AGENT: VDB Results (snippet): \"{vdb_results_text[:150]}...\"")
                else:
                    print(f"AGENT: VDB returned no documents or an unexpected format for query: '{vdb_query}' in category '{vdb_category}'. Full response: {vdb_info_dict}")

                messages_for_synthesis = list(current_turn_messages)
                messages_for_synthesis.append({"role": "assistant", "content": llm_initial_response}) 
                messages_for_synthesis.append({
                    "role": "system",
                    "content": f"You previously decided to search the VDB category \"{vdb_category}\" with the query \"{vdb_query}\". "
                               f"The VDB returned the following information:\n---\n{vdb_results_text}\n---\n"
                               f"Based on this, please now provide a comprehensive answer to the user's original question: \"{user_input}\". "
                               "Answer directly without mentioning the VDB search process or tool formats."
                })
                
                print("AGENT: Asking LLM to synthesize answer using VDB results...")
                synthesis_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages_for_synthesis
                )
                assistant_response_for_history = synthesis_response.choices[0].message.content
                print(f"Agent: {assistant_response_for_history}")

            else:
                assistant_response_for_history = llm_initial_response
                print(f"Agent: {assistant_response_for_history}")

            conversation_messages.append({"role": "user", "content": user_input})
            if assistant_response_for_history is not None:
                 conversation_messages.append({"role": "assistant", "content": assistant_response_for_history})
            else:
                 conversation_messages.append({"role": "assistant", "content": "I encountered an issue processing that request fully."})

        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            conversation_messages.append({"role": "user", "content": user_input})
            conversation_messages.append({"role": "assistant", "content": "Sorry, I encountered an API error."})
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            conversation_messages.append({"role": "user", "content": user_input})
            conversation_messages.append({"role": "assistant", "content": "Sorry, an unexpected error occurred."})

if __name__ == "__main__":
    run_chat_loop()