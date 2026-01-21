from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from .telegram import send_telegram_message
from .models import UserProfile

def task_list(request):
    tasks = Task.objects.all().order_by('due_date')
    return render(request, "tasks/task_list.html", {"tasks": tasks})


def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            # Send Telegram notification to the assignee
            try:
                user_profile = UserProfile.objects.get(user=task.assignee)
                chat_id = user_profile.telegram_chat_id
                message = f"""
📌 New Task Assigned !

Title: {task.title}
Priority: {task.priority.title()}
Due: {task.due_date}
                        """

                send_telegram_message(chat_id, message)
            except UserProfile.DoesNotExist:
                pass  # No Telegram chat ID available
            return redirect("/")
    else:
        form = TaskForm()

    return render(request, "tasks/create_task.html", {"form": form})
