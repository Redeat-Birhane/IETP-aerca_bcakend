from datetime import timedelta, timezone
from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore

from users import models
from users.models import AIAccessPurchase, AIProduct, CartItem, CommunityAnswer, CommunityQuestion, CustomUser, InstructorCoursePurchase, InstructorProfile, InstructorRating, LawAuthority, Message, StoreItem, StorePurchase, SupportTicket, TaxWorkerQuestion, TaxWorkerProfile, TaxWorkerRating, TransitorProfile, TransitorRating, TransitorRequest  # type: ignore
from .forms import BaseSignupForm, TransitorSignupForm, InstructorSignupForm, TaxWorkerSignupForm
from django.http import JsonResponse # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
import json
from django.db.models import Avg # type: ignore
from django.http import HttpResponse # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from decimal import Decimal
from django.utils import timezone # type: ignore
from datetime import timedelta

@csrf_exempt
def signup_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

   
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        files = {} 
    else:
        data = request.POST
        files = request.FILES if request.FILES else {}

    role = data.get("role")
    role_form_map = {
        "transitor": TransitorSignupForm,
        "instructor": InstructorSignupForm,
        "tax_worker": TaxWorkerSignupForm,
        "normal": BaseSignupForm
    }
    FormClass = role_form_map.get(role, BaseSignupForm)

    form = FormClass(data, files)  

    if form.is_valid():
        user = form.save()
        if user.role == "tax_worker":
            TaxWorkerProfile.objects.create(
                user=user,
                job_title=form.cleaned_data.get("job_title"),
                work_email=form.cleaned_data.get("work_email"),
                organization_name=form.cleaned_data.get("organization_name"),
                phone_number=form.cleaned_data.get("phone_number"),
                years_of_experience=form.cleaned_data.get("years_of_experience"),
                photo=form.cleaned_data.get("photo")
            )

        elif user.role == "transitor":
            TransitorProfile.objects.create(
                user=user,
                transitor_license=form.cleaned_data.get("transitor_license"),
                job_title=form.cleaned_data.get("job_title"),
                business_card=form.cleaned_data.get("business_card"),
                company_id_card=form.cleaned_data.get("company_id_card"),
                tin_vat_number=form.cleaned_data.get("tin_vat_number"),
                photo=form.cleaned_data.get("photo")
            )

        elif user.role == "instructor":
            InstructorProfile.objects.create(
        user=user,
        certificate=form.cleaned_data.get("certificate"),
        course_material=form.cleaned_data.get("course_material"),  # handle optional PDF
        job_title=form.cleaned_data.get("job_title"),
        course_title=form.cleaned_data.get("course_title"),
        years_of_experience=form.cleaned_data.get("years_of_experience"),
        photo=form.cleaned_data.get("photo")
    )
        login(request, user, backend='users.backends.EmailBackend')
        return JsonResponse({
            "message": "Signup successful",
            "role": user.role,
            "photo": user.photo.url if user.photo else None
        }, status=201)

    return JsonResponse({"errors": form.errors}, status=400)




