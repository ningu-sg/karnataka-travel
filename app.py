 
"""
Karnataka Yatri — Flask frontend for the Karnataka tourism chatbot.

Prerequisites:
    1. Install Ollama:   https://ollama.com/download
    2. Pull the model:   ollama pull llama3.2:latest
    3. Start the server: ollama serve   (usually auto-starts)
    4. pip install flask requests

Run:
    python3 app.py
Then open http://localhost:5000 in your browser.
"""

import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:latest"

# ---------------------------------------------------------------------------
# Karnataka knowledge base (embedded directly, no external data file needed)
# ---------------------------------------------------------------------------
REGIONS = {
    "Bengaluru": {
        "aliases": ["bangalore", "bengaluru", "blr"],
        "district": "Bengaluru Urban", "type": "Metropolitan city",
        "villages_and_places": ["Lalbagh Botanical Garden", "Cubbon Park", "Bangalore Palace", "Nandi Hills (day trip)", "ISKCON Temple", "Wonderla Amusement Park"],
        "food": ["V.V. Puram / Thindi Beedhi food street (all-vegetarian)", "Masala dosa, idli-vada", "Bisi bele bath", "Multi-cuisine due to migrant population"],
        "transport": ["Namma Metro", "BMTC city buses", "Auto-rickshaws", "Ride-hailing apps (Ola, Uber, Rapido)", "Well connected by air, rail, and highways"],
        "payment_modes": ["UPI widely accepted", "Cards", "Cash", "Metro smart cards"],
        "network": "Excellent 4G/5G coverage across the city",
        "stay_types": ["Luxury hotels", "Business hotels", "Budget lodges", "Serviced apartments", "Hostels"],
        "rating": 4.5, "best_time_to_visit": "October to February",
    },
    "Mysuru": {
        "aliases": ["mysore", "mysuru"],
        "district": "Mysuru", "type": "Heritage city",
        "villages_and_places": ["Mysuru Palace", "Chamundi Hills", "Brindavan Gardens", "St. Philomena's Church", "Mysuru Zoo", "Srirangapatna (nearby)"],
        "food": ["Mysore masala dosa", "Mysore pak (sweet)", "Bisi bele bath", "Mysuru Dasara food mela (Sep/Oct)"],
        "transport": ["City buses (KSRTC)", "Auto-rickshaws", "Cabs", "Train/road from Bengaluru (~3 hrs)"],
        "payment_modes": ["UPI", "Cards at hotels/restaurants", "Cash at small vendors"],
        "network": "Good 4G coverage in city, patchy near rural outskirts",
        "stay_types": ["Heritage hotels", "Budget hotels", "Homestays"],
        "rating": 4.6, "best_time_to_visit": "September to March (Dasara peak)",
    },
    "Hampi": {
        "aliases": ["hampi", "vijayanagara"],
        "district": "Ballari (Vijayanagara)", "type": "UNESCO heritage / rural village site",
        "villages_and_places": ["Hampi Bazaar village", "Virupaksha Temple", "Lotus Mahal", "Elephant Stables", "Vittala Temple", "Anegundi village"],
        "food": ["Village-style vegetarian thalis", "Backpacker cafes near Hampi Bazaar and Sanapur", "Fresh coconut, banana chips"],
        "transport": ["Coracle boat rides", "Bicycles and mopeds for rent", "Auto-rickshaws", "Nearest railhead: Hospet Junction (~13 km)"],
        "payment_modes": ["Cash strongly recommended", "UPI works in main bazaar area"],
        "network": "Patchy — moderate 4G in Hampi Bazaar, weak near ruins/river villages",
        "stay_types": ["Budget guesthouses", "Backpacker hostels", "River-side cottages", "A few resorts on the outskirts"],
        "rating": 4.7, "best_time_to_visit": "October to February",
    },
    "Coorg": {
        "aliases": ["coorg", "kodagu", "madikeri"],
        "district": "Kodagu", "type": "Hill station",
        "villages_and_places": ["Madikeri town", "Abbey Falls", "Raja's Seat", "Talakaveri", "Dubare Elephant Camp", "Coffee estate villages"],
        "food": ["Pandi curry (Kodava-style pork curry)", "Akki rotti", "Kadambuttu", "Locally grown coffee"],
        "transport": ["Self-drive/rental cars recommended", "Jeeps for estate/forest routes", "No railway; nearest station Mysuru (~120 km)"],
        "payment_modes": ["UPI in towns", "Cash essential in remote homestays"],
        "network": "Decent 4G in Madikeri town; weak/no signal in coffee estates",
        "stay_types": ["Coffee estate homestays", "Resorts", "Budget lodges"],
        "rating": 4.5, "best_time_to_visit": "October to March",
    },
    "Mangalore-Udupi": {
        "aliases": ["mangalore", "mangaluru", "udupi", "malpe", "coastal karnataka"],
        "district": "Dakshina Kannada / Udupi", "type": "Coastal region",
        "villages_and_places": ["Malpe Beach", "St. Mary's Island", "Udupi Sri Krishna Matha", "Kaup Beach and lighthouse", "Manipal"],
        "food": ["Neer dosa", "Ghee roast", "Fish curry with coconut", "Original Udupi-style vegetarian cuisine"],
        "transport": ["City buses", "Auto-rickshaws", "Ferries to St. Mary's Island (seasonal)", "Airport and railway well connected"],
        "payment_modes": ["UPI widely used", "Cards at restaurants", "Cash for ferries/small stalls"],
        "network": "Strong 4G/5G in Mangalore and Udupi towns",
        "stay_types": ["Beach resorts", "Business hotels", "Budget lodges", "Homestays near Manipal"],
        "rating": 4.5, "best_time_to_visit": "October to February",
    },
    "Gokarna": {
        "aliases": ["gokarna", "kudle", "om beach"],
        "district": "Uttara Kannada", "type": "Temple town and beach village",
        "villages_and_places": ["Gokarna Main Beach", "Kudle Beach", "Om Beach", "Half Moon Beach", "Mahabaleshwar Temple"],
        "food": ["Beach shacks (Indian/Israeli/Western menus)", "Fresh seafood", "Local thalis in town"],
        "transport": ["Walking/trekking trails between beaches", "Auto-rickshaws", "Rented scooters", "Railway station in town"],
        "payment_modes": ["Cash preferred at beach shacks", "UPI at established restaurants/shops"],
        "network": "Moderate 4G in town; weak on remote beach stretches",
        "stay_types": ["Beach huts/shacks", "Backpacker hostels", "Guesthouses", "A few upscale resorts"],
        "rating": 4.4, "best_time_to_visit": "October to March",
    },
    "Badami": {
        "aliases": ["badami", "aihole", "pattadakal"],
        "district": "Bagalkot", "type": "Historic rock-cut cave town",
        "villages_and_places": ["Badami Cave Temples", "Agastya Lake", "Badami Fort", "Aihole", "Pattadakal (UNESCO, nearby)"],
        "food": ["North Karnataka thali: jolada rotti, yennegayi, shenga chutney", "Simple local eateries near cave entrance"],
        "transport": ["Buses from Hubballi/Bagalkot", "Auto-rickshaws locally", "Nearest railway: Badami station", "Car/taxi best for Aihole-Pattadakal circuit"],
        "payment_modes": ["Cash recommended", "UPI in town center"],
        "network": "Moderate 4G in town, weak near caves/rural stretches",
        "stay_types": ["Budget hotels", "A couple of heritage/resort properties", "Homestays"],
        "rating": 4.6, "best_time_to_visit": "October to February",
    },
    "Hubballi-Dharwad": {
        "aliases": ["hubli", "hubballi", "dharwad"],
        "district": "Dharwad", "type": "Twin city, North Karnataka hub",
        "villages_and_places": ["Unkal Lake", "Nrupatunga Betta", "Indi Rocks (near Dharwad)", "Old Dharwad market area"],
        "food": ["Dharwad Peda (GI-tagged sweet)", "Jolada rotti thali", "Girmit (cotton candy)", "Ennegayi"],
        "transport": ["City buses", "Auto-rickshaws", "Well connected by rail and road", "Hubballi airport for domestic flights"],
        "payment_modes": ["UPI widely accepted", "Cash common at local eateries"],
        "network": "Good 4G/5G coverage in both cities",
        "stay_types": ["Business hotels", "Budget lodges", "A few upscale hotels"],
        "rating": 4.3, "best_time_to_visit": "October to February",
    },
    "Bidar": {
        "aliases": ["bidar"],
        "district": "Bidar", "type": "Deccan Sultanate heritage town",
        "villages_and_places": ["Bidar Fort", "Mahmud Gawan Madrasa", "Rangin Mahal", "Bidriware craft workshops (nearby villages)"],
        "food": ["Persian-influenced Deccan cuisine", "Biryani variations", "Kannada-Hyderabadi fusion snacks"],
        "transport": ["Buses from Kalaburagi/Hyderabad", "Auto-rickshaws locally", "Bidar railway station", "Nearest airport: Kalaburagi or Hyderabad"],
        "payment_modes": ["Cash recommended for small vendors/workshops", "UPI in town center"],
        "network": "Moderate 4G, weaker in surrounding villages",
        "stay_types": ["Budget hotels", "A couple of mid-range hotels"],
        "rating": 4.4, "best_time_to_visit": "October to February",
    },
    "Bandipur": {
        "aliases": ["bandipur", "wildlife", "safari"],
        "district": "Chamarajanagar", "type": "National park / wildlife reserve",
        "villages_and_places": ["Bandipur National Park core zone", "Gopalaswamy Betta viewpoint", "Route towards Mudumalai/Ooty"],
        "food": ["Basic forest-lodge meals", "South Indian thalis at highway dhabas"],
        "transport": ["Safari jeeps (booked in advance)", "Cars/buses on Mysuru-Ooty highway", "Nearest station Mysuru (~80 km)"],
        "payment_modes": ["Cash for safari bookings at gate", "Online booking via Karnataka Forest Dept portal recommended"],
        "network": "Weak/no signal inside the reserve; moderate near highway",
        "stay_types": ["Forest department cottages/lodges (advance booking required)", "Private resorts on the highway"],
        "rating": 4.4, "best_time_to_visit": "October to May",
    },
    "Jog Falls": {
        "aliases": ["jog falls", "shimoga", "sagar"],
        "district": "Shivamogga", "type": "Waterfall / scenic village area",
        "villages_and_places": ["Jog Falls viewpoints", "Kargal village", "Linganamakki Dam (nearby)"],
        "food": ["Basic local eateries near the falls", "Malnad-style rice dishes in Shivamogga town"],
        "transport": ["Buses from Shivamogga/Sagar", "Self-drive recommended", "Nearest railway: Talaguppa"],
        "payment_modes": ["Cash strongly recommended, limited digital acceptance"],
        "network": "Weak signal near the falls, moderate in Sagar town",
        "stay_types": ["Basic guesthouses", "A few resorts near Sagar"],
        "rating": 4.3, "best_time_to_visit": "August to October (peak water flow)",
    },
}

