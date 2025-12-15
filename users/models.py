from django.db import models # type: ignore
from django.contrib.auth.models import AbstractUser, Group, Permission # type: ignore
# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('normal', "Normal User"),
        ('transitor', "Transitor"),
        ('tax_worker', "Tax Worker"),
        ('instructor', "Instructor")
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)  
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True
    )

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['username']  

    def __str__(self):
        return f'username:{self.username} ({self.email})'
    
class TransitorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete = models.CASCADE)
    transitor_license = models.ImageField(upload_to = 'licenses/')
    photo = models.ImageField(upload_to = 'profiles/', blank = True, null = True)
    job_title = models.CharField(max_length = 60)
    business_card = models.FileField(upload_to='business_cards/' )
    company_id_card = models.FileField(upload_to='company_ids/', blank = True, null = True)
    tin_vat_number = models.CharField(max_length=50)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    earning = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Transitor: {self.user.username}"



class InstructorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    certificate = models.FileField(upload_to='certificates/')
    course_material = models.FileField(upload_to='course_materials/', blank=True, null=True) 
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    job_title = models.CharField(max_length=100)
    course_title = models.CharField(max_length=100)

    def __str__(self):
        return f"Instructor: {self.user.username}"





class TaxWorkerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=100)
    work_email = models.EmailField()
    photo = models.ImageField(upload_to = 'profiles/', blank = True, null = True)
    company_id_card = models.FileField(upload_to='company_ids/', blank=True, null=True)
    phone_number = models.CharField(max_length = 20, blank = True, null = True)
    clients_served = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    earning = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    organization_name = models.CharField(max_length=10)
    years_of_experience = models.IntegerField(default = 0)

    def __str__(self):
        return f"Taxworker: {self.user.username}"



class Message(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("pending", "Pending"),
        ("read", "Read"),
    ]

    sender = models.ForeignKey(
        CustomUser,
        related_name="messages_sent",
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        CustomUser,
        related_name="messages_received",
        on_delete=models.CASCADE
    )
    content = models.TextField(blank = False)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.email} → {self.receiver.email}"


class TaxWorkerQuestion(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="asked_questions")
    tax_worker = models.ForeignKey(TaxWorkerProfile, on_delete=models.CASCADE, related_name="received_questions")
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("answered", "Answered")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="receipts/")  
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2,default = 0.00)  

    def __str__(self):
        return f"{self.sender.email} → {self.tax_worker.user.email}"


class TransitorRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_requests")
    transitor = models.ForeignKey(TransitorProfile, on_delete=models.CASCADE, related_name="received_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="receipts/")  
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00)  

    def __str__(self):
        return f"{self.user.email} → {self.transitor.user.email} ({self.status})"



class InstructorCoursePurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="courses_bought")
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE, related_name="students")
    receipt = models.FileField(upload_to="receipts/")
    created_at = models.DateTimeField(auto_now_add=True)





class TaxWorkerRating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tax_worker = models.ForeignKey(TaxWorkerProfile, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField() 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tax_worker") 

    def __str__(self):
        return f"{self.user.email} rated {self.tax_worker.user.email}: {self.rating}"




class TransitorRating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    transitor = models.ForeignKey(TransitorProfile, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "transitor")  

    def __str__(self):
        return f"{self.user.email} rated {self.transitor.user.email}: {self.rating}"




class InstructorRating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "instructor") 

    def __str__(self):
        return f"{self.user.email} rated {self.instructor.user.email}: {self.rating}"


class StoreItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to="store_items/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="cart_items")
    item = models.ForeignKey(StoreItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "item")  

    def __str__(self):
        return f"{self.user.email} - {self.item.name}"


class StorePurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="store_purchases")
    item = models.ForeignKey(StoreItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    receipt = models.FileField(upload_to="receipts/")
    delivery_location = models.CharField(max_length=255, blank=True, null=True)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} purchased {self.item.name}"


class AIProduct(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class AIAccessPurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ai_product = models.ForeignKey(AIProduct, on_delete=models.CASCADE)
    receipt = models.FileField(upload_to="ai_receipts/")
    purchased_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"AI Access for {self.user.email} at {self.purchased_at}"
    

class LawAuthority(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50) 
    year = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    

class CommunityQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="community_questions")
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    


class CommunityAnswer(models.Model):
    question = models.ForeignKey(
        CommunityQuestion,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user.username}"
    
class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    answer = models.TextField(blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return self.subject