@csrf_exempt
def profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Authentication required",
            "authenticated": False
        }, status=401)
    user = request.user
    data = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "photo": user.photo.url if user.photo else None
    }

    sent_questions = [
        {
            "receiver_email": q.tax_worker.user.email,
            "question": q.question,
            "answer": q.answer,
            "status": q.status,
            "created_at": q.created_at
        }
        for q in user.asked_questions.all().order_by("-created_at")
    ]

    received_questions = []
    if hasattr(user, 'taxworkerprofile'):
        profile = user.taxworkerprofile
        received_questions = [
            {
                "asker_email": q.sender.email,
                "question": q.question,
                "answer": q.answer,
                "status": q.status,
                "created_at": q.created_at
            }
            for q in profile.received_questions.all().order_by("-created_at")
        ]
        data.update({
            "job_title": profile.job_title,
            "work_email": profile.work_email,
            "phone_number": profile.phone_number,
            "clients_served": profile.clients_served,
            "rating": str(profile.rating),
            "earning": str(profile.earning),
            "organization_name": profile.organization_name,
            "transitor_license": profile.transitor_license.url if hasattr(profile, 'transitor_license') and profile.transitor_license else None
        })

   
    sent_requests = [
        {
            "transitor_email": req.transitor.user.email,
            "status": req.status,
            "connected": req.status == "accepted",
            "created_at": req.created_at
        }
        for req in user.sent_requests.all().order_by("-created_at")
    ]

    received_requests = []
    if hasattr(user, 'transitorprofile'):
        profile = user.transitorprofile
        received_requests = [
            {
                "user_email": req.user.email,
                "status": req.status,
                "connected": req.status == "accepted",
                "created_at": req.created_at
            }
            for req in profile.received_requests.all().order_by("-created_at")
        ]
        data.update({
            "job_title": profile.job_title,
            "photo": profile.photo.url if profile.photo else None,
            "rating": str(profile.rating),
            "earning": str(profile.earning),
            "transitor_license": profile.transitor_license.url if profile.transitor_license else None,
            "business_card": profile.business_card.url if profile.business_card else None,
            "company_id_card": profile.company_id_card.url if profile.company_id_card else None,
            "tin_vat_number": profile.tin_vat_number,
        })

    if hasattr(user, 'instructorprofile'):
        profile = user.instructorprofile
        data.update({
            "job_title": profile.job_title,
            "course_title": profile.course_title,
            "years_of_experience": profile.years_of_experience,
            "photo": profile.photo.url if profile.photo else None,
            "course_material": profile.course_material.url if profile.course_material else None,
            "rating": str(profile.rating) if profile.rating is not None else None
        })

    purchased_courses = []
    if user.role != 'instructor':
        purchased_courses = [
            {
                "instructor_email": c.instructor.user.email,
                "course_title": c.instructor.course_title,
                "receipt_url": c.receipt.url,
                "created_at": c.created_at
            }
            for c in InstructorCoursePurchase.objects.filter(user=user).order_by("-created_at")
        ]

    store_purchases = [
        {
            "item_name": p.item.name,
            "description": p.item.description,
            "price": str(p.item.price),
            "quantity": p.quantity,
            "photo": p.item.photo.url if p.item.photo else None,
            "delivery_location": p.delivery_location,
            "receipt_url": p.receipt.url,
            "purchased_at": p.purchased_at
        }
        for p in StorePurchase.objects.filter(user=user).order_by("-purchased_at")
    ]

   
    ai_purchases = [
        {
            "id": p.id,
            "ai_product_name": p.ai_product.name,
            "price": str(p.ai_product.price),
            "receipt_url": p.receipt.url,
            "purchased_at": p.purchased_at
        }
        for p in AIAccessPurchase.objects.filter(user=user).order_by("-purchased_at")
    ]


    data.update({
        "sent_questions": sent_questions,
        "received_questions": received_questions,
        "sent_requests": sent_requests,
        "received_requests": received_requests,
        "purchased_courses": purchased_courses,
        "purchased_items": store_purchases,
        "ai_purchases": ai_purchases
    })

    return JsonResponse(data)






def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user = authenticate(request, email=email, password=password)
    if user:
        login(request, user)
        return JsonResponse({"message": "Login successful", "role": user.role})
    return JsonResponse({"message": "Invalid Credentials"}, status=401)

@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logout successful"})


@csrf_exempt
@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        receiver_email = data.get("receiver_email")
        content = data.get("content")
        
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not receiver_email:
        return JsonResponse({"error": "receiver_email is required"}, status=400)

    if not content or not content.strip():
        return JsonResponse(
            {"error": "Message content cannot be empty"},
            status=400
        )
    try:
        receiver = CustomUser.objects.get(email=receiver_email) # type: ignore
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Receiver not found"}, status=404)

    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content
    )

    return JsonResponse({
        "message": "Message sent",
        "data": {
            "id": message.id,
            "receiver": receiver.email,
            "status": message.status,
            "created_at": message.created_at
        }
    }, status=201)


