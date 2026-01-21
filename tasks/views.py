from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from .telegram import send_telegram_message
from .models import UserProfile
from .models import Task, Scratchpad
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

def task_list(request):
    user = User.objects.first()

    active_tasks = Task.objects.exclude(status="done").order_by("due_date")
    done_tasks = (
        Task.objects
        .filter(status="done")
        .order_by("-due_date", "-created_at")[:5]
    )


    scratchpad, _ = Scratchpad.objects.get_or_create(user=user)

    return render(
        request,
        "tasks/task_list.html",
        {
            "active_tasks": active_tasks,
            "done_tasks": done_tasks,
            "scratchpad": scratchpad,
        }
    )


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
@csrf_exempt
def save_scratchpad(request):
    if request.method == "POST":
        scratchpad, _ = Scratchpad.objects.get_or_create(user=request.user)
        scratchpad.content = request.POST.get("content", "")
        scratchpad.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)





from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from datetime import datetime

@csrf_exempt
def update_task_field(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    task = get_object_or_404(Task, id=task_id)

    field = request.POST.get("field")
    value = request.POST.get("value")

    try:
        if field == "title":
            task.title = value

        elif field == "description":
            task.description = value

        elif field == "status":
            print("status update requested:", value)
            if value in ["todo", "in_progress", "done"]:
                task.status = value
                print("STATUS UPDATED TO:", task.status)
            else:
                print("INVALID STATUS VALUE:", value)
                return JsonResponse({"error": "Invalid status value"}, status=400)


        elif field == "priority":
            if value in ["low", "medium", "high"]:
                task.priority = value

        elif field == "due_date":
            task.due_date = datetime.strptime(value, "%Y-%m-%d").date()

        elif field == "assignee_id":
            task.assignee_id = int(value)

        else:
            return JsonResponse({"error": "Invalid field"}, status=400)
        print("UPDATING TASK:", task.id, field, value)

        task.save()
        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