CATEGORY_KEYWORDS = {
    "villages_and_places": ["village", "place", "places", "attraction", "visit", "see", "sight"],
    "food": ["food", "cuisine", "eat", "dish", "restaurant", "thali", "snack", "sweet"],
    "transport": ["transport", "bus", "train", "auto", "taxi", "cab", "flight", "airport", "reach", "travel to"],
    "payment_modes": ["payment", "upi", "cash", "card", "pay"],
    "network": ["network", "signal", "internet", "4g", "5g", "wifi", "connectivity"],
    "stay_types": ["stay", "hotel", "resort", "hostel", "homestay", "lodge", "accommodation"],
    "rating": ["rating", "rated", "review", "score", "best region", "recommend"],
    "best_time_to_visit": ["best time", "season", "when to visit", "weather"],
}

SYSTEM_PROMPT = """You are "Karnataka Yatri", a helpful travel assistant that ONLY answers
questions about Karnataka state, India — its regions, villages, places, food,
transportation, payment modes, mobile network coverage, types of stay, and
ratings.

Rules:
- Only use the CONTEXT block provided with each user question as your source of
  facts. If the context doesn't cover something, say so honestly and give only
  general, clearly-labeled travel advice rather than inventing specifics.
- If the user asks about anything unrelated to Karnataka travel, politely
  decline and redirect them to ask about Karnataka instead.
- Keep answers conversational, concise, and organized with short bullet points
  when listing multiple facts.
- Never invent phone numbers, prices, or exact opening hours not in the context.
"""

