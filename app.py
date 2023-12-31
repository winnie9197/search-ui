import streamlit as st
import requests
import os
import numpy # Use this to organize snippets information later on
import openai
import time

openai_api_key = os.environ.get('OPENAI_API_KEY')

messages = []

### Bing API
def search_bing(query):
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv('BING_API_KEY'),
    }
    params = {
        "q": query,
    }

    response = requests.get(url, headers=headers, params=params)
    results = response.json().get("webPages", {}).get("value", [])
    
    return results

### ChatGPT
def get_prompt_str_using_search_query(search_query, data, language):
    data_str = '\n'.join(data) 
    prompt = f"""
    Question: {search_query}
    Input: {data_str}
    Output: 
    - Return code to create an embeddable HTML visualization widget with above data {f"in {language}"}
    - Aim to answer the question and include relevant info in your visualization
    - Minimize error
    - Do not include any explanation in your response. Make the code runnable as is
    - Make sure to not include any code block markup or delimiters in your response
    - Make the visualization look great. eg. Feel free to include images in your HTML
    """

    #returning as HTML so we don't need to execute in streamlit
    return prompt


def get_prompt_iterate_accuracy(feedback):
    prompt = f"I want more accurate information on {feedback}"
    # Build a list of dicts to handle previous conversations
    return prompt

def ask_gpt(prompt):
    messages.append({       
        "role": "user", 
        "content": prompt
    })

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,     # TODO: add token limit check and/or truncate input messages
        temperature=0, # this is the degree of randomness of the model's output
    )
    prompt_text = response.choices[0].message["content"]

    return prompt_text

def execute_gpt_wrapper(): # mode: "code" or "html"
    # Ask GPT, measure prompt execution time
    prompt_start_time = time.time()
    prompt_input_html = get_prompt_str_using_search_query(search_query=search_query, data=all_snippets, language="html")
    prompt_input_code = get_prompt_str_using_search_query(search_query=search_query, data=all_snippets, language="streamlit")
    html_response = ask_gpt(prompt=prompt_input_html)
    prompt_end_time = time.time()
    code_response = ask_gpt(prompt=prompt_input_code)
    
    # Render in frontend
    with html_tab:
        html_response = html_response.strip('```html')
        display_html(html_response)
        prompt_execution_time = prompt_end_time - prompt_start_time
        st.write(f"GPT execution time: {prompt_execution_time:.2f} seconds")
    with code_tab:
        display_code(code_response)
        st.write(f"GPT execution time: {(time.time()-prompt_end_time):.2f} seconds")

    return html_response

### Display
def display_code(code_response):
    # ensure ```python``` is removed
    code_response = code_response.strip('```python')

    # Display in code (important: check the code to avoid security risks)
    st.write("Code from GPT:")
    st.code(code_response)

    st.write("WARNING: Be very careful with this! Make sure the code is safe to run.")
    # Optional: Ask the user if they want to execute the code
    if st.button("Execute Code"):
        exec(code_response)

def display_html(html_response):
    # ensure ```html``` is removed
    # html_response = html_response.strip('```html')
    # Display in html
    # There’s also a components.iframe in case you want to embed an external website into Streamlit, such as components.iframe("https://docs.streamlit.io/en/latest")
    st.components.v1.html(html_response, height=600)

st.title('Bing Search App')
query = st.text_input('Enter your search query:')
if query:
    search_query = f"Searching for: {query}"
    st.write(search_query)
    results = search_bing(query)
    all_snippets = []
    for result in results:
        # [Text from: url] in GPT4 plus prompt for internet access
        # st.markdown(f"[{result['name']}]({result['url']})")
        
        all_snippets.append(result['snippet'])

    html_tab, code_tab = st.tabs(["Html", "Code"])
    
    html_response = execute_gpt_wrapper()

    while not html_response:
        time.sleep(2)

    with st.expander("Provide Feedback"):
        # Provide a text area for the user to write feedback
        feedback = st.text_input("I'd like to iterate on...")
        
        if feedback:
            execute_gpt_wrapper()