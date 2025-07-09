import json
import pickle
from datetime import date, datetime, timedelta

import numpy as np
import google.generativeai as genai
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from accounts.models import CustomUser
from .models import ChatMessage, UserTodo

# --- Configuration & Model Loading ---

# Load ML models
DIABETES_MODEL = pickle.load(open('case_companion/diabetes_model.sav', 'rb'))
HEART_MODEL = pickle.load(open('case_companion/heart_model.sav', 'rb'))

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDA_-bru_PHUbgHDmRBsXHMbzWyQKpII5w" 
genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODEL = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024, # Ensure this is sufficient for your reports
    }
)

# --- Helper Functions: AI Interactions ---

def _generate_ai_content(prompt: str) -> str:
    """Handles interaction with the Gemini model and returns stripped text."""
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Log the error for debugging, but return a user-friendly message
        print(f"Gemini API error: {e}")
        return "Sorry, I'm having trouble connecting right now. Please try again later."

def handle_general_health(message: str) -> str:
    """Provides general health advice using AI."""
    prompt = (
        "You are Curo, a friendly general health assistant. Provide concise, accurate health advice based on the user’s query. "
        "For specific needs, suggest using the mode selector. Keep responses natural and supportive.\n\n"
        f"Query: {message}"
    )
    return _generate_ai_content(prompt)

def handle_symptoms_predictor(input_data: str) -> str:
    """Analyzes symptoms using AI."""
    prompt = (
        "You are Curo, a health assistant. Analyze the user's input and determine if the described symptoms suggest a health concern. "
        "If age is provided, consider it in your assessment. Provide a concise response with a recommendation (e.g., 'Healthy: Symptoms seem mild. Stay hydrated and monitor.' or 'Possible risk: Symptoms suggest a concern. Consult a doctor.'). "
        "If the input is unstructured or lacks age, suggest the user provide age and symptoms in the format 'age: 30, symptoms: fatigue, headache'. "
        f"Input: {input_data}"
    )
    return _generate_ai_content(prompt)

def handle_mental_health(input_data: str, user: CustomUser) -> str:
    """Provides mental health support and suggests activities using AI."""
    prompt = (
        "You are Curo, a mental health assistant. Provide supportive advice based on the user’s input (e.g., feelings like 'sadness' or 'stress'). "
        "If appropriate, **suggest a specific actionable mental well-being activity** that the user could add to their daily routine, like 'meditation', 'mindful breathing', 'short walk', 'journaling', or 'reaching out to a friend'. "
        "Format the suggestion clearly, for example: 'I suggest you try [activity] today.' Keep it friendly and concise.\n\n"
        f"Query: {input_data}"
    )
    curo_response = _generate_ai_content(prompt)

    # Check for suggested activity from AI response
    suggested_activity = None
    if "i suggest you try" in curo_response.lower():
        if "meditation" in curo_response.lower():
            suggested_activity = "meditation"
        elif "mindful breathing" in curo_response.lower() or "breathing exercise" in curo_response.lower():
            suggested_activity = "mindful breathing"
        elif "walk" in curo_response.lower():
            suggested_activity = "short walk"
        elif "journaling" in curo_response.lower():
            suggested_activity = "journaling"
        elif "reaching out to a friend" in curo_response.lower():
            suggested_activity = "reach out to a friend"
        # Add more keywords for activities here as needed

    if suggested_activity:
        # Store in session for follow-up
        user.session['last_suggested_activity'] = suggested_activity
        curo_response += f"\n\nWould you like me to add '{suggested_activity}' to your to-do list? (Say 'yes' or 'no')"
    return curo_response

