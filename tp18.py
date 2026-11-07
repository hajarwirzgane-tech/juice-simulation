from fastapi import FastAPI

app = FastAPI(
    title="Simulateur de Concentration de Jus",
    description="API pour le calcul des bilans de matière et d'énergie",
    version="1.0"
)

@app.get("/")
def home():
    return {"message": "مرحباً بك في واجهة محاكاة تركيز عصير الفواكه!"}

@app.get("/calcul")
def calculate_process(
    m0: float = 1000, 
    x0: float = 0.02, 
    y0: float = 0.10, 
    mR: float = 100, 
    yR: float = 0.40, 
    y4: float = 0.40, 
    T3: float = 80
):
    Cp = 3.8
    lambda_v = 2300
    T2 = 20
    T5 = 25
    
    residus = m0 * x0
    m1 = m0 - residus
    y1 = (m0 * y0) / m1
    
    m2 = m1 + mR
    y2 = (m1 * y1 + mR * yR) / m2
    
    Q3 = (m2 * Cp * (T3 - T2)) / 3600
    
    m4 = (m2 * y2) / y4
    mv = m2 - m4
    Q4 = (mv * lambda_v) / 3600
    
    Q5 = (m4 * Cp * (T3 - T5)) / 3600
    
    entrees = m0 + mR
    sorties = residus + mv + m4
    
    return {
        "parametres_entree": {
            "m0": m0, "mR": mR, "T3": T3, "y4": y4 * 100
        },
        "resultats": {
            "debit_filtre_m1_kg_h": round(m1, 2),
            "concentration_melange_y2_pct": round(y2 * 100, 2),
            "puissance_chauffage_Q3_kW": round(Q3, 2),
            "eau_evaporee_mv_kg_h": round(mv, 2),
            "debit_concentre_m4_kg_h": round(m4, 2),
            "puissance_evaporation_Q4_kW": round(Q4, 2),
            "puissance_refroidissement_Q5_kW": round(Q5, 2)
        },
        "verification_bilan_global_kg_h": round(entrees - sorties, 2)
    }