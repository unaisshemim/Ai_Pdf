import streamlit as st
from  dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings,HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub
import os

def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

# def get_pdf_text_from_directory(directory):
#     textbooks=""
#     # question_papers=""

#     for filename in os.listdir(directory):
#         print(filename)
#         if filename.endswith(".pdf"):
#             pdf_path = os.path.join(directory, filename)
#             pdf_reader = PdfReader(pdf_path)
#             text_content = ""
#             for page in pdf_reader.pages:
#                 text_content += page.extract_text() 

#             if "textbook" in filename.lower():
#                 textbooks += text_content
#             # elif "questionpaper" in filename.lower():
#                 # question_papers += text_content

#     return textbooks



def get_text_chunks(raw_text):
    text_splitter=CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks=text_splitter.split_text(raw_text)
    return chunks

def get_vector_store(text_chunks):
    embeddings=OpenAIEmbeddings()
    # embeddings=HuggingFaceEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore=FAISS.from_texts(texts=text_chunks,embedding=embeddings)
    return vectorstore

def get_conversation_chain(vector_store):
    llm=ChatOpenAI()
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})
    memory=ConversationBufferMemory(
        memory_key='chat_history',return_messages=True
    )
    conversation_chain=ConversationalRetrievalChain.from_llm(
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
    st.set_page_config(page_title="Chat with multiple pdf",page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    st.header("chat with multiple pdfs :books:")
    user_question=st.text_input("Ask the question about your pdf")

    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("your documents")
        pdf_docs= st.file_uploader('Upload your PDFs here and click on process' ,accept_multiple_files=True  )
        if st.button("process"):
            with st.spinner("Processing"):
                #get pdf text
                raw_text=get_pdf_text(pdf_docs)
                
                #multiple pdf fils upload automatically
                
                # textbooks= get_pdf_text_from_directory("pdf_files")
             
                
                #get text chunk

                text_chunks=get_text_chunks(raw_text)
               
                
               #create vector store
                vector_store=get_vector_store(text_chunks)
             
            
               #create conversion chain

                st.session_state.conversation=get_conversation_chain(vector_store)
            


        st.image("https://static.toiimg.com/photo/msid-66081026,width-96,height-65.cms")


if __name__== '__main__':
    main()