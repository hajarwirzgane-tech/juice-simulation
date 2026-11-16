import os
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# 1. إعداد قاعدة البيانات (كتخدم أوتوماتيكياً فـ Render بـ SQLite أو كتاخد رابط DB من Render)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 2. جداول قاعدة البيانات (Models)
class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(50), unique=True, index=True, nullable=False)
  password = Column(String(255), nullable=False)
  simulations = relationship("SimulationResult", back_populates="owner")


class SimulationResult(Base):
  __tablename__ = "simulations"
  id = Column(Integer, primary_key=True, index=True)
  feed_flow = Column(Float, nullable=False)  # التدفق الأولي (kg/h)
  initial_brix = Column(Float, nullable=False)  # التركيز الأولي (%)
  final_brix = Column(Float, nullable=False)  # التركيز النهائي (%)
  concentrate_flow = Column(Float, nullable=False)  # تدفق المركز (kg/h)
  evaporated_water = Column(Float, nullable=False)  # الماء المتبخر (kg/h)
  user_id = Column(Integer, ForeignKey("users.id"))
  owner = relationship("User", back_populates="simulations")


Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


app = FastAPI(title="Génie des Procédés - Concentration Web App")


# 3. قالب الواجهة الأمامية (HTML/CSS مدمج)
def render_page(content: str, title: str = "Simulation Génie des Procédés"):
  return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; color: #1e293b; }}
            .container {{ max-width: 800px; margin: 30px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
            h1, h2 {{ color: #0f172a; margin-top: 0; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: 600; }}
            input {{ width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; font-size: 15px; }}
            button {{ background: #2563eb; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; width: 100%; }}
            button:hover {{ background: #1d4ed8; }}
            .btn-secondary {{ background: #475569; margin-top: 10px; }}
            .btn-secondary:hover {{ background: #334155; }}
            .alert {{ padding: 12px; background: #fee2e2; color: #b91c1c; border-radius: 6px; margin-bottom: 15px; }}
            .success {{ padding: 12px; background: #dcfce7; color: #15803d; border-radius: 6px; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #f8fafc; color: #334155; }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 25px; }}
            .logout {{ color: #dc2626; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            {content}
        </div>
    </body>
    </html>
    """


# 4. صفحة الدخول والتسجيل (Login / Register)
@app.get("/", response_class=HTMLResponse)
def home_page(error: str = None, msg: str = None):
  alert_html = f'<div class="alert">{error}</div>' if error else ""
  msg_html = f'<div class="success">{msg}</div>' if msg else ""
  content = f"""
    <h1>🧪 Simulation : Concentration de Jus de Fruits</h1>
    <p>Connectez-vous pour accéder au simulateur et sauvegarder vos bilans de matière.</p>
    {alert_html}
    {msg_html}
    <form action="/login" method="post">
        <div class="form-group">
            <label>Nom d'utilisateur</label>
            <input type="text" name="username" required placeholder="Ex: hajar">
        </div>
        <div class="form-group">
            <label>Mot de passe</label>
            <input type="password" name="password" required placeholder="••••••••">
        </div>
        <button type="submit">Se connecter</button>
    </form>
    <hr style="margin: 25px 0; border: 0; border-top: 1px solid #e2e8f0;">
    <h2>Créer un compte</h2>
    <form action="/register" method="post">
        <div class="form-group">
            <label>Nouveau nom d'utilisateur</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Nouveau mot de passe</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn-secondary">S'inscrire</button>
    </form>
    """
  return render_page(content)


@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
  existing_user = db.query(User).filter(User.username == username).first()
  if existing_user:
    return RedirectResponse(
        url="/?error=Ce+nom+d'utilisateur+existe+déjà", status_code=303
    )
  new_user = User(username=username, password=password)
  db.add(new_user)
  db.commit()
  return RedirectResponse(
      url="/?msg=Compte+créé+avec+succès!+Connectez-vous.", status_code=303
  )


@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
  user = (
      db.query(User)
      .filter(User.username == username, User.password == password)
      .first()
  )
  if not user:
    return RedirectResponse(
        url="/?error=Identifiants+incorrects", status_code=303
    )
  return RedirectResponse(url=f"/dashboard/{user.id}", status_code=303)


# 5. لوحة التحكم وحساب الموازنة المادية (Bilan de matière)
@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard(user_id: int, error: str = None, db: Session = Depends(get_db)):
  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    return RedirectResponse(url="/", status_code=303)

  alert_html = f'<div class="alert">{error}</div>' if error else ""
  rows = ""
  for sim in reversed(user.simulations):
    rows += f"""
        <tr>
            <td>{sim.feed_flow:.2f}</td>
            <td>{sim.initial_brix:.1f}%</td>
            <td>{sim.final_brix:.1f}%</td>
            <td><strong>{sim.concentrate_flow:.2f}</strong></td>
            <td><strong>{sim.evaporated_water:.2f}</strong></td>
        </tr>
        """

  content = f"""
    <div class="header-bar">
        <h2>Bienvenue, {user.username} 👋</h2>
        <a href="/" class="logout">Déconnexion</a>
    </div>
    {alert_html}
    <h3>Nouveau calcul d'évaporation (Bilan de matière)</h3>
    <form action="/calculate/{user.id}" method="post">
        <div class="form-group">
            <label>Débit d'alimentation F (kg/h)</label>
            <input type="number" step="0.01" name="feed_flow" required placeholder="Ex: 1000">
        </div>
        <div class="form-group">
            <label>Concentration initiale X_F (% Brix)</label>
            <input type="number" step="0.1" name="initial_brix" required placeholder="Ex: 12">
        </div>
        <div class="form-group">
            <label>Concentration finale souhaitée X_C (% Brix)</label>
            <input type="number" step="0.1" name="final_brix" required placeholder="Ex: 65">
        </div>
        <button type="submit">Calculer et Enregistrer</button>
    </form>

    <h3 style="margin-top: 30px;">Historique des simulations</h3>
    <table>
        <thead>
            <tr>
                <th>Alimentation F (kg/h)</th>
                <th>Brix Initial</th>
                <th>Brix Final</th>
                <th>Concentrat C (kg/h)</th>
                <th>Eau évaporée V (kg/h)</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="5">Aucune simulation enregistrée</td></tr>'}
        </tbody>
    </table>
    """
  return render_page(content, title="Tableau de bord - Simulation")


@app.post("/calculate/{user_id}")
def calculate(
    user_id: int,
    feed_flow: float = Form(...),
    initial_brix: float = Form(...),
    final_brix: float = Form(...),
    db: Session = Depends(get_db),
):
  if final_brix <= initial_brix or final_brix <= 0 or feed_flow <= 0:
    return RedirectResponse(
        url=f"/dashboard/{user_id}?error=Valeurs+invalides+(Brix+final+doit+être+supérieur+au+Brix+initial)",
        status_code=303,
    )

  # Bilan partiel sur le solide : F * X_F = C * X_C
  concentrate_flow = (feed_flow * initial_brix) / final_brix
  # Bilan global : F = C + V  =>  V = F - C
  evaporated_water = feed_flow - concentrate_flow

  sim = SimulationResult(
      feed_flow=feed_flow,
      initial_brix=initial_brix,
      final_brix=final_brix,
      concentrate_flow=concentrate_flow,
      evaporated_water=evaporated_water,
      user_id=user_id,
  )
  db.add(sim)
  db.commit()
  return RedirectResponse(url=f"/dashboard/{user_id}", status_code=303)