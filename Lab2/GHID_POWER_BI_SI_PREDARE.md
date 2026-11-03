# Lab 2 — Ghid Power BI și predare

Notebook-urile sunt deja în Databricks, în `Workspace → Users → d.panutsa@gmail.com → Lab2`:

- `lab2_databricks` — notebook-ul principal (părțile 1–4);
- `lab2_stream_worker` — job-ul de streaming, pornit de notebook-ul principal în secțiunea 3.3.

Tabelele rezultate sunt în `workspace.lab2`.

| Tabel | Rol |
|---|---|
| `bronze_payroll`, `bronze_civil_list` | date încărcate din Lab 1 (~90 MB) |
| `silver_payroll_features` | rânduri pregătite pentru model, partiționate pe `fiscal_year` |
| `gold_predictions` | predicții pentru toți anii, partiționate pe `fiscal_year` |
| `gold_predictions_backup` | copia DEEP CLONE |
| `stream_incoming`, `gold_predictions_stream` | sursa și destinația fluxului cu reluare după cădere |
| `pipeline_monitoring_log` | jurnalul de monitorizare |
| `gold_model_metrics` | AUC, F1, precizie, recall |
| **`gold_dashboard_agency_year`** | **tabelul pentru Power BI** |

---

## 1. Rulați notebook-ul interactiv (pentru .ipynb și HTML cu rezultate)

1. Deschideți `Lab2/lab2_databricks` → **Connect** → **Serverless** → **Run all**. Durează ~8–10 minute.
   - Dacă apare o întrebare despre mediu, alegeți **Environment version 4** (deja setat în notebook).
2. După rulare: **File → Export → IPython Notebook** (`.ipynb`, cu rezultate) și **File → Export → HTML**.
3. Faceți la fel pentru `lab2_stream_worker`. Rezultatele lui se văd în **Jobs & Pipelines → Runs**: cele două rulări pornite de notebook, prima cu status *Failed* (căderea simulată), a doua *Succeeded*. Faceți o captură de ecran cu ele ca dovadă de monitorizare.

> Exportul din job nu păstrează celulele ca `.ipynb` cu output, de aceea rularea interactivă e necesară pentru predare.

---

## 2. Conectarea Power BI Desktop la Databricks

1. În Databricks: **SQL Warehouses → Serverless Starter Warehouse → Connection details**. Copiați:
   - **Server hostname**: `dbc-2efdc576-8d89.cloud.databricks.com`
   - **HTTP path**: `/sql/1.0/warehouses/b385175c6b505a92`
2. Token: **avatar (dreapta sus) → Settings → Developer → Access tokens → Generate new token**. Copiați-l doar în Power BI; nu îl puneți în notebook sau în fișierele predate.
3. Power BI Desktop → **Get data → More… → Azure Databricks** (merge și pentru Databricks pe AWS).
   - Server hostname și HTTP path de mai sus.
   - **Data Connectivity mode: Import** (cerința: `.pbix` cu date importate).
   - Autentificare: **Personal Access Token** → lipiți token-ul.
4. În Navigator: `workspace → lab2` → bifați **`gold_dashboard_agency_year`** și **`gold_model_metrics`** → **Load**.

---

## 3. Măsuri DAX (Modeling → New measure, pe tabelul `gold_dashboard_agency_year`)

```DAX
Înregistrări = SUM(gold_dashboard_agency_year[records])

Angajați OT reali = SUM(gold_dashboard_agency_year[actual_ot_employees])

Angajați OT așteptați (model) = SUM(gold_dashboard_agency_year[expected_ot_employees])

Rată OT reală = DIVIDE([Angajați OT reali], [Înregistrări])

Rată OT prezisă = DIVIDE([Angajați OT așteptați (model)], [Înregistrări])

Plăți OT totale = SUM(gold_dashboard_agency_year[total_ot_paid])

Plată OT medie per angajat OT = DIVIDE([Plăți OT totale], [Angajați OT reali])

Cost OT estimat (model) = [Angajați OT așteptați (model)] * [Plată OT medie per angajat OT]

Eroare predicție (pp) = ([Rată OT prezisă] - [Rată OT reală]) * 100

Ultima actualizare = MAX(gold_dashboard_agency_year[refreshed_at])
```

