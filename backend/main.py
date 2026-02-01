from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from backend.database import engine, SessionLocal, Base
from backend.models import Customer, Purchase


# ---------------- APP INIT ----------------
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="triple_n_supermart_secret",
    same_site="lax"
)



app.mount(
    "/static",
    StaticFiles(directory="backend/static"),
    name="static"
)

templates = Jinja2Templates(directory="backend/templates")

# Create tables automatically
Base.metadata.create_all(bind=engine)

# ---------------- DATABASE DEPENDENCY ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------- ADMIN LOGIN ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin-login")
def admin_login_process(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":
        request.session["admin_logged_in"] = True
        return RedirectResponse("/admin-dashboard", status_code=302)
    return {"error": "Invalid admin credentials"}

@app.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin")
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# ---------------- ADMIN LOGOUT ----------------
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

# ---------------- CUSTOMER LOGIN ----------------
@app.get("/customer-login", response_class=HTMLResponse)
def customer_login_page(request: Request):
    return templates.TemplateResponse("customer_login.html", {"request": request})

@app.post("/customer-login")
def customer_login_process(
    request: Request,
    customer_id: str = Form(...),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        return {"error": "Invalid Customer ID"}

    request.session["customer_logged_in"] = True
    request.session["customer_id"] = customer.customer_id
    return RedirectResponse(f"/customer-dashboard/{customer.customer_id}", status_code=302)

# ---------------- CUSTOMER LOGOUT ----------------
@app.get("/customer-logout")
def customer_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

# ---------------- CUSTOMER DASHBOARD ----------------
@app.get("/api/customer/{customer_id}")
def get_customer_dashboard(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        return {"error": "Customer not found"}

    purchases = db.query(Purchase).filter(Purchase.customer_id == customer_id).all()

    purchase_list = []
    for p in purchases:
        purchase_list.append({
            "amount": p.amount,
            "points_earned": p.points_earned,
            "date": p.created_at.strftime("%d-%m-%Y %H:%M")
        })

    return {
        "customer": {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "total_points": customer.points
        },
        "purchases": purchase_list
    }



# ---------------- AUTO CUSTOMER ID ----------------
def generate_customer_id(db):
    count = db.query(Customer).count() + 1
    return f"TNM{count:05d}"

# ---------------- CREATE CUSTOMER ----------------
@app.post("/admin/create-customer")
def create_customer(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    exists = db.query(Customer).filter(
        (Customer.phone == phone) | (Customer.email == email)
    ).first()

    if exists:
        return {"error": "Customer already exists"}

    customer_id = generate_customer_id(db)

    new_customer = Customer(
        customer_id=customer_id,
        name=name,
        phone=phone,
        email=email,
        points=0
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return {
        "message": "Customer created",
        "customer_id": customer_id
    }
# ----------------CUSTOMER SIGNUP OTPION ------------
@app.post("/customer/register")
def customer_register(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check duplicate
    exists = db.query(Customer).filter(
        (Customer.phone == phone) | (Customer.email == email)
    ).first()
    if exists:
        return {"error": "Phone or Email already registered"}

    customer_id = generate_customer_id(db)

    new_customer = Customer(
        customer_id=customer_id,
        name=name,
        phone=phone,
        email=email,
        points=0
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return {
        "message": "Registration successful",
        "customer_id": customer_id
    }
@app.get("/customer-signup", response_class=HTMLResponse)
def customer_signup_page(request: Request):
    return templates.TemplateResponse("customer_signup.html", {"request": request})

# ---------------- ADD PURCHASE ----------------
@app.post("/admin/add-purchase")
def add_purchase(
    customer_id: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        return {"error": "Customer not found"}

    points = int(amount)  # 1 SGD = 1 point

    new_purchase = Purchase(
        customer_id=customer.customer_id,
        amount=amount,
        points_earned=points
    )

    customer.points += points

    db.add(new_purchase)
    db.commit()
    db.refresh(customer)

    return {
        "message": "Purchase added",
        "points_added": points,
        "total_points": customer.points
    }

# ---------------- CUSTOMER API VIEW ----------------
@app.get("/customer-dashboard/{customer_id}", response_class=HTMLResponse)
def customer_dashboard_page(request: Request, customer_id: str):
    return templates.TemplateResponse(
        "customer_dashboard.html",
        {"request": request, "customer_id": customer_id}
    )