def handle_disease_predictor(input_data: str, disease_type: str) -> str:
    """Predicts disease risk using loaded ML models."""
    try:
        inputs = {}
        for part in input_data.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":")
            key = key.strip()
            value = value.strip()
            if key == "disease": # Skip if 'disease' key is present
                continue
            inputs[key] = float(value)

        if disease_type == "diabetes":
            required_keys = ['pregnancies', 'glucose', 'blood_pressure', 'skin_thickness', 'insulin', 'bmi', 'diabetes_pedigree_function', 'age']
            if not all(k in inputs for k in required_keys):
                raise ValueError("Missing required inputs for diabetes prediction.")
            model_input = [inputs[k] for k in required_keys]
            prediction = DIABETES_MODEL.predict(np.array(model_input).reshape(1, -1))
            if prediction[0] == 0:
                return "You are likely healthy regarding diabetes. Maintain a balanced diet and exercise 30 minutes daily."
            return "There is a risk of diabetes. Consult a doctor and reduce refined carbs."
        
        elif disease_type == "heart":
            required_keys = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']
            if not all(k in inputs for k in required_keys):
                raise ValueError("Missing required inputs for heart disease prediction.")
            model_input = [inputs[k] for k in required_keys]
            prediction = HEART_MODEL.predict(np.array(model_input).reshape(1, -1))
            if prediction[0] == 0:
                return "You are likely healthy regarding heart disease. Try regular cardio and a veggie-rich diet."
            return "There is a risk of heart disease. See a doctor and consider lowering salt intake."
        
        else:
            return "Invalid disease type selected for prediction."
    except ValueError as ve:
        return f"Error: {ve}. Please provide inputs in the correct format. For diabetes: 'pregnancies: 2, glucose: 120, ..., age: 30'. For heart: 'age: 50, sex: 1, ..., thal: 3'."
    except Exception as e:
        return f"An unexpected error occurred during prediction: {e}"

# --- Helper Functions: To-Do Management ---

def _format_todos_for_response(user: CustomUser) -> str:
    """Formats a user's to-do list for display in chat."""
    todos = UserTodo.objects.filter(user=user).order_by('completed', 'due_date', '-created_at')
    if not todos:
        return "Your to-do list is empty! Want to add something? (e.g., 'Add todo: Meditate')"

    todo_list_text = "Here's your to-do list:\n"
    for i, todo in enumerate(todos):
        status = "[Done]" if todo.completed else "[Pending]"
        due_info = ""
        if todo.due_date:
            if todo.due_date == date.today():
                due_info = " (Due Today)"
            elif todo.due_date == date.today() + timedelta(days=1):
                due_info = " (Due Tomorrow)"
            else:
                due_info = f" (Due: {todo.due_date.strftime('%b %d')})"
        todo_list_text += f"{i+1}. {status} {todo.task_description}{due_info}\n"
    return todo_list_text

def _serialize_todos_for_json(user: CustomUser) -> list:
    """Serializes user todos for JSON response."""
    todos_queryset = UserTodo.objects.filter(user=user).order_by('completed', 'due_date', '-created_at')
    return [
        {
            'id': todo.id,
            'task_description': todo.task_description,
            'completed': todo.completed,
            'due_date': todo.due_date.isoformat() if todo.due_date else None
        } for todo in todos_queryset
    ]

def handle_todo_commands(request, message: str) -> str:
    """Processes user commands related to the to-do list."""
    user = request.user
    message_lower = message.lower()
    response_message = ""

    # Handle "yes/no" after an AI suggestion
    last_suggested_activity = request.session.get('last_suggested_activity')
    if message_lower == "yes" and last_suggested_activity:
        UserTodo.objects.create(
            user=user,
            task_description=last_suggested_activity,
            suggested_by_curo=True,
            due_date=date.today()
        )
        response_message = f"Added '{last_suggested_activity}' to your list for today! "
        del request.session['last_suggested_activity']
        response_message += "\n" + _format_todos_for_response(user)
        return response_message
    elif message_lower == "no" and last_suggested_activity:
        response_message = "Okay, no problem! Let me know if you change your mind."
        del request.session['last_suggested_activity']
        return response_message

    # Handle explicit To-Do Commands
    if message_lower.startswith("add todo:"):
        task_description = message_lower.replace("add todo:", "").strip()
        if task_description:
            due_date = date.today() + timedelta(days=1) # Default to tomorrow
            UserTodo.objects.create(
                user=user,
                task_description=task_description,
                suggested_by_curo=False,
                due_date=due_date
            )
            response_message = f"Okay, I've added '{task_description}' to your list!"
            response_message += "\n" + _format_todos_for_response(user)
        else:
            response_message = "Please tell me what to add. Example: 'Add todo: Meditate for 10 mins'."

    elif message_lower.startswith(("done todo:", "complete todo:")):
        identifier = message_lower.split(":", 1)[1].strip() if ":" in message_lower else ""
        todo_item = None
        try:
            todos = UserTodo.objects.filter(user=user, completed=False).order_by('due_date', '-created_at')
            todo_index = int(identifier) - 1
            if 0 <= todo_index < len(todos):
                todo_item = todos[todo_index]
        except (ValueError, IndexError):
            todo_item = UserTodo.objects.filter(
                user=user,
                task_description__icontains=identifier,
                completed=False
            ).first()

        if todo_item:
            todo_item.completed = True
            todo_item.completed_at = datetime.now()
            todo_item.save()
            response_message = f"Great job! You've completed: '{todo_item.task_description}'."
            response_message += "\n" + _format_todos_for_response(user)
        else:
            response_message = f"Couldn't find an incomplete task matching '{identifier}'. Try 'list todos' to see numbers."
    
    elif message_lower == "list todos" or message_lower == "my todos":
        response_message = _format_todos_for_response(user)
    
    elif message_lower == "clear todos":
        UserTodo.objects.filter(user=user, completed=True).delete()
        response_message = "Completed tasks have been cleared."
        response_message += "\n" + _format_todos_for_response(user)

    return response_message or "I didn't understand that to-do command. Try 'Add todo: [task]', 'Done todo: [task or number]', 'List todos', or 'Clear todos'."