Formatați ratele ca **Percentage** și plățile/costurile ca **Currency ($)**.

---

## 4. Pagina de raport (minimum: 2 indicatori, 2 tipuri de grafice, 2 filtre)

**Indicatori (Card / KPI)**

1. `Rată OT prezisă` *(din predicții)*
2. `Rată OT reală`
3. `Cost OT estimat (model)` *(din predicții)*
4. `Ultima actualizare` (pentru demonstrarea refresh-ului)
5. *(opțional)* card din `gold_model_metrics[roc_auc]` și `[f1]`

**Grafice**

1. **Clustered bar chart** — Axa Y: `agency_name`; valori: `Rată OT reală` și `Rată OT prezisă`. Filtru vizual *Top N = 15 după Înregistrări*. *(folosește predicțiile)*
2. **Line chart** — Axa X: `fiscal_year`; valori: `Angajați OT reali` și `Angajați OT așteptați (model)`.
3. *(opțional)* **Treemap** sau **Donut** — `work_location_borough` după `Plăți OT totale`.
4. *(opțional)* **Table** — agenție, `Rată OT prezisă`, `Plată OT medie per angajat OT`, `Cost OT estimat (model)`, sortat descrescător.

**Filtre (Slicers)**

1. `fiscal_year` (dropdown sau listă)
2. `work_location_borough`
3. *(opțional)* `pay_basis`, `split` (`test` = doar anul nevăzut de model, 2025)

Titlu sugerat: *„NYC Payroll — Risc de ore suplimentare (real vs. prezis)”*. Salvați ca `lab2_dashboard.pbix`.

---

## 5. Demonstrarea filtrării și a actualizării

- **Filtrare:** selectați anul 2025 și un borough; toate cardurile și graficele se schimbă.
- **Actualizare:**
  1. Notați valoarea cardului `Ultima actualizare`.
  2. În Databricks, rulați din nou celula `build_dashboard_table()` din secțiunea 4 (sau tot notebook-ul).
  3. În Power BI: **Home → Refresh**. `Ultima actualizare` se schimbă la noua oră.
  4. Pentru o modificare vizibilă și în cifre, rulați în Databricks înainte de refresh, de exemplu:
     ```sql
     DELETE FROM workspace.lab2.gold_dashboard_agency_year WHERE work_location_borough = 'UNKNOWN';
     ```
     După refresh, totalurile scad. Rulați apoi din nou `build_dashboard_table()` și refresh ca să reveniți la datele complete.

---

## 6. Ce explicați (decizii și limite) — text gata de pus în raport

**Decizia 1 — Bugetul de overtime pe agenții.** `Cost OT estimat (model)` pe agenție arată unde trebuie rezervat bugetul de ore suplimentare pentru anul următor. Agențiile din vârful clasamentului (de regulă poliție, pompieri, corecții) primesc prioritate la planificare.

**Decizia 2 — Angajări vs. ore suplimentare.** Agențiile/borough-urile cu rată prezisă mare *și* plată OT medie mare sunt candidate pentru posturi noi sau redistribuirea personalului. Când costul anual al overtime-ului depășește costul unui post, angajarea e mai ieftină.

**Limitele predicțiilor**

- Modelul prezice *dacă* apar ore suplimentare, nu suma; costul e estimat cu plata medie istorică.
- Nu anticipează schimbări de politică, crize sau reorganizări de agenții.
- Rândurile sunt înregistrări salariale, nu persoane unice.
- Doar `split = test` (2025) arată performanța reală; anii de antrenare dau valori optimiste.
- Probabilitățile sunt pentru decizii la nivel de agenție/borough, nu pentru persoane individuale.

---

## 7. Ce încărcați în Google Drive

- `lab2_databricks.ipynb` și `lab2_databricks.html` (exportate după **Run all**)
- `lab2_stream_worker.ipynb` și `.html`
- `lab2_dashboard.pbix` (cu date importate)
- capturi: Jobs → Runs (Failed + Succeeded) și raportul Power BI filtrat

**Nu** includeți token-ul Databricks. Power BI nu salvează token-ul în `.pbix`, dar verificați să nu fie scris în vreun text sau în vreo captură.
