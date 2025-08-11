# Amazon Market Analyzer – v2 (Complete)

Dashboard Streamlit per analizzare l'arbitraggio tra marketplace Amazon con **Opportunity Score 2.0**.
- **Upload unico multi-paese** (Keepa CSV/XLSX)
- **Pairing Acquisto→Vendita** automatico per ASIN
- **Calcolo Margine** con regole **IVA & SCONTO INVARIATE**
- **Punteggio v2** (Domanda, Concorrenza, Disponibilità, Vantaggio Prezzo, Logistica, Rischio, Stabilità, Margine)
- **UI dark** (rosso/nero/bianco) in stile HDGaming.it

## Avvio
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dati richiesti
Il dataset deve contenere almeno: `ASIN`, `Locale`, prezzi (es. **Buy Box 🚚: Current**) e metriche principali. È possibile caricare in un colpo solo file di diversi paesi; la colonna `Locale` viene normalizzata in **country** (IT, DE, FR, ...).

## IVA & SCONTO (regole NON modificate)
- **Estero (non IT)**: `Net = Price/(1+VAT) * (1 - Discount)`
- **Italia (IT)**: `Net = Price/(1+VAT) - Price*Discount`

L'implementazione è in `utils.py: apply_vat_discount_rules` ed è già collegata all'app.

## Flusso
1. Carica i file Keepa (CSV/XLSX) dei vari paesi.
2. Scegli **Paesi ACQUISTO** e **VENDITA** dalla sidebar (puoi selezionare più mercati).
3. Imposta eventuali **sconti** per paese (Acquisto), pesi Score v2 e modalità **FBA/FBM**.
4. Analizza la **classifica** e scarica i risultati CSV.

## Note
- Gli alias per gli header Keepa sono in `core/config.py` → `ALIAS_MAP`. Aggiungi alias se usi nomi diversi.
- Per FBM è impostato un costo fisso (configurabile in `core/config.py`).
- I pesi dello Score v2 sono regolabili in UI.

Buon sourcing!
