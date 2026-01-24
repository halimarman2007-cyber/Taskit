from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from .telegram import send_telegram_message
from .models import UserProfile
from .models import Task, Scratchpad
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from django.contrib.auth.models import User

from django.utils.timezone import localdate
import calendar
from datetime import date

from django.utils.timezone import localdate
from datetime import date
import calendar

def task_list(request):
    user = User.objects.first()

    active_tasks = Task.objects.exclude(status="done").order_by("due_date")
    done_tasks = Task.objects.filter(status="done").order_by("-due_date")[:5]

    # 🔹 Determine month/year from query params
    today = localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    # Prevent invalid values
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Calendar data
    month_calendar = calendar.monthcalendar(year, month)

    calendar_tasks = Task.objects.filter(
        due_date__year=year,
        due_date__month=month
    ).exclude(status="done")

    # Navigation months
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    scratchpad, _ = Scratchpad.objects.get_or_create(user=user)

    return render(request, "tasks/task_list.html", {
        "active_tasks": active_tasks,
        "done_tasks": done_tasks,
        "scratchpad": scratchpad,
        "users": User.objects.all(),

        # calendar context
        "month_calendar": month_calendar,
        "calendar_tasks": calendar_tasks,
        "current_month": date(year, month, 1).strftime("%B %Y"),
        "today_day": today.day if (year == today.year and month == today.month) else None,

        # navigation
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
    })


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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_task_inline(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = request.POST.copy()

    # ✅ IMPORTANT: pass assignee ID directly (NOT User object)
    # Django ModelForm handles FK conversion
    data["assignee"] = data.get("assignee")
    data["status"] = data.get("status", "todo")

    form = TaskForm(data)

    if not form.is_valid():
        print("❌ FORM ERRORS:", form.errors)
        return JsonResponse(
            {"error": "Invalid form", "details": form.errors},
            status=400
        )

    task = form.save()

    # ✅ Telegram notification
    try:
        user_profile = UserProfile.objects.get(user=task.assignee)
        chat_id = user_profile.telegram_chat_id

        message = f"""
📌 New Task Assigned!

Title: {task.title}
Priority: {task.priority.title()}
Due: {task.due_date}
        """

        send_telegram_message(chat_id, message)

    except UserProfile.DoesNotExist:
        print("⚠️ No Telegram chat ID for user")

    return JsonResponse({
        "status": "created",
        "task_id": task.id
    })