def find_matching_regions(query):
    q = query.lower()
    return [name for name, info in REGIONS.items()
            if any(alias in q for alias in [name.lower()] + [a.lower() for a in info.get("aliases", [])])]

def find_matching_categories(query):
    q = query.lower()
    return [cat for cat, kws in CATEGORY_KEYWORDS.items() if any(kw in q for kw in kws)]

def build_context(query):
    region_matches = find_matching_regions(query)
    category_matches = find_matching_categories(query)

    if not region_matches and not category_matches:
        summary = {name: {"type": info["type"], "district": info["district"], "rating": info["rating"]}
                   for name, info in REGIONS.items()}
        return "No specific region/category detected. Overview of all regions:\n" + json.dumps(summary, indent=2)

    target_regions = region_matches if region_matches else list(REGIONS.keys())
    context_blob = {}
    for name in target_regions:
        info = REGIONS[name]
        if category_matches:
            context_blob[name] = {cat: info[cat] for cat in category_matches if cat in info}
            context_blob[name]["district"] = info["district"]
            context_blob[name]["type"] = info["type"]
        else:
            context_blob[name] = info
    return json.dumps(context_blob, indent=2)

def ask_ollama(user_query, context, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": f"CONTEXT:\n{context}\n\nUSER QUESTION:\n{user_query}"})

    payload = {"model": MODEL_NAME, "messages": messages, "stream": False}

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return ("⚠️ Couldn't reach Ollama at localhost:11434. Make sure it's running "
                "(`ollama serve`) and the model is pulled (`ollama pull llama3.2:latest`).")
    except requests.exceptions.Timeout:
        return "⚠️ The model took too long to respond. Try a shorter question."
    except Exception as e:
        return f"⚠️ Unexpected error talking to Ollama: {e}"

@app.route("/")
def index():
    return render_template("index.html", regions=sorted(REGIONS.keys()))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"reply": "Please type a question about Karnataka."})

    context = build_context(user_message)
    reply = ask_ollama(user_message, context, history)
    return jsonify({"reply": reply})
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)