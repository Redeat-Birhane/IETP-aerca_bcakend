from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path("signup/", views.signup_view, name = "signup"),
    path("login/", views.login_view, name = "login"),
    path("profile/", views.profile, name = "profile"),
    path("logout/", views.logout_view, name = "logout"),
    path("send/", views.send_message),
    path("inbox/", views.inbox),
    path("sent/", views.sent_messages),
    path("tax_workers/", views.list_tax_workers),
    path("ask/", views.ask_tax_worker, name="ask-tax-worker"),
    path("answer/", views.answer_question, name="answer_question"),
    path("rate_tax_worker/", views.rate_tax_worker, name="rate_tax_worker"),
    path("transitors/", views.list_transitors),
    path("send_transitor_request/", views.send_transitor_request),
    path("respond_to_transitor_request/", views.respond_to_transitor_request),
    path("rate_transitor/", views.rate_transitor, name="rate_transitor"),
    path("instructors/", views.list_instructors),
    path("buy_course/", views.buy_course),
    path("rate_instructor/", views.rate_instructor, name="rate_instructor"),
    path("items/", views.list_store_items, name="list_store_items"),
    path("add/", views.add_to_cart, name="add_to_cart"),
    path("view/", views.view_cart, name="view_cart"),
    path("remove/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout_cart, name="checkout_cart"),
    path("buy_ai_access/", views.buy_ai_access, name="buy_ai_access"),
    path("ask_ai/", views.ask_ai_question, name="ask_ai"),
    path("laws/", views.list_laws, name="list_laws"),
    path("ask_community_question/", views.ask_community_question, name="ask_community_question"),
    path("answer_community_question/<int:question_id>", views.answer_community_question, name="answer_community_question"),
    path("ask_support/", views.create_support_ticket, name="ask_support"),
    path("view_support/", views.my_support_tickets, name="view_support"),
    path("view_community_questions/", views.list_community_questions, name="view_questions"),
    path("search/", views.search, name="search")



   
   


]