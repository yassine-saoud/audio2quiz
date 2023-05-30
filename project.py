from __future__ import print_function
import speech_recognition as sr
import openai
from time import sleep
import streamlit as st
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools


def audio2text():
    # Create a recognizer object
    r = sr.Recognizer()
    # Set the audio source as the default microphone
    mic = sr.Microphone()
    # Open the microphone for recording
    with mic as source:
        # Adjust microphone energy threshold to ambient noise level (optional)
        r.adjust_for_ambient_noise(source)
        print("start recording")
        audio = r.listen(source)
    try:
        # Use the recognizer to convert speech to text
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
    except sr.RequestError as e:
        print("Error: {0}".format(e))


openai.api_key = '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'
def get_form(text):
    message = "User: {}:".format(text)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}])
    # Extract and return the chatbot's reply
    form = response['choices'][0]['message']['content']
    return form    

def Quiz(questions,options):
    #-------------------Create Quiz Form ----------------------#
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

    # Request body for creating a form
    NEW_FORM = {
        "info": {
            "title": "Quiz form",
        }
    }
    # Creates the initial form
    result = form_service.forms().create(body=NEW_FORM).execute()
    # Request body to add a multiple-choice question
    # JSON to convert the form into a quiz
    update = {
        "requests": [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            }
        ]
    }
    # Converts the form into a quiz
    question_setting = form_service.forms().batchUpdate(formId=result["formId"],body=update).execute()
    for i in range(len(questions)): 
        NEW_QUESTION = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": questions[i],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value":j} for j in options[i]],
                                    "shuffle": True
                                }
                            }
                        },
                    },
                    "location": {
                        "index": i
                    }
                }
            }]
        }
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()

    get_result = form_service.forms().get(formId=result["formId"]).execute()
    return get_result['responderUri']




# Streamlit app
def main():
    st.title("Quiz")
    if st.button('Start Recording'):
        text=audio2text()
        st.write(text)
        form = get_form(text + 'the form of the quiz should be like this: number_of_question) question\na) option1\nb) option2\nc) option3\nd) option4\nAnswer: answer_alphabet) answer')

        l=form.split('\n\n')
        answers = [l[i][8:] for i in range(1,len(l),2)]
        questions = [l[i].split('\n')[0] for i in range(0,len(l),2)]
        options = [l[i].split('\n')[1:] for i in range(0,len(l),2)]

        link=Quiz(questions=questions,options=options)
        st.write(link)



if __name__ == "__main__":
    main()