@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by("-created_at")

    data = [
        {
            "id": m.id,
            "sender": m.sender.email,
            "content": m.content,
            "status": m.status,
            "created_at": m.created_at
        }
        for m in messages
    ]

    return JsonResponse({"messages": data})


@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by("-created_at")

    data = [
        {
            "id": m.id,
            "receiver": m.receiver.email,
            "content": m.content,
            "status": m.status,
            "created_at": m.created_at
        }
        for m in messages
    ]

    return JsonResponse({"messages": data})


@login_required
def list_tax_workers(request):
    tax_workers = TaxWorkerProfile.objects.select_related("user") # type: ignore

    data = []
    for profile in tax_workers:
        data.append({
            "id": profile.id,
            "user_id": profile.user.id,
            "username": profile.user.username,
            "email": profile.user.email,
            "job_title": profile.job_title,
            "organization_name": profile.organization_name,
            "work_email": profile.work_email,
            "phone_number": profile.phone_number,
            "photo": profile.photo.url if profile.photo else None,
            "clients_served": profile.clients_served,
            "rating": str(profile.rating),
            "years_of_experience": profile.years_of_experience,
        })

    return JsonResponse({"tax_workers": data})

def create_missing_profiles():
    tax_workers = CustomUser.objects.filter(role="tax_worker").exclude(taxworkerprofile__isnull=False)
    for user in tax_workers:
        TaxWorkerProfile.objects.create(
            user=user,
            job_title="Default Job Title",
            work_email=user.email,
            organization_name="Default Org",
            phone_number="",
            years_of_experience=0
        )

  
    transitors = CustomUser.objects.filter(role="transitor").exclude(transitorprofile__isnull=False)
    for user in transitors:
        TransitorProfile.objects.create(
            user=user,
            transitor_license=None,
            job_title="Default Job Title",
            business_card=None,
            company_id_card=None,
            tin_vat_number="N/A"
        )

    instructors = CustomUser.objects.filter(role="instructor").exclude(instructorprofile__isnull=False)
    for user in instructors:
        InstructorProfile.objects.create(
            user=user,
            certificate=None,
            job_title="Default Job Title",
            course_title="Default Course",
            years_of_experience=0
        )

FIXED_PAYMENT_AMOUNT = Decimal("50.00") 


