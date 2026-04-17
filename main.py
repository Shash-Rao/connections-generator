from generators.semantic import SemanticGenerator
import random
from generators.anagram import AnagramGenerator
from scoring.embedding_scorer import score
from generators.synonym_generator import SynonymGenerator
from scoring.difficulty import assign_difficulties

SEED_SUBJECTS = [
    # ANIMALS
    "animals", "mammals", "birds", "fish", "reptiles", "amphibians",
    "insects", "dogs", "cats", "horses", "cattle", "sheep",
    "goats", "pigs", "rabbits", "rodents", "bears", "wolves",
    "foxes", "deer", "whales", "dolphins", "sharks", "snakes",
    "lizards", "frogs", "turtles", "ducks", "geese", "swans",
    "eagles", "hawks", "owls", "parrots", "penguins",

    # FOOD
    "foods", "fruits", "vegetables", "meats", "seafood",
    "cheeses", "breads", "pastries", "desserts", "cakes",
    "cookies", "pies", "pastas", "noodles", "soups",
    "salads", "sandwiches", "sauces", "spices", "herbs",
    "beverages", "drinks", "teas", "coffees", "juices",
    "sodas", "cocktails", "liquors", "wines", "beers",

    # CLOTHING
    "clothing", "shoes", "boots", "sneakers", "sandals",
    "hats", "caps", "jackets", "coats", "shirts",
    "pants", "shorts", "skirts", "dresses", "suits",
    "uniforms", "socks", "gloves", "scarves", "belts",

    # VEHICLES
    "vehicles", "cars", "trucks", "buses", "vans",
    "motorcycles", "bicycles", "trains", "boats",
    "ships", "airplanes", "helicopters", "taxis",
    "ambulances", "wagons", "sedans", "jeeps",
    "limousines", "canoes", "kayaks", "yachts",

    # HOUSEHOLD / OBJECTS
    "furniture", "chairs", "tables", "desks", "beds",
    "lamps", "mirrors", "couches", "sofas", "cabinets",
    "dressers", "wardrobes", "shelves", "appliances",
    "tools", "instruments", "machines", "devices",
    "gadgets", "utensils", "containers", "bottles",
    "jars", "boxes", "bags", "suitcases", "keys",
    "locks", "clocks", "watches", "knives", "forks",
    "spoons", "plates", "cups", "mugs", "bowls",

    # BUILDINGS / PLACES
    "buildings", "houses", "apartments", "rooms",
    "shops", "stores", "schools", "colleges",
    "universities", "churches", "hospitals",
    "offices", "factories", "warehouses",
    "garages", "barns", "cabins", "cottages",
    "mansions", "villas", "lodges", "hotels",
    "restaurants", "cafes", "bakeries",
    "pharmacies", "libraries", "museums",
    "stadiums", "theaters", "airports",

    # PROFESSIONS (HIGH QUALITY)
    "jobs", "professions", "doctors", "lawyers",
    "scientists", "teachers", "artists", "writers",
    "actors", "musicians", "dancers", "athletes",
    "drivers", "pilots", "engineers", "architects",
    "designers", "builders", "farmers", "chefs",
    "bakers", "detectives", "inspectors",
    "captains", "soldiers", "guards",
    "firefighters", "nurses", "dentists",
    "surgeons", "veterinarians",

    # SPORTS / GAMES
    "sports", "games", "teams", "positions",
    "plays", "moves", "penalties", "trophies",
    "awards", "medals", "ribbons", "prizes",
    "balls", "bats", "rackets", "goals",
    "courts", "tracks", "races", "tournaments",

    # MUSIC / ARTS
    "music", "songs", "dances", "genres",
    "instruments", "bands", "orchestras",
    "choirs", "drums", "guitars", "violins",
    "pianos", "trumpets", "flutes",

    # MEDIA / STORY
    "books", "stories", "novels", "plays",
    "films", "movies", "shows", "series",
    "episodes", "chapters", "scenes",
    "plots", "characters", "heroes", "villains",

    # MATERIALS
    "materials", "metals", "stones", "gems",
    "crystals", "rocks", "minerals", "fabrics",
    "woods", "plastics", "glass", "paper",

    # GEOGRAPHY
    "countries", "states", "cities", "towns",
    "villages", "islands", "continents",
    "oceans", "seas", "rivers", "lakes",
    "mountains", "valleys", "deserts",
    "forests", "jungles", "beaches",

    # TIME
    "times", "hours", "days", "months",
    "years", "decades", "seasons",

    # CLEAN CATEGORY LABELS (VERY USEFUL)
    "types", "styles", "models", "brands",
    "categories", "genres", "flavors",
    "colors", "shapes", "sizes",

    # STRONG ABSTRACT BUT USABLE (LIMITED)
    "emotions", "feelings", "beliefs",
    "crimes", "diseases", "injuries",
    "symptoms", "medicines"
]

if __name__ == "__main__":

    # generator = SemanticGenerator(SEED_SUBJECTS)
    # categories = generator.generate_all_categories()

    # print(f"\nGenerated {len(categories)} categories\n")

    # random.shuffle(categories)

    # for c in categories[:100]:
    #     print(c)

    gen = AnagramGenerator(n_words=200000, min_zipf=3.0, debug=True)

    # Inspect the pool directly
    gen.debug_print_buckets(limit=25)
    gen.debug_print_bucket_scores(limit=25)

    # Build one canonical group per anagram family
    groups = gen.generate_all_canonical_groups()

    print(f"\nCanonical anagram groups before scoring: {len(groups)}")

    # Score and keep only valid groups
    kept = []
    seen_keys = set()

    for group in groups:
        fam_key = group["meta"]["key"]

        if fam_key in seen_keys:
            continue

        seen_keys.add(fam_key)

        s = score(group)
        if s != float("-inf"):
            group["score"] = s
            kept.append(group)

    print(f"Canonical anagram groups after scoring: {len(kept)}")

    if not kept:
        print("\nNo valid groups survived scoring.")
    else:
        kept = assign_difficulties(kept)

        # Print best-scoring groups first
        kept.sort(key=lambda g: g["score"], reverse=True)

        print("\nFinal groups:")
        for g in kept[:20]:
            print(f"\nGroup: {g['category']}")
            print(f"Difficulty: {g['difficulty']}")
            print(f"Score: {g['score']:.3f}")
            print(", ".join(g["words"]))
