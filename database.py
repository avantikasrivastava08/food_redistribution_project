import json, os, uuid
from datetime import datetime

USE_MONGO = False          # ← flip to True when you have MongoDB running
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME   = "foodshare"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "db.json")


def _ts():
    return datetime.now().isoformat(sep=" ", timespec="seconds")

def _new_id():
    return str(uuid.uuid4())[:8]


class _JSONStore:
    """Tiny document store backed by a single JSON file."""

    _SCHEMA = {
        "users": [],
        "donations": [],
        "ngos": [],
        "messages": [],
        "notifications": [],
    }

    def __init__(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            self._save(self._SCHEMA.copy())
        self._seed()

    

    def _load(self):
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)


    def _seed(self):
        db = self._load()
        if db["ngos"]:
            return  # already seeded

        ngos = [
            {"_id": _new_id(), "name": "Feeding India",     "contact": "9876543210", "city": "Delhi",     "registered": _ts()},
            {"_id": _new_id(), "name": "Roti Bank",          "contact": "9812345678", "city": "Mumbai",    "registered": _ts()},
            {"_id": _new_id(), "name": "No Food Waste",      "contact": "9823456789", "city": "Bangalore", "registered": _ts()},
            {"_id": _new_id(), "name": "Akshaya Patra",      "contact": "9834567890", "city": "Hyderabad", "registered": _ts()},
            {"_id": _new_id(), "name": "Robin Hood Army",    "contact": "9845678901", "city": "Chennai",   "registered": _ts()},
        ]
        db["ngos"] = ngos

        # demo users
        users = [
            {"_id": _new_id(), "name": "Priya Sharma",   "role": "donor",     "email": "priya@example.com",   "phone": "9001112222", "location": "Delhi",     "joined": _ts()},
            {"_id": _new_id(), "name": "Rahul Verma",    "role": "volunteer", "email": "rahul@example.com",   "phone": "9002223333", "location": "Delhi",     "joined": _ts()},
            {"_id": _new_id(), "name": "Anita Patel",    "role": "donor",     "email": "anita@example.com",   "phone": "9003334444", "location": "Mumbai",    "joined": _ts()},
            {"_id": _new_id(), "name": "Suresh Kumar",   "role": "volunteer", "email": "suresh@example.com",  "phone": "9004445555", "location": "Bangalore", "joined": _ts()},
        ]
        db["users"] = users

        # demo donations
        statuses = ["available", "available", "picked_up", "delivered", "available"]
        foods    = ["Biryani", "Dal Makhani", "Roti + Sabzi", "Bread & Butter", "Pulao"]
        urgencies = [True, False, False, True, False]
        beneficiaries = ["humans", "humans", "animals", "humans", "both"]
        for i, u in enumerate(users[:2]):
            db["donations"].append({
                "_id":         _new_id(),
                "donor_id":    users[i % 2]["_id"],
                "donor_name":  users[i % 2]["name"],
                "food_item":   foods[i],
                "quantity":    f"{(i+1)*5} portions",
                "status":      statuses[i],
                "urgent":      urgencies[i],
                "beneficiary": beneficiaries[i],
                "location":    users[i % 2]["location"],
                "posted_at":   _ts(),
                "volunteer_id": None,
            })

        self._save(db)


    def find(self, collection, query=None):
        db   = self._load()
        docs = db.get(collection, [])
        if not query:
            return docs
        result = []
        for doc in docs:
            if all(doc.get(k) == v for k, v in query.items()):
                result.append(doc)
        return result

    def find_one(self, collection, query):
        for doc in self.find(collection, query):
            return doc
        return None

    def insert(self, collection, document):
        db = self._load()
        document.setdefault("_id", _new_id())
        db.setdefault(collection, []).append(document)
        self._save(db)
        return document["_id"]

    def update(self, collection, query, update_fields):
        db    = self._load()
        docs  = db.get(collection, [])
        count = 0
        for doc in docs:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update_fields)
                count += 1
        self._save(db)
        return count

    def delete(self, collection, query):
        db   = self._load()
        orig = db.get(collection, [])
        kept = [d for d in orig if not all(d.get(k) == v for k, v in query.items())]
        db[collection] = kept
        self._save(db)
        return len(orig) - len(kept)

    def count(self, collection, query=None):
        return len(self.find(collection, query))


class _MongoStore:
    def __init__(self):
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI)
        self._db = client[DB_NAME]

    def find(self, collection, query=None):
        return list(self._db[collection].find(query or {}, {"_id": 0}))

    def find_one(self, collection, query):
        return self._db[collection].find_one(query, {"_id": 0})

    def insert(self, collection, document):
        document.setdefault("_id", _new_id())
        self._db[collection].insert_one(document)
        return document["_id"]

    def update(self, collection, query, update_fields):
        r = self._db[collection].update_many(query, {"$set": update_fields})
        return r.modified_count

    def delete(self, collection, query):
        r = self._db[collection].delete_many(query)
        return r.deleted_count

    def count(self, collection, query=None):
        return self._db[collection].count_documents(query or {})



db: _JSONStore | _MongoStore = _MongoStore() if USE_MONGO else _JSONStore()
