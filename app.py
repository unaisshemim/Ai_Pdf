import streamlit as st
import pymongo
import json
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template

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
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vector_store):
    llm = ChatOpenAI()
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

def main():
    load_dotenv()
    st.set_page_config(page_title="Ask Questions here", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    items = get_data()

    subjects, chapter_of_subjects = collect_data(items)

    with st.form("subject_form"):
        col1, col2 = st.columns(2)
        col1.selectbox("Select Subject: ",subjects , key="subjects_class")


        chapter_sub=col2.selectbox("Select Chapter: ",chapter_of_subjects , key="chapter_list")
    
        # Find the selected chapter details
        selected_chapter_details = None
        for chapters_contents in items[0]['contents']:
            if chapters_contents['chapter'] == chapter_sub:
                selected_chapter_details = chapters_contents['content']
        # Store the selected chapter details in raw_text
        raw_text = json.dumps(selected_chapter_details, indent=2)

        submitted = st.form_submit_button("Start")
        if submitted:
            with st.spinner("Processing"):
                text_chunks = get_text_chunks(raw_text)
                vector_store = get_vector_store(text_chunks)
                st.session_state.conversation = get_conversation_chain(vector_store)

    
    st.header("chat with the chapter :books:")
    user_question = st.text_input("Ask some questions")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:

        st.image("https://static.toiimg.com/photo/msid-66081026,width-96,height-65.cms")

if __name__ == '__main__':
    main()
