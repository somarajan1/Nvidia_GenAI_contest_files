import streamlit as st
#from langchain.llms import OpenAI
st.title('Artificial Intelligent Diet Assistant')

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
import os
from typing import Literal
from langgraph.graph import Graph

model = ChatNVIDIA(model="meta/llama3-70b-instruct", api_key="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")

AgentState = {}
AgentState["messages"] = []
AgentState["grocerylist"] = ""
AgentState["mealplan"] = ""

def patient_goal(input):
    messages = input["messages"]
    user_input = messages[-1]
    print(user_input) 
    query = user_input
    response = model.invoke(query)
    input["messages"].append(response.content)
    return input

def router(input):
    messages = input["messages"]
    user_input = messages[-1]
    if "diabetes" in user_input.lower():
        return "diabetes"
    elif "weightloss" in user_input.lower() or "weight loss" in user_input.lower():
        return "weightloss"
    else:
       return "unknown"
   

def diabetes_mealplan(input):
    messages = input["messages"]
    user_input = messages[-1]
    query = "Based on this response: \n" + user_input + prompt + "\n Please provide a detailed specific analysis and recommendations for managing the diabetic patient's condition, considering their sugar levels, dietary requirements, and any other relevant factors. Your response should be comprehensive and tailored to the patient's specific needs. Based on the correlation between blood sugar level and meal data can you create a weekly mealplan recommendation. Also make this based on cuisine type specified in Patient data as preffered Cuisine"
    response = model.invoke(query)
    input["mealplan"] = response.content
    return input

def weightloss_mealplan(input):
    messages = input["messages"]
    user_input = messages[-1]
    query = "Based on this response: \n" + user_input + prompt + "\n Please provide a detailed specific analysis and recommendations for managing patient's weightloss considering dietary requirements, and any other relevant factors such as BMI. Your response should be comprehensive and tailored to the patient's specific needs. Based on the correlation between patient data, BMI and meal data can you create a weekly mealplan recommendation. Also make this based on cuisine type the patient follows"
    response = model.invoke(query)
    input["mealplan"] = response.content
    return input

def grocery_list_generator(input):
    mealplan = input["mealplan"]
    query = "Based on this response: \n" + mealplan + "\n Based on the weekly meal plan information create a weekly shopping list of groceries to buy. Include quantity as well."
    response = model.invoke(query)
    input["grocerylist"] = response.content
    return input

def generate_response(input_text):
    # Create a new graph
    workflow = Graph()

    workflow.add_node("Patient_goal", patient_goal)
    workflow.add_node("diabetes_mealplan", diabetes_mealplan)
    workflow.add_node("weightloss_mealplan", weightloss_mealplan)
    workflow.add_node("Grocery_list", grocery_list_generator)

    workflow.add_conditional_edges(
        "Patient_goal",
        router,
        {
            "diabetes": "diabetes_mealplan",
            "weightloss": "weightloss_mealplan",
            "unknown": "__end__"
        },
    )
    
    workflow.add_edge("diabetes_mealplan", "Grocery_list")
    workflow.add_edge("weightloss_mealplan", "Grocery_list")

    workflow.add_edge("Grocery_list", "__end__")

    workflow.set_entry_point("Patient_goal")

    app = workflow.compile()

    inputs = {"messages": [input_text]}

    answer = app.invoke(inputs)
    st.info(answer["messages"][-1])
    st.info(answer["mealplan"])
    st.info(answer["grocerylist"])

with st.form('my_form'):
    text = st.text_area('Enter Meal Data:', 'Date,Meal,Food,Quantity,Sugar Intake (g)')
    text2 = st.text_area('Enter Blood Glucose Data-optional only for diabetes', 'Date,Time,Blood Glucose Level (mg/dL)')
    text3 = st.text_area('Enter Patient Data:', 'Patient ID,Name,Age,Gender,Weight (kg),Height (cm),Preferred Cuisine')
    goal = st.text_input('Enter your goal (diabetes or weightloss):', 'diabetes')
    submitted = st.form_submit_button('Submit')
    if submitted:
        prompt = f"""
        Based on the following patient information:

        Goal:
        {goal}

        Patient Data:
        {text3}

        Sugar Data:
        {text2}

        Meal Data:
        {text}
        Based on the patient goal provided identify whether patient goal is to manage diabetes or manage weightloss. Give output as diabetes or weightloss or unknown
        """
        generate_response(prompt)