@csrf_exempt
@login_required
def ask_tax_worker(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = request.POST
        tax_worker_email = data.get("tax_worker_email")
        question_text = data.get("question")
        receipt = request.FILES.get("receipt")
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not tax_worker_email or not question_text:
        return JsonResponse({"error": "tax_worker_email and question are required"}, status=400)
    
    if not receipt:
        return JsonResponse({"error": "Payment receipt is required"}, status=400)

    try:
        tax_worker_user = CustomUser.objects.get(email=tax_worker_email, role="tax_worker")
        tax_worker_profile = tax_worker_user.taxworkerprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Tax worker not found"}, status=404)

    question = TaxWorkerQuestion.objects.create(
        sender=request.user,
        tax_worker=tax_worker_profile,
        question=question_text,
        receipt=receipt,
        payment_amount=FIXED_PAYMENT_AMOUNT
    )

    tax_worker_profile.clients_served += 1
    tax_worker_profile.earning += FIXED_PAYMENT_AMOUNT
    tax_worker_profile.save()

    return JsonResponse({
        "message": "Question asked successfully",
        "question": {
            "asker_email": request.user.email,
            "tax_worker_email": tax_worker_user.email,
            "question": question.question,
            "status": question.status,
            "answer": question.answer,
            "created_at": question.created_at,
            "receipt_url": question.receipt.url,
            "payment_amount": str(question.payment_amount)
        }
    }, status=201)



@csrf_exempt
@login_required
def answer_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    if request.user.role != "tax_worker":
        return JsonResponse({"error": "Only tax workers can answer questions"}, status=403)

    try:
        data = json.loads(request.body)
        asker_email = data.get("asker_email")
        answer_text = data.get("answer")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not asker_email or not answer_text:
        return JsonResponse({"error": "asker_email and answer are required"}, status=400)

    try:
        asker = CustomUser.objects.get(email=asker_email)
        question = TaxWorkerQuestion.objects.filter(
            sender=asker,
            tax_worker=request.user.taxworkerprofile,
            status="pending"
        ).latest("created_at")
    except (CustomUser.DoesNotExist, TaxWorkerQuestion.DoesNotExist):
        return JsonResponse({"error": "Pending question not found for this user"}, status=404)


    question.answer = answer_text
    question.status = "answered"
    question.save()

    return JsonResponse({
        "message": "Question answered successfully",
        "question": {
            "asker_email": question.sender.email,
            "tax_worker_email": request.user.email,
            "question": question.question,
            "answer": question.answer,
            "status": question.status,
            "created_at": question.created_at
        }
    }, status=200)




@login_required
def list_transitors(request):
    transitors = TransitorProfile.objects.select_related("user")
    data = []
    for t in transitors:
        try:
            req = TransitorRequest.objects.get(user=request.user, transitor=t)
            status = req.status
        except TransitorRequest.DoesNotExist:
            status = None

        data.append({
            "username": t.user.username,
            "email": t.user.email,
            "job_title": t.job_title,
            "photo": t.photo.url if t.photo else None,
            "status": status,
            "rating": str(t.rating) if t.rating is not None else None
        })
    return JsonResponse({"transitors": data})




@csrf_exempt
@login_required
def send_transitor_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = request.POST
        transitor_email = data.get("transitor_email")
        receipt = request.FILES.get("receipt")
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not transitor_email:
        return JsonResponse({"error": "transitor_email is required"}, status=400)
    
    if not receipt:
        return JsonResponse({"error": "Payment receipt is required"}, status=400)

    try:
        transitor_user = CustomUser.objects.get(email=transitor_email, role="transitor")
        transitor_profile = transitor_user.transitorprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Transitor not found"}, status=404)

    req, created = TransitorRequest.objects.get_or_create(
        user=request.user,
        transitor=transitor_profile,
        defaults={
            "status": "pending",
            "receipt": receipt,
            "payment_amount": FIXED_PAYMENT_AMOUNT
        }
    )

    if not created:
        return JsonResponse({"message": f"Request already {req.status}"}, status=400)

  
    transitor_profile.earning += FIXED_PAYMENT_AMOUNT
    transitor_profile.save()

    return JsonResponse({
        "message": "Request sent successfully",
        "request": {
            "user_email": request.user.email,
            "transitor_email": transitor_user.email,
            "status": req.status,
            "created_at": req.created_at,
            "receipt_url": req.receipt.url,
            "payment_amount": str(req.payment_amount)
        }
    }, status=201)






@login_required
def list_instructors(request):
    instructors = InstructorProfile.objects.select_related("user")
    data = []
    for ins in instructors:
        purchased = InstructorCoursePurchase.objects.filter(user=request.user, instructor=ins).exists()
        data.append({
             "username": ins.user.username,
            "email": ins.user.email,
            "job_title": ins.job_title,
            "course_title": ins.course_title,
            "years_of_experience": ins.years_of_experience,
            "rating": str(ins.rating) if ins.rating is not None else None,
            "photo": ins.photo.url if ins.photo else None,
            "course_material": ins.course_material.url if ins.course_material else None
        })
    return JsonResponse({"instructors": data})



@csrf_exempt
@login_required
def buy_course(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = request.POST
    receipt = request.FILES.get("receipt") 

    instructor_email = data.get("instructor_email")
    if not instructor_email or not receipt:
        return JsonResponse({"error": "instructor_email and receipt are required"}, status=400)

    try:
        instructor_user = CustomUser.objects.get(email=instructor_email, role="instructor")
        instructor_profile = instructor_user.instructorprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Instructor not found"}, status=404)

    purchase = InstructorCoursePurchase.objects.create(
        user=request.user,
        instructor=instructor_profile,
        receipt=receipt
    )

    return JsonResponse({"message": "Course purchased successfully"})



@csrf_exempt
@login_required
def rate_tax_worker(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        tax_worker_email = data.get("tax_worker_email")
        rating_value = int(data.get("rating"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON or rating"}, status=400)

    if rating_value < 1 or rating_value > 5:
        return JsonResponse({"error": "Rating must be between 1 and 5"}, status=400)

   
    try:
        tax_worker_user = CustomUser.objects.get(email=tax_worker_email, role="tax_worker")
        tax_worker_profile = tax_worker_user.taxworkerprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Tax Worker not found"}, status=404)

    answered_questions = TaxWorkerQuestion.objects.filter(
        sender=request.user,
        tax_worker=tax_worker_profile,
        status="answered"
    )
    if not answered_questions.exists():
        return JsonResponse({"error": "You can only rate after having an answered question"}, status=403)

   
    rating_obj, created = TaxWorkerRating.objects.update_or_create(
        user=request.user,
        tax_worker=tax_worker_profile,
        defaults={"rating": rating_value}
    )

 
    avg_rating = TaxWorkerRating.objects.filter(tax_worker=tax_worker_profile).aggregate(rating_avg=Avg('rating'))['rating_avg']
    tax_worker_profile.rating = avg_rating
    tax_worker_profile.save()

    return JsonResponse({
        "message": "Tax Worker rated successfully",
        "average_rating": str(avg_rating)
    }, status=200)





@csrf_exempt
@login_required
def rate_instructor(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        instructor_email = data.get("instructor_email")
        rating_value = int(data.get("rating"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON or rating"}, status=400)

    if rating_value < 1 or rating_value > 5:
        return JsonResponse({"error": "Rating must be between 1 and 5"}, status=400)

  
    try:
        instructor_user = CustomUser.objects.get(email=instructor_email, role="instructor")
        instructor_profile = instructor_user.instructorprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Instructor not found"}, status=404)

   
    if not InstructorCoursePurchase.objects.filter(user=request.user, instructor=instructor_profile).exists():
        return JsonResponse({"error": "You can only rate an instructor after purchasing their course"}, status=403)

    rating_obj, created = InstructorRating.objects.update_or_create(
        user=request.user,
        instructor=instructor_profile,
        defaults={"rating": rating_value}
    )


    avg_rating = InstructorRating.objects.filter(instructor=instructor_profile).aggregate(Avg('rating'))['rating__avg']
    instructor_profile.rating = avg_rating
    instructor_profile.save()

    return JsonResponse({
        "message": "Instructor rated successfully",
        "average_rating": str(avg_rating)
    }, status=200)


@csrf_exempt
@login_required
def rate_transitor(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        transitor_email = data.get("transitor_email")
        rating_value = int(data.get("rating"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON or rating"}, status=400)

    if rating_value < 1 or rating_value > 5:
        return JsonResponse({"error": "Rating must be between 1 and 5"}, status=400)


    try:
        transitor_user = CustomUser.objects.get(email=transitor_email, role="transitor")
        transitor_profile = transitor_user.transitorprofile
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Transitor not found"}, status=404)


    try:
        request_obj = TransitorRequest.objects.get(user=request.user, transitor=transitor_profile, status="accepted")
    except TransitorRequest.DoesNotExist:
        return JsonResponse({"error": "You can only rate a Transitor after your request has been accepted"}, status=403)

  
    rating_obj, created = TransitorRating.objects.update_or_create(
        user=request.user,
        transitor=transitor_profile,
        defaults={"rating": rating_value}
    )

   
    avg_rating = TransitorRating.objects.filter(transitor=transitor_profile).aggregate(Avg('rating'))['rating__avg']
    transitor_profile.rating = avg_rating
    transitor_profile.save()

    return JsonResponse({
        "message": "Transitor rated successfully",
        "average_rating": str(avg_rating)
    }, status=200)




@csrf_exempt
@login_required
def respond_to_transitor_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    if request.user.role != "transitor":
        return JsonResponse({"error": "Only transitors can respond to requests"}, status=403)

    try:
        data = json.loads(request.body)
        user_email = data.get("user_email")
        action = data.get("action")  
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if action not in ["accept", "reject"]:
        return JsonResponse({"error": "Invalid action"}, status=400)

    try:
        user = CustomUser.objects.get(email=user_email)
        transitor_profile = request.user.transitorprofile
        req = TransitorRequest.objects.get(
            user=user,
            transitor=transitor_profile,
            status="pending"
        )
    except (CustomUser.DoesNotExist, TransitorRequest.DoesNotExist):
        return JsonResponse({"error": "Pending request not found"}, status=404)

    req.status = "accepted" if action == "accept" else "rejected"
    req.save()

    return JsonResponse({
        "message": f"Request {req.status} successfully",
        "request": {
            "user_email": user.email,
            "transitor_email": request.user.email,
            "status": req.status
        }
    })



@csrf_exempt
@login_required
def list_store_items(request):
    items = StoreItem.objects.all()
    data = [
        {
            "id": i.id,
            "name": i.name,
            "description": i.description,
            "price": str(i.price),
            "photo": i.photo.url if i.photo else None,
            "location": i.location
        }
        for i in items
    ]
    return JsonResponse({"store_items": data})


@csrf_exempt
@login_required
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        item_id = data.get("item_id")
        quantity = int(data.get("quantity", 1))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        item = StoreItem.objects.get(id=item_id)
    except StoreItem.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)

    cart_item, created = CartItem.objects.get_or_create(user=request.user, item=item)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    return JsonResponse({"message": "Item added to cart", "quantity": cart_item.quantity})


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    data = [
        {
            "id": c.id,
            "item_id": c.item.id,
            "name": c.item.name,
            "price": str(c.item.price),
            "quantity": c.quantity,
            "photo": c.item.photo.url if c.item.photo else None
        }
        for c in cart_items
    ]
    return JsonResponse({"cart_items": data})


@csrf_exempt
@login_required
def remove_from_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
        cart_item.delete()
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Cart item not found"}, status=404)

    return JsonResponse({"message": "Item removed from cart"})


@csrf_exempt
@login_required
def checkout_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        receipt = request.FILES.get("receipt")
        delivery_location = request.POST.get("delivery_location", "")
    except Exception:
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not receipt:
        return JsonResponse({"error": "Payment receipt is required"}, status=400)

    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    for ci in cart_items:
        StorePurchase.objects.create(
            user=request.user,
            item=ci.item,
            quantity=ci.quantity,
            receipt=receipt,
            delivery_location=delivery_location
        )
        ci.delete() 

    return JsonResponse({"message": "Cart checked out successfully"})



@csrf_exempt
@login_required
def buy_ai_access(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    receipt = request.FILES.get("receipt")
    ai_product_id = request.POST.get("ai_product_id") 
    if not receipt or not ai_product_id:
        return JsonResponse({"error": "AI product and receipt are required"}, status=400)

    try:
        ai_product = AIProduct.objects.get(id=ai_product_id)
    except AIProduct.DoesNotExist:
        return JsonResponse({"error": "AI product not found"}, status=404)

    purchase = AIAccessPurchase.objects.create(
        user=request.user,
        ai_product=ai_product,
        receipt=receipt
    )

    return JsonResponse({
        "message": f"AI Assistant '{ai_product.name}' access purchased successfully",
        "purchase_id": purchase.id,
        "ai_product": ai_product.name,
        "price": str(ai_product.price),
        "purchased_at": purchase.purchased_at
    }, status=201)



@csrf_exempt
@login_required
def ask_ai_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        question_text = data.get("question")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not question_text or not question_text.strip():
        return JsonResponse({"error": "Question cannot be empty"}, status=400)

    
    has_access = AIAccessPurchase.objects.filter(user=request.user).exists()
    if not has_access:
        return JsonResponse({"error": "You need to purchase AI access first"}, status=403)


    return JsonResponse({
        "message": "AI question feature is not available yet. You have successfully purchased access."
    }, status=200)



def list_laws(request):
    laws = LawAuthority.objects.all()

    year = request.GET.get("year")
    show_new = request.GET.get("new")

  
    if year:
        laws = laws.filter(year=year)


    if show_new == "true":
        one_month_ago = timezone.now() - timedelta(days=30)
        laws = laws.filter(created_at__gte=one_month_ago)

    return JsonResponse({
        "laws": [
            {
                "id": law.id,
                "name": law.name,
                "description": law.description,
                "category": law.category,
                "year": law.year,
                "created_at": law.created_at
            }
            for law in laws
        ]
    })



def list_community_questions(request):
    questions = CommunityQuestion.objects.all().order_by("-created_at")

    return JsonResponse({
        "questions": [
            {
                "id": q.id,
                "title": q.title,
                "body": q.body,
                "asked_by": q.user.username,
                "created_at": q.created_at,
                "answers": [
                    {
                        "id": a.id,
                        "body": a.body,
                        "answered_by": a.user.username,
                        "created_at": a.created_at
                    }
                    for a in q.answers.all()
                ]
            }
            for q in questions
        ]
    })



@csrf_exempt
@login_required
def ask_community_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)

    question = CommunityQuestion.objects.create(
        user=request.user,
        title=data.get("title"),
        body=data.get("body")
    )

    return JsonResponse({
        "message": "Question posted successfully",
        "question_id": question.id
    }, status=201)


@csrf_exempt
@login_required
def answer_community_question(request, question_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)

    question = CommunityQuestion.objects.get(id=question_id)

    CommunityAnswer.objects.create(
        question=question,
        user=request.user,
        body=data.get("body")
    )

    return JsonResponse({
        "message": "Answer submitted successfully"
    }, status=201)


@csrf_exempt
@login_required
def create_support_ticket(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)

    ticket = SupportTicket.objects.create(
        user=request.user,
        subject=data.get("subject"),
        message=data.get("message")
    )

    return JsonResponse({
        "message": "Support ticket submitted successfully",
        "ticket_id": ticket.id,
        "status": ticket.status
    }, status=201)


@login_required
def my_support_tickets(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at")

    return JsonResponse({
        "tickets": [
            {
                "id": t.id,
                "subject": t.subject,
                "message": t.message,
                "status": t.status,
                "answer": t.answer,  
                "created_at": t.created_at,
                "answered_at": t.answered_at 
            }
            for t in tickets
        ]
    })


@login_required
def search(request):
    category = request.GET.get("category")
    query = request.GET.get("query", "")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    results = []

    if category == "instructors":
        instructors = InstructorProfile.objects.filter(job_title__icontains=query)
        results = [
            {
                "username": ins.user.username,
                "email": ins.user.email,
                "job_title": ins.job_title,
                "course_title": ins.course_title,
                "years_of_experience": ins.years_of_experience,
                "rating": str(ins.rating) if ins.rating else None,
                "photo": ins.photo.url if ins.photo else None,
                "course_material": ins.course_material.url if ins.course_material else None
            }
            for ins in instructors
        ]

    elif category == "tax_workers":
        tax_workers = TaxWorkerProfile.objects.filter(job_title__icontains=query)
        results = [
            {
                "username": tw.user.username,
                "email": tw.user.email,
                "job_title": tw.job_title,
                "organization_name": tw.organization_name,
                "work_email": tw.work_email,
                "phone_number": tw.phone_number,
                "photo": tw.photo.url if tw.photo else None,
                "clients_served": tw.clients_served,
                "rating": str(tw.rating) if tw.rating else None,
                "years_of_experience": tw.years_of_experience
            }
            for tw in tax_workers
        ]

    elif category == "transitors":
        transitors = TransitorProfile.objects.filter(job_title__icontains=query)
        results = [
            {
                "username": t.user.username,
                "email": t.user.email,
                "job_title": t.job_title,
                "photo": t.photo.url if t.photo else None,
                "rating": str(t.rating) if t.rating else None
            }
            for t in transitors
        ]

    elif category == "store":
        items = StoreItem.objects.all()
        if min_price:
            items = items.filter(price__gte=min_price)
        if max_price:
            items = items.filter(price__lte=max_price)
        results = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": str(item.price),
                "photo": item.photo.url if item.photo else None,
                "location": item.location
            }
            for item in items
        ]

    else:
        return JsonResponse({"error": "Invalid category"}, status=400)

    return JsonResponse({"results": results})

