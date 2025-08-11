\# Amazon Arbitrage Manager (Streamlit)



Web app per gestire l'arbitraggio su Amazon con dataset Keepa. Supporta:

\- Upload di file \*\*XLSX\*\* (origine e opzionale file di vendita/target).

\- Normalizzazione `Locale` → codici ISO2 (con eccezione GB→UK).

\- \*\*IVA selezionata automaticamente\*\* per ogni riga (configurabile da UI).

\- \*\*Regole sconto\*\* gift-card \*\*esatte\*\*:

&nbsp; - \*\*Estero (≠ IT)\*\*: `Net = Price / (1 + VAT) \* (1 - Discount)`

&nbsp; - \*\*Italia (IT)\*\*: `Net = Price / (1 + VAT) - Price \* Discount`

\- Join per \*\*ASIN\*\* tra origine e vendita (se fornito file target) e calcolo di \*\*NetCost\*\*, \*\*Net Proceeds\*\*, \*\*Margine\*\* e \*\*ROI\*\*.

\- Filtri rapidi (es. escludi ricondizionato), esportazione CSV/XLSX.



\## Avvio locale

```bash

pip install -r requirements.txt

streamlit run app.py