# --- Django Views ---

@login_required
def chat_room(request):
    """Handles the main chat room logic, including AI interaction and to-do management."""
    # Fetch chat history for initial render or full page reload
    chat_history_list = list(ChatMessage.objects.filter(user=request.user).order_by('timestamp').values('message', 'bot_response', 'timestamp'))

    # Get/Set AI mode and disease type from session or POST
    ai_mode = request.POST.get('ai-mode', request.session.get('ai_mode', 'general'))
    disease_type = request.POST.get('disease-type', request.session.get('disease_type', 'diabetes'))
    request.session['ai_mode'] = ai_mode
    request.session['disease_type'] = disease_type

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        new_ai_mode = request.POST.get('ai-mode', '').strip()
        new_disease_type = request.POST.get('disease-type', '').strip()

        # Update mode if changed by user in form
        if new_ai_mode:
            ai_mode = new_ai_mode
            request.session['ai_mode'] = ai_mode
        if new_disease_type:
            disease_type = new_disease_type
            request.session['disease_type'] = disease_type

        bot_response = ""

        # Prioritize To-Do commands or session-based "yes/no"
        if message.lower().startswith(("add todo:", "done todo:", "complete todo:", "list todos", "my todos", "clear todos")) or \
           (message.lower() in ["yes", "no"] and request.session.get('last_suggested_activity')):
            bot_response = handle_todo_commands(request, message)
        else:
            # Handle general chat/AI modes
            greetings = ["hi", "hello", "hey", "greetings", "yo", "what's up", "howdy"]
            if message.lower() in greetings:
                bot_response = "Hey there! I’m Curo, your friendly health coach. Ask me about health or use the mode selector for specific help!"
            elif not message or len(message.split()) <= 2:
                bot_response = "Hey! I’m Curo, ready to help with your health questions. Try asking something specific or select a mode!"
            else:
                if ai_mode == "general":
                    bot_response = handle_general_health(message)
                elif ai_mode == "symptoms":
                    bot_response = handle_symptoms_predictor(message)
                elif ai_mode == "mental":
                    bot_response = handle_mental_health(message, request.user)
                elif ai_mode == "disease":
                    bot_response = handle_disease_predictor(message, disease_type)
                else:
                    bot_response = "Invalid mode selected. Please choose a valid mode."

        # Save current interaction
        ChatMessage.objects.create(
            user=request.user,
            message=message,
            bot_response=bot_response,
            timestamp=datetime.now()
        )

        # For AJAX requests, return JSON with updated todos
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            todos_data = _serialize_todos_for_json(request.user)
            return JsonResponse({'bot_response': bot_response, 'todos': todos_data})

        # For full page reloads, re-render the template
        active_todos_json_for_template = json.dumps(_serialize_todos_for_json(request.user))
        return render(request, 'chat.html', {
            'chat_history': chat_history_list,
            'ai_mode': ai_mode,
            'disease_type': disease_type,
            'active_todos': active_todos_json_for_template
        })

    # Initial GET request to load the chat page
    active_todos_json_for_template = json.dumps(_serialize_todos_for_json(request.user))
    return render(request, 'chat.html', {
        'chat_history': chat_history_list,
        'ai_mode': ai_mode,
        'disease_type': disease_type,
        'active_todos': active_todos_json_for_template
    })

