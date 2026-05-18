import json
import pandas as pd
import os
import datetime
from difflib import SequenceMatcher

class SME_AutoKit_Pro:
    def __init__(self):
        self.db_path = 'msic_database.json'
        self.memory_path = 'user_learning_memory.json'
        self.load_data()

        self.golden_rules = {
            "56210": [
                "catering", "katering", "event", "majlis", "wedding", "perkahwinan",
                "kenduri", "buffet", "bufet", "khemah", "canopy",
                "decoration", "hiasan", "pelamin",
                "photographer", "videographer", "drone",
                "emcee", "entertainer", "entertainment", "hiburan",
                "sound system", "pa system", "lampu pentas",
                "birthday party", "harijadi", "annual dinner"
            ],
            "43224": [
                "aircond", "air cond", "aircon", "air-cond", "penghawa dingin",
                "cuci aircond", "install aircond", "service aircond",
                "plumbing", "paip bocor", "leaking pipe", "sinki", "toilet repair",
                "wiring", "electrical", "pendawaian", "light fitting",
                "ceiling fan", "exhaust fan", "kipas siling",
                "generator", "genset", "solar panel", "water heater", "pemanas air",
                "water pump", "pam air", "sewerage", "longkang"
            ],
            "45201": [
                "workshop kereta", "bengkel kereta", "car workshop",
                "engine oil", "minyak enjin", "oil change", "tukar minyak",
                "tyre", "tayar", "rim", "brake pad", "brek pad",
                "car battery", "bateri kereta", "spark plug",
                "wiper", "absorber", "wheel alignment", "wheel balancing",
                "cat kereta", "car polish", "coating kereta", "tinted",
                "service kereta", "car service", "puspakom", "road tax"
            ],
            "46631": [
                "hardware", "screw", "skru", "wrench", "spanner", "bolt", "nut",
                "paku", "hammer", "tukul", "drill bit", "gergaji",
                "wall paint", "paint -", "paint white", "cat dinding", "cat besi",
                "brush roller", "sealant", "cement", "simen", "tile", "jubin",
                "wire rope", "steel cable", "plug socket", "circuit breaker",
                "plywood", "timber", "tempered glass", "steel bar", "besi",
                "roofing", "bumbung", "zinc roof", "aluminium",
                "ladder", "tangga", "toolbox", "measuring tape"
            ],
            "56101": [
                "cafe", "coffee shop", "kopi", "teh tarik", "milo", "neslo",
                "restoran", "restaurant", "warung", "mamak",
                "nasi", "chicken rice", "nasi ayam", "mee", "noodle",
                "roti canai", "kuih", "kek",
                "ayam goreng", "ikan goreng", "daging", "kambing",
                "sup", "curry", "kari", "rendang", "satay", "burger", "pizza",
                "takeaway", "bungkus", "dine in", "tapau",
                "breakfast set", "lunch set", "dinner set", "brunch"
            ],
            "47111": [
                "sundry", "runcit", "grocery", "provision shop",
                "beras", "minyak masak", "cooking oil", "gula", "sugar",
                "tepung", "garam", "sos", "kicap", "soy sauce",
                "sabun mandi", "shampoo", "syampu", "toothpaste", "ubat gigi",
                "tisu", "toilet paper", "pampers", "diaper",
                "air mineral", "mineral water", "soft drink", "100 plus",
                "instant noodle", "maggi", "santan", "coconut milk",
                "fresh milk", "susu segar", "telur", "butter", "margarine"
            ],
            "62010": [
                "software", "sistem", "app development", "application",
                "website", "laman web", "coding", "programming",
                "it solution", "tech support", "server", "hosting",
                "cloud service", "database", "cybersecurity", "antivirus",
                "e-invoice system", "einvois", "pos system",
                "accounting software", "erp", "crm",
                "domain", "email setup", "wifi setup", "it maintenance"
            ],
            "96021": [
                "salon", "saloon", "hair cut", "potong rambut", "hair colour",
                "rebonding", "rebond", "hair treatment", "rawatan rambut",
                "facial", "face treatment", "waxing", "threading", "eyebrow",
                "manicure", "pedicure", "gel nail", "nail art", "kuku",
                "eyelash", "bulu mata", "makeup", "solek",
                "beauty treatment", "kecantikan", "spa", "body massage", "urut",
                "skincare", "moisturizer", "serum", "botox", "filler"
            ],
            "85491": [
                "tuition", "tuisyen", "kelas tuisyen", "lesson fee",
                "teaching fee", "tutorial", "workshop fee", "bengkel",
                "course fee", "kursus", "training fee", "seminar",
                "mathematics class", "science class", "english class",
                "piano lesson", "violin", "guitar lesson", "music class",
                "coding class", "robotics class", "stem",
                "tadika", "kindergarten", "daycare", "nursery"
            ],
            "49410": [
                "logistics", "logistik", "courier service", "kurier",
                "courier -", "same day delivery", "delivery service",
                "penghantaran", "shipping", "lorry rental", "lori",
                "grab express", "lalamove", "poslaju",
                "freight", "cargo", "kargo", "forwarding agent",
                "warehouse", "gudang", "storage fee", "packing service"
            ],
            "47910": [
                "online shop", "kedai online", "shopee", "lazada", "tiktok shop",
                "ecommerce", "e-commerce", "marketplace fee",
                "dropship", "dropshipping", "reseller",
                "digital product", "produk digital", "ebook",
                "facebook shop", "instagram shop", "whatsapp order"
            ],
            "86110": [
                "klinik", "clinic", "doktor", "doctor", "physician",
                "consultation fee", "medical consultation",
                "ubat", "medicine", "medication", "prescription",
                "pharmacy", "farmasi", "tablet", "capsule",
                "injection", "suntikan", "blood test", "ujian darah",
                "dental", "gigi", "dentist", "tooth filling",
                "veterinary", "vet clinic", "vaccination", "vaksin"
            ],
            "18110": [
                "printing", "percetakan", "cetak",
                "banner printing", "bunting", "backdrop printing", "signboard",
                "flyer", "pamphlet", "brochure", "brosur",
                "name card", "kad nama", "business card", "letterhead",
                "t-shirt print", "jersey print", "baju seragam",
                "sticker", "packaging design", "logo design",
                "graphic design", "rekabentuk", "photocopy", "fotostat"
            ],
            "69100": [
                "accounting fee", "yuran perakaunan", "audit fee",
                "tax consultation", "tax filing", "cukai",
                "legal fee", "guaman", "lawyer fee", "peguam",
                "professional fee", "yuran profesional",
                "management fee", "yuran pengurusan",
                "company secretary", "ssm registration",
                "payroll service", "hr service", "recruitment fee"
            ],
            "01110": [
                "baja", "fertilizer", "racun serangga", "pesticide", "herbicide",
                "benih", "seedling", "anak pokok", "sayur segar", "vegetable farm",
                "buah segar", "organic farm", "hydroponic", "hidroponik",
                "ladang", "sawit", "padi", "getah",
                "fish farm", "udang", "prawn", "ketam", "crab farm",
                "ayam kampung", "duck farm", "itik", "ternakan"
            ],
        }

    def load_data(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
        else:
            self.db = []
        if os.path.exists(self.memory_path):
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                self.memory = json.load(f)
        else:
            self.memory = {}

    def save_correction(self, item_text, correct_code):
        item_key = str(item_text).lower().strip()
        self.memory[item_key] = str(correct_code)
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=4, ensure_ascii=False)

    def match_logic(self, text):
        text = str(text).lower().strip()
        if not text or text == 'nan':
            return "N/A", "🚨 ERROR: No Data"
        if text in self.memory:
            return self.memory[text], "🟢 GREEN: User Verified (100% Safe)"
        for code, kws in self.golden_rules.items():
            if any(kw in text for kw in kws):
                return code, "🟢 GREEN: Industry Golden Rule (100% Safe)"
        best_code, highest_score = "Manual Review", 0
        for item in self.db:
            sim = SequenceMatcher(None, text, item['desc'].lower()).ratio()
            if sim > highest_score:
                highest_score, best_code = sim, item['code']
        if highest_score > 0.75:
            return best_code, "🟡 YELLOW: High Confidence (Verify Needed)"
        elif highest_score > 0.50:
            return best_code, "🟡 YELLOW: Medium Confidence (Please Verify)"
        return "Manual Review", "🔴 RED: High Risk (Manual Action Required)"

    def generate_lhdn_batch_json(self, df):
        """Generate JSON directly from DataFrame — no file I/O"""
        all_ready_data = []
        total_tax_summary = 0.0
        total_amount_summary = 0.0
        zero_tax_codes = ["47111"]

        target_col = next((c for c in df.columns if any(
            k in str(c).lower() for k in ['item', 'desc', '商品', '描述'])), "Item")

        ready = df[df['Export_Ready'] == "YES"]

        for _, row in ready.iterrows():
            price = float(row.get('Price', 0.0))
            qty   = float(row.get('Qty', 1.0))
            if price <= 0:
                continue

            raw_code = str(row['Suggested_MSIC']).split('.')[0].strip().zfill(5)
            current_tax_rate = 0.00 if raw_code in zero_tax_codes else 0.06
            tax_type_code    = "02" if current_tax_rate == 0.00 else "01"

            sub_total    = round(price * qty, 2)
            tax_amount   = round(sub_total * current_tax_rate, 2)
            total_payable = round(sub_total + tax_amount, 2)

            total_tax_summary    += tax_amount
            total_amount_summary += total_payable

            def clean(val):
                s = str(val).strip()
                return "" if s in ("nan", "None", "NaN") else s

            lhdn_item = {
                "invoiceNo":   f"INV-{datetime.datetime.now().strftime('%Y%m')}-{len(all_ready_data)+1:04d}",
                "invoiceDate": clean(row.get('_invoice_date', str(datetime.date.today()))),
                "currency":    clean(row.get('_currency', 'MYR')) or 'MYR',
                "note":        clean(row.get('_invoice_note', '')),
                "seller": {
                    "name":    clean(row.get('_client_name', '')),
                    "tin":     clean(row.get('_client_tin', '')),
                    "reg_no":  clean(row.get('_client_reg', '')),
                    "sst_no":  clean(row.get('_client_sst', '')),
                    "address": clean(row.get('_client_address', ''))
                },
                "buyer": {
                    "name":    clean(row.get('_buyer_name', '')),
                    "tin":     clean(row.get('_buyer_tin', '')),
                    "reg_no":  clean(row.get('_buyer_reg', '')),
                    "address": clean(row.get('_buyer_address', ''))
                },
                "item": {
                    "classification": raw_code,
                    "description":    str(row.get(target_col, "N/A")),
                    "unitPrice":      price,
                    "quantity":       int(qty),
                    "taxRate":        f"{int(current_tax_rate * 100)}%",
                    "taxType":        tax_type_code,
                    "calculation": {
                        "subTotal":     sub_total,
                        "taxAmount":    tax_amount,
                        "totalPayable": total_payable
                    }
                }
            }
            all_ready_data.append(lhdn_item)

        if all_ready_data:
            return {
                "header": {
                    "batch_id":             datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                    "total_records":        len(all_ready_data),
                    "total_tax_amount":     round(total_tax_summary, 2),
                    "total_payable_amount": round(total_amount_summary, 2),
                    "generated_at":         datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "invoice_items": all_ready_data
            }
        return None


def get_styled_df(df):
    def style_logic(row):
        status = str(row.get('Compliance_Status', ''))
        if "🟢" in status:   bg = '#d4edda'
        elif "🟡" in status: bg = '#fff3cd'
        else:                bg = '#f8d7da'
        return [f'background-color: {bg}; color: #212529; font-weight: bold;' for _ in row]
    return df.style.apply(style_logic, axis=1)
