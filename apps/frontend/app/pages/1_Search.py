import streamlit as st
import urllib
import os
import sys
import re
import time
import random
from operator import itemgetter
from collections import OrderedDict
from langchain_core.documents import Document
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


try:
    from utils import get_search_results
    from prompts import DOCSEARCH_PROMPT_TEXT
except Exception as e:
    # Add the path four levels up
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
    from common.utils import get_search_results
    from common.prompts import DOCSEARCH_PROMPT_TEXT


st.set_page_config(page_title="GPT Smart Search", page_icon="📖", layout="wide")
# Add custom CSS styles to adjust padding
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                }
        </style>
        """, unsafe_allow_html=True)

st.header("GPT Smart Search Engine")


def clear_submit():
    st.session_state["submit"] = False


with st.sidebar:
    st.markdown("""# Instructions""")
    st.markdown("""

Example questions:
- Why Ross faked his death?
- Who proposed first, Chandler or Monica?
- What are the main risk factors for Covid-19?
- What medicine reduces inflammation in the lungs?
- Why Covid doesn't affect kids that much compared to adults?
- What is the acronim of the book "Made to Stick" and what does it mean? give a short explanation of each letter.
    
    \nYou will notice that the answers to these questions are diferent from the open ChatGPT, since these papers are the only possible context. This search engine does not look at the open internet to answer these questions. If the context doesn't contain information, the engine will respond: I don't know.
    """)

coli1, coli2= st.columns([3,1])
with coli1:
    query = st.text_input("Ask a question to your enterprise data lake", value= "What are the main risk factors for Covid-19?", on_change=clear_submit)

button = st.button('Search')



if (not os.environ.get("AZURE_SEARCH_ENDPOINT")) or (os.environ.get("AZURE_SEARCH_ENDPOINT") == ""):
    st.error("Please set your AZURE_SEARCH_ENDPOINT on your Web App Settings")
elif (not os.environ.get("AZURE_SEARCH_KEY")) or (os.environ.get("AZURE_SEARCH_KEY") == ""):
    st.error("Please set your AZURE_SEARCH_ENDPOINT on your Web App Settings")
elif (not os.environ.get("AZURE_OPENAI_ENDPOINT")) or (os.environ.get("AZURE_OPENAI_ENDPOINT") == ""):
    st.error("Please set your AZURE_OPENAI_ENDPOINT on your Web App Settings")
elif (not os.environ.get("AZURE_OPENAI_API_KEY")) or (os.environ.get("AZURE_OPENAI_API_KEY") == ""):
    st.error("Please set your AZURE_OPENAI_API_KEY on your Web App Settings")
elif (not os.environ.get("BLOB_SAS_TOKEN")) or (os.environ.get("BLOB_SAS_TOKEN") == ""):
    st.error("Please set your BLOB_SAS_TOKEN on your Web App Settings")

else: 
    os.environ["OPENAI_API_VERSION"] = os.environ["AZURE_OPENAI_API_VERSION"]
    
    MODEL = os.environ["GPT4o_DEPLOYMENT_NAME"]
    llm = AzureChatOpenAI(deployment_name=MODEL, temperature=0.5, max_tokens=1000)
                           
    if button or st.session_state.get("submit"):
        if not query:
            st.error("Please enter a question!")
        else:
            # Azure Search

            try:
                indexes = ["srch-index-files", "srch-index-csv", "srch-index-books"]
                k = 10  
                ordered_results = get_search_results(query, indexes, k=k, reranker_threshold=1, sas_token=os.environ['BLOB_SAS_TOKEN'])

                st.session_state["submit"] = True
                # Output Columns
                placeholder = st.empty()

            except Exception as e:
                st.markdown("Not data returned from Azure Search, check connection..")
                st.markdown(e)
            
            if "ordered_results" in locals():
                try:
                    top_docs = []
                    for key,value in ordered_results.items():
                        location = value["location"] if value["location"] is not None else ""
                        document = {"source": location,
                                    "score": value["score"],
                                    "page_content": value["chunk"]}
                        top_docs.append(document)
            
                        add_text = "Reading the source documents to provide the best answer... ⏳"

                    if "add_text" in locals():
                        with st.spinner(add_text):
                            if(len(top_docs)>0):
                                
                                # Define prompt template
                                DOCSEARCH_PROMPT = ChatPromptTemplate.from_messages(
                                        [
                                            ("system", DOCSEARCH_PROMPT_TEXT + "\n\Retrieved Documents:\n{context}\n\n"),
                                            ("human", "{question}"),
                                        ]
                                    )
                                
                                chain = (
                                    DOCSEARCH_PROMPT 
                                    | llm   # Passes the finished prompt to the LLM
                                    | StrOutputParser()  # converts the output (Runnable object) to the desired output (string)
                                )
                                
    
                                answer = chain.invoke({"question": query, "context":str(top_docs)})
                                
                            else:
                                answer = {"output_text":"No results found" }
                    else:
                        answer = {"output_text":"No results found" }


                    with placeholder.container():

                        st.markdown("#### Answer")
                        st.markdown(answer, unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown("#### Search Results")

                        if(len(top_docs)>0):
                            for key, value in ordered_results.items():
                                location = value["location"] if value["location"] is not None else ""
                                title = str(value['title']) if (value['title']) else value['name']
                                score = str(round(value['score']*100/4,2))
                                st.markdown("[" + title +  "](" + location + ")" + "  (Score: " + score + "%)")
                                st.markdown(value["caption"])
                                st.markdown("---")

                except Exception as e:
                    st.error(e)