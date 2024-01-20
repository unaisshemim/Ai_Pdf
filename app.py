import streamlit as st
import pymongo
import json
import langchain
langchain.verbose = False
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from authentication import *

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo"])

def get_data():
    client = init_connection()
    db = client.mydb
    items = db.mycollection.find()
    items = list(items)  # make hashable for st.cache_data
    return items

def collect_data(items):
    for item in items:
        st.write(f"Board: {item['board']}")
        st.write(f"Class: {item['class']} ")

    subjects = [item['subject'] for item in items]
    chapter_of_subjects = [chapters_subject['chapter'] for chapters_subject in items[0]['contents']]
    return subjects, chapter_of_subjects

def find_selected_chapter_details(items, chapter_box):
    selected_chapter_details = None
    for chapters_contents in items[0]['contents']:
        if chapters_contents['chapter'] == chapter_box:
            selected_chapter_details = chapters_contents['content']
    return selected_chapter_details

def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks

def get_vector_store(text_chunks):
    openai_api_key = st.secrets["openai"]["api_key"]
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vector_store):
    openai_api_key = st.secrets["openai"]["api_key"]

    llm = ChatOpenAI(openai_api_key=openai_api_key) 
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True
    )
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        response = st.session_state.conversation({'question': user_question})
        st.session_state.chat_history = response['chat_history']
        reversed_chat_history = reversed(st.session_state.chat_history)

        for i, message in enumerate(reversed_chat_history):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
    else:
        st.write("Conversation object not initialized. Please upload and process PDFs first.")

 # Define it globally


def main():
    load_dotenv()
    st.set_page_config(page_title="QF Innovate", page_icon="./assets/logo.png")
    st.write(css, unsafe_allow_html=True)
    global process_started
    process_started=verify_login()  
    items = get_data()

    subjects, chapter_of_subjects = collect_data(items)
    
    with st.form("subject_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject_box = st.selectbox("Select Subject: ", subjects, key="subjects_class", index=0)

        with col2:
            chapter_box = st.selectbox("Select Chapter: ", chapter_of_subjects, key="chapter_list", index=0)

        # Find the selected chapter details
        selected_chapter_details = find_selected_chapter_details(items, chapter_box)
        # Store the selected chapter details in raw_text
        raw_text = json.dumps(selected_chapter_details, indent=2)

        submitted = st.form_submit_button("Start")
        
        if submitted:
            with st.spinner("Processing"):
                text_chunks = get_text_chunks(raw_text)
                vector_store = get_vector_store(text_chunks)
                st.session_state.conversation = get_conversation_chain(vector_store)
                 # Toggle the value of process_started
        
    st.header("chat with the chapter :books:")
    
    # Check if the process has started before enabling the text input

    if process_started :
        user_question = st.text_input("Ask some questions", key="user_question")
        if user_question:
            handle_userinput(user_question)
    else:
        st.text("Press 'Start'.")

    with st.sidebar:
        st.image("./assets/logo.png")
        st.markdown('<div style="display: flex; justify-content: center;">QF Innovate</div>', unsafe_allow_html=True)

if __name__ == '__main__':
        main()