@csrf_exempt # Consider making this POST-only with csrf_token in AJAX for better security
@login_required
def generate_health_report(request):
    """Generates a detailed health report using AI based on user-provided data."""
    if request.method == 'POST':
        try:
            data = request.POST
            age = data.get('age')
            gender = data.get('gender')
            height_cm = data.get('height_cm')
            weight_kg = data.get('weight_kg')
            exercise_frequency = data.get('exercise_frequency')
            diet_quality = data.get('diet_quality')
            smoking_status = data.get('smoking_status')
            alcohol_consumption = data.get('alcohol_consumption')

            # Prompt using the best version from previous conversation
            prompt = (
                "You are a highly skilled AI assistant specializing in health and wellness. "
                "Your task is to generate a comprehensive, yet concise, health report and "
                "provide actionable, practical recommendations based on the user's provided data. "
                "Prioritize clarity, accuracy, and a positive, encouraging tone. "
                "The report should be suitable for a general audience, without overly technical jargon. "
                "Aim for a total response length of approximately 200-300 words, structured with clear headings.\n\n"
                "--- User Health Data ---\n"
                f"Age: {age} years\n"
                f"Gender: {gender.capitalize()}\n"
                f"Height: {height_cm} cm\n"
                f"Weight: {weight_kg} kg\n"
                f"Exercise Frequency: {exercise_frequency.replace('_', ' ').title()}\n"
                f"Diet Quality: {diet_quality.capitalize()}\n"
                f"Smoking Status: {smoking_status.capitalize()}\n"
                f"Alcohol Consumption: {alcohol_consumption.capitalize()}\n\n"
                "--- Report Structure ---\n"
                "Please use the following section headings and content guidelines:\n"
                "**1. Overview:** A brief summary of the patient's general health profile, noting positive aspects and initial observations about height/weight relative to age.\n"
                "**2. Key Observations:** Elaborate on significant positive health habits and specific areas that warrant attention (e.g., low weight, specific lifestyle factors). Avoid making direct diagnoses.\n"
                "**3. Recommendations:** Provide 3-5 clear, actionable, and safe suggestions for improving or maintaining health. Focus on areas identified in 'Key Observations'. Ensure recommendations are general advice and not medical prescriptions.\n"
                "**4. Important Note:** Include a disclaimer that this report is for informational purposes only and not a substitute for professional medical advice.\n"
                "-----------------------\n"
                "Begin the health report now."
            )
            response_text = _generate_ai_content(prompt) 

            return JsonResponse({'status': 'success', 'report': response_text})

        except Exception as e:
            print(f"Error generating health report: {e}")
            return JsonResponse({'status': 'error', 'message': 'Failed to generate report.'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
def profile_view(request):
    """Handles user profile updates (email and password)."""
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            email = request.POST.get('email')
            password = request.POST.get('password')

            try:
                user = request.user
                if email and email != user.email:
                    if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                        return JsonResponse({'success': False, 'error': 'Email already in use.'})
                    user.email = email

                if password:
                    user.set_password(password)
                user.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return render(request, 'profile.html', {'user': request.user})

def signup_view(request):
    """Handles user registration."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'login.html', {
                'signup_errors': 'Email already exists. Try logging in or use a different email.'
            })

        user = CustomUser.objects.create_user(
            email=email,
            username=name, # Using name for username, adjust if your CustomUser handles this differently
            password=password,
            first_name=name # Storing name as first_name
        )
        user.save()
        login(request, user)
        return redirect('landing')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """Logs out the current user."""
    if request.method == 'POST':
        logout(request)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('login')
    return redirect('login') # Handles direct GET requests to logout (redirects to login)

def index_view(request):
    """Renders the main index page."""
    return render(request, 'index.html')

def landing_view(request):
    """Renders the landing page, redirects to login if not authenticated."""
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'landing.html')

def mark_todo_done(request, todo_id):
    # Your existing logic to mark todo as done
    if request.method == 'POST':
        try:
            # Get the Todo item
            todo = UserTodo.objects.get(id=todo_id)
            # Parse the JSON body
            import json
            data = json.loads(request.body)
            completed_status = data.get('completed')

            # Update the todo status
            todo.completed = completed_status
            todo.save()

            # Return all todos
            todos = list(UserTodo.objects.values()) # Get all todos, including the updated one
            return JsonResponse({'todos': todos})
        except UserTodo.DoesNotExist:
            return JsonResponse({'error': 'Todo not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def clear_completed_todos(request):
    # Your existing logic to clear completed todos
    if request.method == 'POST':
        try:
            UserTodo.objects.filter(completed=True).delete()
            todos = list(UserTodo.objects.values()) # Get remaining todos
            return JsonResponse({'todos': todos})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)