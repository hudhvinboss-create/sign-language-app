"""
Sign Language Database Module
Handles SQLite operations for dictionary, translation history, and settings.
Includes data from Gallaudet Dictionary, ASL/BSL/SASL/Makaton resources.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "signs.db")

class SignDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'ASL',
                category TEXT NOT NULL,
                meaning TEXT NOT NULL,
                hand_position TEXT,
                movement TEXT,
                example_sentence TEXT,
                related_signs TEXT,
                image_path TEXT,
                confidence_threshold REAL DEFAULT 0.7
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_type TEXT NOT NULL,
                input_data TEXT,
                translated_text TEXT NOT NULL,
                confidence REAL,
                language TEXT DEFAULT 'ASL'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                description TEXT,
                url TEXT,
                language TEXT,
                pages INTEGER,
                category TEXT,
                format TEXT DEFAULT 'PDF'
            )
        """)

        conn.commit()
        self._seed_data(cursor)
        self._seed_resources(cursor)
        conn.commit()
        conn.close()

    def _seed_data(self, cursor):
        cursor.execute("SELECT COUNT(*) FROM signs")
        if cursor.fetchone()[0] > 0:
            return

        signs = [
            # ========== GREETINGS ==========
            ("HELLO", "ASL", "Greetings", "A greeting used when meeting someone.", 
             "Hand open, fingers spread, thumb extended. Hand at side of forehead.",
             "Move hand outward from forehead in a small arc, like a salute.",
             "Hello, nice to meet you!", "HI, GOODBYE, MORNING", None, 0.75),
            ("HI", "ASL", "Greetings", "An informal greeting.",
             "Hand open, palm facing outward.",
             "Small upward movement of the hand.",
             "Hi, how are you?", "HELLO, HEY, WHAT'S-UP", None, 0.75),
            ("GOODBYE", "ASL", "Greetings", "Used when parting from someone.",
             "Hand open, palm facing outward.",
             "Move hand side to side like waving.",
             "Goodbye, see you tomorrow!", "HELLO, SEE-YOU, BYE", None, 0.75),
            ("GOOD-MORNING", "ASL", "Greetings", "Wishing someone well at the start of the day.",
             "Flat hand at chin, then arc down to stomach.",
             "Move hand from chin downward in an arc.",
             "Good morning! Did you sleep well?", "HELLO, MORNING", None, 0.75),
            ("GOOD-NIGHT", "ASL", "Greetings", "Wishing someone well before sleep.",
             "Flat hand at chin, then move to bent hand at forehead.",
             "Chin to forehead, closing fingers like going to sleep.",
             "Good night, sweet dreams!", "GOODBYE, SLEEP", None, 0.75),

            # ========== COMMON PHRASES ==========
            ("THANK-YOU", "ASL", "Common phrases", "Expression of gratitude.",
             "Flat hand touching chin, fingers pointing forward.",
             "Move hand forward and slightly downward from chin.",
             "Thank you for your help.", "THANKS, WELCOME, GRATEFUL", None, 0.75),
            ("PLEASE", "ASL", "Common phrases", "Polite request.",
             "Flat hand on chest, moving in circular motion.",
             "Rub chest in circular motion with flat hand.",
             "Please pass the salt.", "THANK-YOU, SORRY, EXCUSE-ME", None, 0.75),
            ("SORRY", "ASL", "Common phrases", "Apology expression.",
             "Fist hand, rub in circular motion on chest.",
             "Circular rubbing motion on chest with fist.",
             "I am sorry for being late.", "PLEASE, APOLOGIZE, FORGIVE", None, 0.75),
            ("EXCUSE-ME", "ASL", "Common phrases", "Polite way to get attention or apologize.",
             "A-handshape, brush twice on inner edge of non-dominant hand.",
             "Brush A-handshape twice on palm of other hand.",
             "Excuse me, can I get through?", "SORRY, PLEASE", None, 0.75),
            ("YES", "ASL", "Common phrases", "Affirmative response.",
             "Closed fist, nod up and down like a head nod.",
             "Move fist up and down in nodding motion.",
             "Yes, I agree with you.", "NO, MAYBE, AGREE", None, 0.75),
            ("NO", "ASL", "Common phrases", "Negative response.",
             "Index and middle fingers together, thumb touching them. Open like scissors.",
             "Tap index and middle fingers to thumb, then open.",
             "No, I do not want that.", "YES, NOT, NEVER", None, 0.75),
            ("MAYBE", "ASL", "Common phrases", "Uncertain or possible response.",
             "Both hands with palms up, alternate moving up and down.",
             "Move both open hands alternately up and down.",
             "Maybe I will come tomorrow.", "YES, NO, PERHAPS", None, 0.75),
            ("WELCOME", "ASL", "Common phrases", "Response to thanks.",
             "B-handshape from chin, move outward and down.",
             "Move B-hand outward from chin in arc.",
             "You are welcome!", "THANK-YOU, PLEASE", None, 0.75),

            # ========== FAMILY ==========
            ("MOTHER", "ASL", "Family", "Female parent.",
             "Open hand, thumb touching chin.",
             "Tap thumb on chin twice.",
             "My mother is kind.", "FATHER, PARENT, MOM", None, 0.75),
            ("FATHER", "ASL", "Family", "Male parent.",
             "Open hand, thumb touching forehead.",
             "Tap thumb on forehead twice.",
             "My father works hard.", "MOTHER, PARENT, DAD", None, 0.75),
            ("FAMILY", "ASL", "Family", "Group of related people.",
             "F-hands touching at tips, then circle outward.",
             "Circle both F-hands outward from center.",
             "My family is large.", "MOTHER, FATHER, BROTHER", None, 0.75),
            ("BROTHER", "ASL", "Family", "Male sibling.",
             "L-hands: one at forehead (boy), one at chest (same).",
             "Sign BOY + SAME combined.",
             "My brother is tall.", "SISTER, SIBLING", None, 0.75),
            ("SISTER", "ASL", "Family", "Female sibling.",
             "L-hands: one at chin (girl), one at chest (same).",
             "Sign GIRL + SAME combined.",
             "My sister is smart.", "BROTHER, SIBLING", None, 0.75),
            ("BABY", "ASL", "Family", "Very young child.",
             "Arms cradled, rock back and forth.",
             "Rock arms back and forth like holding a baby.",
             "The baby is sleeping.", "CHILD, INFANT", None, 0.75),
            ("CHILD", "ASL", "Family", "Young person.",
             "Pat chest twice with open hand, then show height.",
             "Pat chest, then indicate small height with hand.",
             "The child is playing.", "BABY, KID, ADULT", None, 0.75),
            ("GRANDMOTHER", "ASL", "Family", "Mother's or father's mother.",
             "Sign MOTHER, then bounce hand upward twice.",
             "MOTHER sign with bouncing motion upward.",
             "My grandmother bakes cookies.", "GRANDFATHER, GRANDPARENT", None, 0.75),
            ("GRANDFATHER", "ASL", "Family", "Mother's or father's father.",
             "Sign FATHER, then bounce hand upward twice.",
             "FATHER sign with bouncing motion upward.",
             "My grandfather tells stories.", "GRANDMOTHER, GRANDPARENT", None, 0.75),

            # ========== MEDICAL ==========
            ("HOSPITAL", "ASL", "Medical", "Place for medical treatment.",
             "H-hand tapping on opposite wrist twice.",
             "Tap H-hand on wrist twice.",
             "I need to go to the hospital.", "DOCTOR, MEDICINE, CLINIC", None, 0.75),
            ("DOCTOR", "ASL", "Medical", "Medical professional.",
             "D-hand tapping on inner wrist twice.",
             "Tap D-hand on inner wrist twice.",
             "The doctor will see you now.", "HOSPITAL, NURSE, SURGEON", None, 0.75),
            ("MEDICINE", "ASL", "Medical", "Substance used for treatment.",
             "Middle finger touches left palm, then twist wrist.",
             "Touch palm and twist wrist.",
             "Take your medicine.", "HOSPITAL, DOCTOR, PILL", None, 0.75),
            ("SICK", "ASL", "Medical", "Not feeling well.",
             "Middle fingers of both hands at stomach, move outward.",
             "Touch stomach with both middle fingers, then pull outward.",
             "I feel sick today.", "HEALTHY, PAIN, HURT", None, 0.75),
            ("PAIN", "ASL", "Medical", "Physical discomfort.",
             "Index fingers pointing at each other, twist in opposite directions.",
             "Twist index fingers in opposite directions near affected area.",
             "I have pain in my head.", "SICK, HURT, ACHE", None, 0.75),
            ("HELP", "ASL", "Medical", "Assistance needed.",
             "Right hand on top of left fist, lift upward.",
             "Lift right hand from left fist upward.",
             "Help me, please!", "EMERGENCY, SAVE, ASSIST", None, 0.75),
            ("EMERGENCY", "ASL", "Medical", "Urgent situation.",
             "Both E-hands, palms facing body, move outward.",
             "Move both E-hands outward from chest.",
             "This is an emergency!", "HELP, DANGER, URGENT", None, 0.75),
            ("NURSE", "ASL", "Medical", "Healthcare assistant.",
             "N-hand at shoulder, tap twice.",
             "Tap N-hand on shoulder twice.",
             "The nurse is kind.", "DOCTOR, HOSPITAL", None, 0.75),

            # ========== EMERGENCY ==========
            ("FIRE", "ASL", "Emergency", "Dangerous burning.",
             "Fingers wiggling upward from palm, like flames.",
             "Wiggle fingers upward from open palm.",
             "Fire! Call emergency services!", "BURN, HOT, EMERGENCY", None, 0.75),
            ("POLICE", "ASL", "Emergency", "Law enforcement officer.",
             "C-hand at chest, tap twice.",
             "Tap C-hand on chest twice (from badge shape).",
             "Call the police!", "OFFICER, LAW, EMERGENCY", None, 0.75),
            ("STOP", "ASL", "Emergency", "Cease movement or action.",
             "One hand flat, palm facing out, move forward sharply.",
             "Push flat palm forward firmly.",
             "Stop! Do not move!", "WAIT, HALT, NO", None, 0.75),
            ("DANGER", "ASL", "Emergency", "Risk of harm.",
             "X-hands crossed, move apart sharply.",
             "Cross X-hands then pull apart quickly.",
             "Danger! Stay back!", "WARNING, EMERGENCY, CAUTION", None, 0.75),

            # ========== FOOD ==========
            ("WATER", "ASL", "Food", "Clear liquid essential for life.",
             "W-hand at chin, tap index finger.",
             "Tap W-hand on chin.",
             "I need water.", "DRINK, FOOD, THIRSTY", None, 0.75),
            ("FOOD", "ASL", "Food", "Substance eaten for nutrition.",
             "Fingertips together, touch mouth twice.",
             "Touch fingertips to mouth twice.",
             "The food is delicious.", "EAT, WATER, MEAL", None, 0.75),
            ("EAT", "ASL", "Food", "To consume food.",
             "O-hand to mouth, close and open.",
             "Bring O-hand to mouth and open.",
             "I want to eat.", "FOOD, HUNGRY, MEAL", None, 0.75),
            ("DRINK", "ASL", "Food", "To consume liquid.",
             "C-hand at mouth, tilt back like drinking from cup.",
             "Tilt C-hand at mouth like drinking.",
             "I want to drink juice.", "WATER, THIRSTY", None, 0.75),
            ("HUNGRY", "ASL", "Food", "Needing food.",
             "C-hand at stomach, move down in circular motion.",
             "Circle C-hand down from stomach.",
             "I am hungry.", "EAT, FOOD, FULL", None, 0.75),
            ("BREAD", "ASL", "Food", "Baked food made from flour.",
             "Both hands slice imaginary bread with knife motion.",
             "Sawing motion with both hands like slicing bread.",
             "I want bread with butter.", "FOOD, EAT, SANDWICH", None, 0.75),
            ("MILK", "ASL", "Food", "White liquid from cows.",
             "Squeeze imaginary udder with both hands alternately.",
             "Alternate squeezing motion with both fists.",
             "I drink milk every morning.", "DRINK, WATER, FOOD", None, 0.75),
            ("COFFEE", "ASL", "Food", "Hot caffeinated beverage.",
             "F-hands, one on top of other, twist like grinding coffee.",
             "Twist F-hands in grinding motion.",
             "I need coffee.", "DRINK, TEA, HOT", None, 0.75),
            ("APPLE", "ASL", "Food", "Round red or green fruit.",
             "Knuckle of index finger at cheek, twist.",
             "Twist knuckle on cheek like checking apple firmness.",
             "I ate an apple.", "FRUIT, FOOD, EAT", None, 0.75),

            # ========== NUMBERS ==========
            ("ONE", "ASL", "Numbers", "Number 1.",
             "Index finger extended upward.",
             "Hold index finger up.",
             "I have one apple.", "TWO, THREE, FIRST", None, 0.75),
            ("TWO", "ASL", "Numbers", "Number 2.",
             "Index and middle fingers extended.",
             "Hold two fingers up.",
             "I have two cats.", "ONE, THREE, SECOND", None, 0.75),
            ("THREE", "ASL", "Numbers", "Number 3.",
             "Index, middle, and ring fingers extended.",
             "Hold three fingers up.",
             "Three people are here.", "ONE, TWO, THIRD", None, 0.75),
            ("FOUR", "ASL", "Numbers", "Number 4.",
             "All four fingers extended, thumb tucked.",
             "Hold four fingers up with thumb tucked.",
             "I have four books.", "FIVE, THREE", None, 0.75),
            ("FIVE", "ASL", "Numbers", "Number 5.",
             "All five fingers extended (open hand).",
             "Hold open hand with all fingers spread.",
             "I have five fingers.", "FOUR, SIX", None, 0.75),
            ("TEN", "ASL", "Numbers", "Number 10.",
             "Shake A-handshape (thumb out) with twisting motion.",
             "Shake A-handshape with thumb flicking.",
             "I have ten dollars.", "FIVE, TWENTY", None, 0.75),
            ("HUNDRED", "ASL", "Numbers", "Number 100.",
             "C-handshape, palm facing signer, move in small arc.",
             "Move C-hand in small arc.",
             "One hundred people came.", "THOUSAND, MANY", None, 0.75),

            # ========== ALPHABET ==========
            ("A", "ASL", "Alphabet", "Letter A.",
             "Fist with thumb on side of fingers.",
             "Hold fist steady.",
             "A is the first letter.", "B, C", None, 0.75),
            ("B", "ASL", "Alphabet", "Letter B.",
             "Flat hand, fingers together, thumb tucked.",
             "Hold palm facing outward.",
             "B is the second letter.", "A, C", None, 0.75),
            ("C", "ASL", "Alphabet", "Letter C.",
             "Hand curved in C shape.",
             "Hold C shape steady.",
             "C is the third letter.", "A, B", None, 0.75),
            ("D", "ASL", "Alphabet", "Letter D.",
             "Index finger up, thumb and middle finger touch to form circle.",
             "Hold D-handshape steady.",
             "D is the fourth letter.", "C, E", None, 0.75),
            ("E", "ASL", "Alphabet", "Letter E.",
             "All fingers curled in, thumb across fingertips.",
             "Hold E-handshape steady.",
             "E is the fifth letter.", "D, F", None, 0.75),
            ("F", "ASL", "Alphabet", "Letter F.",
             "Index and thumb touch, other fingers extended up.",
             "Hold OK-sign with other fingers up.",
             "F is the sixth letter.", "E, G", None, 0.75),
            ("I", "ASL", "Alphabet", "Letter I.",
             "Pinky finger extended, other fingers closed into fist.",
             "Hold pinky up.",
             "I love you.", "J, L", None, 0.75),
            ("L", "ASL", "Alphabet", "Letter L.",
             "Index finger and thumb extended in L shape.",
             "Hold L-handshape steady.",
             "L is for love.", "I, K", None, 0.75),
            ("R", "ASL", "Alphabet", "Letter R.",
             "Crossed fingers: index over middle.",
             "Hold crossed fingers steady.",
             "R is the eighteenth letter.", "P, S", None, 0.75),
            ("S", "ASL", "Alphabet", "Letter S.",
             "Fist with thumb over fingers.",
             "Hold fist with thumb wrapped over.",
             "S is for sign.", "R, T", None, 0.75),
            ("W", "ASL", "Alphabet", "Letter W.",
             "Index, middle, and ring fingers extended, thumb and pinky tucked.",
             "Hold three middle fingers up.",
             "W is for water.", "V, X", None, 0.75),
            ("Y", "ASL", "Alphabet", "Letter Y.",
             "Pinky and thumb extended, other fingers closed.",
             "Hold hang-loose sign.",
             "Y is for yes.", "X, Z", None, 0.75),

            # ========== COMMON PHRASES ==========
            ("HOW-ARE-YOU", "ASL", "Common phrases", "Asking about someone's well-being.",
             "Both hands with bent fingers, palms up, move outward.",
             "Move both hands outward from chest.",
             "How are you today?", "HELLO, FINE, YOU", None, 0.75),
            ("I-LOVE-YOU", "ASL", "Common phrases", "Expression of deep affection.",
             "I-L-Y handshape: pinky, index, thumb extended.",
             "Hold I-L-Y handshape at chest, move outward.",
             "I love you very much.", "LOVE, LIKE, FRIEND", None, 0.75),
            ("GOOD", "ASL", "Common phrases", "Positive quality.",
             "Flat hand from chin, move forward and down.",
             "Move flat hand from chin outward.",
             "That is good!", "BAD, GREAT, FINE", None, 0.75),
            ("BAD", "ASL", "Common phrases", "Negative quality.",
             "Flat hand under chin, flip outward.",
             "Flip flat hand outward from under chin.",
             "That is bad.", "GOOD, WRONG", None, 0.75),
            ("FINE", "ASL", "Common phrases", "Satisfactory or well.",
             "Thumbs up at chest, move slightly upward.",
             "Give thumbs up.",
             "I am fine, thank you.", "GOOD, WELL, OKAY", None, 0.75),
            ("WHERE", "ASL", "Common phrases", "Questioning location.",
             "Index fingers pointing outward, shake side to side.",
             "Shake both index fingers side to side.",
             "Where is the bathroom?", "WHAT, WHO, WHEN", None, 0.75),
            ("WHAT", "ASL", "Common phrases", "Questioning identity or nature.",
             "Index fingers extended, palms up, move both hands outward.",
             "Move both open hands outward with questioning expression.",
             "What is your name?", "WHERE, WHO, WHY", None, 0.75),
            ("WHO", "ASL", "Common phrases", "Questioning person identity.",
             "L-hand at chin, move outward in arc.",
             "Move L-hand from chin outward.",
             "Who is that person?", "WHAT, WHERE, WHICH", None, 0.75),
            ("WHY", "ASL", "Common phrases", "Questioning reason.",
             "Index finger at forehead, flick outward.",
             "Touch forehead with index finger, then flick outward.",
             "Why are you late?", "WHAT, HOW, BECAUSE", None, 0.75),
            ("HOW", "ASL", "Common phrases", "Questioning manner or method.",
             "Both hands with bent fingers, palms up, alternate moving up and down.",
             "Move both hands alternately up and down.",
             "How do you sign this?", "WHAT, WHY, WHERE", None, 0.75),
            ("NAME", "ASL", "Common phrases", "What someone is called.",
             "H-hands: tap index and middle fingers of both hands together twice.",
             "Tap H-hands together twice.",
             "My name is John.", "CALLED, WHO, WHAT", None, 0.75),
            ("NICE-TO-MEET-YOU", "ASL", "Common phrases", "Pleasant first encounter.",
             "Flat hands together, then move outward in arc.",
             "Press palms together then arc outward.",
             "Nice to meet you!", "HELLO, WELCOME", None, 0.75),

            # ========== SCHOOL/WORK ==========
            ("SCHOOL", "ASL", "School", "Place of learning.",
             "Clap hands together twice (like clapping erasers).",
             "Clap open hands together twice.",
             "I go to school.", "LEARN, STUDENT, CLASS", None, 0.75),
            ("LEARN", "ASL", "School", "To acquire knowledge.",
             "Flat hand at forehead, pull down to palm of other hand.",
             "Move hand from forehead down to other palm.",
             "I want to learn ASL.", "STUDY, SCHOOL, KNOW", None, 0.75),
            ("TEACHER", "ASL", "School", "Person who teaches.",
             "Sign LEARN + PERSON (flat hand down from chin).",
             "Learn sign followed by person indicator.",
             "My teacher is patient.", "PROFESSOR, INSTRUCTOR", None, 0.75),
            ("STUDENT", "ASL", "School", "Person who learns.",
             "Sign LEARN + PERSON.",
             "Learn sign followed by person indicator.",
             "The student studies hard.", "LEARN, PUPIL", None, 0.75),
            ("BOOK", "ASL", "School", "Written pages bound together.",
             "Open hands together, then open like a book.",
             "Open hands from together to apart like opening book.",
             "I read a book.", "READ, PAGE, LIBRARY", None, 0.75),
            ("WRITE", "ASL", "School", "To mark paper with pen.",
             "I-handshape, move like writing on palm of other hand.",
             "Make writing motion on palm.",
             "I need to write a letter.", "PEN, PAPER, TYPE", None, 0.75),
            ("WORK", "ASL", "Work", "To do a job.",
             "S-hands, tap together twice.",
             "Tap S-hands together twice.",
             "I go to work.", "JOB, BUSINESS, EMPLOY", None, 0.75),
            ("MONEY", "ASL", "Work", "Currency for exchange.",
             "Rub thumb and fingers together in circular motion.",
             "Rub fingertips together like counting coins.",
             "I need money.", "CASH, PAY, DOLLAR", None, 0.75),

            # ========== TRAVEL ==========
            ("CAR", "ASL", "Travel", "Motor vehicle.",
             "S-hands at chest, move in steering motion.",
             "Move S-hands like steering a wheel.",
             "I drive a car.", "DRIVE, VEHICLE, TRUCK", None, 0.75),
            ("HOME", "ASL", "Travel", "Place where one lives.",
             "Flat hand at mouth, then move to palm of other hand.",
             "Touch mouth then place hand on other palm.",
             "I am going home.", "HOUSE, LIVE, PLACE", None, 0.75),
            ("GO", "ASL", "Travel", "To move from one place to another.",
             "Index fingers together, move forward in arc.",
             "Move both index fingers forward together.",
             "Let's go!", "LEAVE, COME, WALK", None, 0.75),
            ("COME", "ASL", "Travel", "To move toward speaker.",
             "Both hands beckoning inward.",
             "Beckon with both hands toward yourself.",
             "Come here, please.", "GO, HERE, ARRIVE", None, 0.75),
            ("WALK", "ASL", "Travel", "To move on foot.",
             "Both index and middle fingers walking on palm of other hand.",
             "Walk two fingers across palm.",
             "I walk to school.", "RUN, GO, FOOT", None, 0.75),
            ("BUS", "ASL", "Travel", "Public transport vehicle.",
             "B-hands at chest, move forward while shaking.",
             "Move B-hands forward with slight shake.",
             "I take the bus.", "CAR, TRAIN, RIDE", None, 0.75),

            # ========== EMOTIONS ==========
            ("HAPPY", "ASL", "Emotions", "Feeling joy.",
             "Flat hand at chest, move upward in circular motion.",
             "Circle flat hand upward from chest.",
             "I am happy today.", "SAD, JOY, GLAD", None, 0.75),
            ("SAD", "ASL", "Emotions", "Feeling sorrow.",
             "Both hands at face, move downward.",
             "Move both hands down from face.",
             "I feel sad.", "HAPPY, CRY, UPSET", None, 0.75),
            ("ANGRY", "ASL", "Emotions", "Feeling rage.",
             "Claw hands at stomach, move upward sharply.",
             "Pull claw hands up from stomach.",
             "Do not be angry.", "MAD, FRUSTRATED", None, 0.75),
            ("LOVE", "ASL", "Emotions", "Deep affection.",
             "Cross arms over chest, hug yourself.",
             "Cross arms and hug chest.",
             "I love my family.", "LIKE, ADORE, CARE", None, 0.75),
            ("SCARED", "ASL", "Emotions", "Feeling fear.",
             "Both hands at chest, move outward while opening fingers.",
             "Flap hands outward from chest like startled.",
             "I am scared of spiders.", "AFRAID, FEAR, NERVOUS", None, 0.75),
            ("TIRED", "ASL", "Emotions", "Needing rest.",
             "Flat hands at chest, droop downward.",
             "Let hands droop down from chest.",
             "I am very tired.", "SLEEP, EXHAUSTED", None, 0.75),

            # ========== ANIMALS ==========
            ("DOG", "ASL", "Animals", "Common pet animal.",
             "Pat thigh, then snap fingers or clap.",
             "Pat leg then snap fingers (calling a dog).",
             "I have a dog.", "CAT, PET, PUPPY", None, 0.75),
            ("CAT", "ASL", "Animals", "Common pet animal.",
             "Fingers spread at cheeks, pull outward like whiskers.",
             "Pull fingers from cheeks outward like whiskers.",
             "The cat is sleeping.", "DOG, KITTEN, PET", None, 0.75),
            ("BIRD", "ASL", "Animals", "Flying animal.",
             "Thumbs at armpits, flap hands like wings.",
             "Flap hands at sides like bird wings.",
             "The bird is flying.", "FLY, WING, EAGLE", None, 0.75),
            ("FISH", "ASL", "Animals", "Swimming animal.",
             "One hand flat, wiggle side to side like a fish.",
             "Wiggle flat hand side to side.",
             "I see a fish.", "SWIM, WATER, SHARK", None, 0.75),

            # ========== COLORS ==========
            ("RED", "ASL", "Colors", "Color of blood.",
             "Index finger at lip, pull down.",
             "Brush index finger down from bottom lip.",
             "The apple is red.", "COLOR, PINK, ORANGE", None, 0.75),
            ("BLUE", "ASL", "Colors", "Color of sky.",
             "B-handshape, shake side to side.",
             "Shake B-hand side to side.",
             "The sky is blue.", "COLOR, GREEN, PURPLE", None, 0.75),
            ("GREEN", "ASL", "Colors", "Color of grass.",
             "G-handshape, shake side to side.",
             "Shake G-hand side to side.",
             "The grass is green.", "BLUE, YELLOW, BROWN", None, 0.75),
            ("BLACK", "ASL", "Colors", "Darkest color.",
             "Index finger across forehead from left to right.",
             "Draw line across forehead with index finger.",
             "The cat is black.", "WHITE, DARK, COLOR", None, 0.75),
            ("WHITE", "ASL", "Colors", "Lightest color.",
             "W-hand at chest, pull outward.",
             "Pull W-hand outward from chest.",
             "The paper is white.", "BLACK, LIGHT, COLOR", None, 0.75),

            # ========== TIME ==========
            ("TODAY", "ASL", "Time", "The present day.",
             "Both flat hands at chest, move downward together.",
             "Move both flat hands down from chest.",
             "Today is Monday.", "NOW, DAY, YESTERDAY", None, 0.75),
            ("TOMORROW", "ASL", "Time", "The day after today.",
             "A-hand at cheek, move forward and arc down.",
             "Move A-hand from cheek forward in arc.",
             "I will go tomorrow.", "TODAY, FUTURE, LATER", None, 0.75),
            ("YESTERDAY", "ASL", "Time", "The day before today.",
             "A-hand at cheek, move backward and arc down.",
             "Move A-hand from cheek backward in arc.",
             "I went yesterday.", "TODAY, PAST, BEFORE", None, 0.75),
            ("NOW", "ASL", "Time", "At the present moment.",
             "Y-hands, drop downward sharply.",
             "Drop both Y-hands downward.",
             "I want it now.", "TODAY, IMMEDIATE", None, 0.75),
            ("MORNING", "ASL", "Time", "Early part of the day.",
             "Flat hand at stomach, arc up to chest.",
             "Arc flat hand upward from stomach to chest.",
             "I wake up in the morning.", "NIGHT, AFTERNOON, DAY", None, 0.75),
            ("NIGHT", "ASL", "Time", "Dark time of day.",
             "Bent hand over face, close fingers.",
             "Bend hand over face and close fingers like night falling.",
             "The stars come out at night.", "MORNING, EVENING, DARK", None, 0.75),

            # ========== BSL SIGNS (British Sign Language) ==========
            ("HELLO", "BSL", "Greetings", "Greeting in British Sign Language.",
             "Flat hand at temple, move outward in small arc.",
             "Move flat hand outward from temple.",
             "Hello, how are you?", "GOODBYE, HI", None, 0.75),
            ("THANK-YOU", "BSL", "Common phrases", "Gratitude in BSL.",
             "Flat hand at chin, move forward and down.",
             "Move flat hand from chin forward.",
             "Thank you very much.", "PLEASE, SORRY", None, 0.75),
            ("GOOD", "BSL", "Common phrases", "Positive quality in BSL.",
             "Flat hand at mouth, move down to chest.",
             "Move flat hand from mouth to chest.",
             "That is good.", "BAD, FINE", None, 0.75),

            # ========== ISL SIGNS (Indian Sign Language) ==========
            ("HELLO", "ISL", "Greetings", "Greeting in Indian Sign Language.",
             "Both hands wave with palms outward.",
             "Wave both hands with palms facing outward.",
             "Hello, namaste!", "GOODBYE, HI", None, 0.75),
            ("THANK-YOU", "ISL", "Common phrases", "Gratitude in ISL.",
             "Flat hand at lips, move forward.",
             "Move flat hand from lips forward.",
             "Thank you, dhanyavaad.", "PLEASE, SORRY", None, 0.75),
        ]

        cursor.executemany("""
            INSERT INTO signs (word, language, category, meaning, hand_position, 
                             movement, example_sentence, related_signs, image_path, 
                             confidence_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, signs)

    def _seed_resources(self, cursor):
        """Seed external learning resources."""
        cursor.execute("SELECT COUNT(*) FROM resources")
        if cursor.fetchone()[0] > 0:
            return

        resources = [
            ("Simplified Signs: A Manual Sign-Communication System", 
             "John D. Bonvillian, Nicole Kissane Lee, Tracy T. Dooley, Filip T. Loncke",
             "Comprehensive system for teaching sign communication to people with intellectual disabilities, cerebral palsy, autism, or aphasia. Covers principles, research, and application of simplified manual signs.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 652, "Special Populations", "PDF"),
            ("Let's Chat! American Sign Language (ASL)",
             "Amber Hoye, Kelly Arispe, Thais Lacar",
             "Massive collection of ASL conversation activities from Boise State University, covering Levels 1-4 for face-to-face and online instruction. Includes warm-ups, main activities, and assessments.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 1199, "Education", "PDF"),
            ("American Sign Language The Easy Way",
             "David A. Stewart",
             "Complete ASL course covering fingerspelling, grammar, facial expressions, dialogues, Deaf culture, and sports vocabulary. Includes exercises, review sections, and a comprehensive index.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 553, "Beginner", "PDF"),
            ("Sign Languages and the Common European Framework of Reference for Languages",
             "Lorraine Leeson, Beppie van den Bogaerde, Christian Rathmann",
             "European standards for sign language proficiency aligned with CEFR levels. Developed by the PRO-Sign project at the European Centre for Modern Languages.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "Multiple", 55, "Standards", "PDF"),
            ("Create a World of Deaf Readers: Standards for Sign Language Storybooks",
             "Chris Kurz, Truc Nguyen",
             "Standards for creating sign language storybooks for deaf children in underserved communities. Developed by RIT/NTID with USAID support.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "Multiple", 115, "Education", "PDF"),
            ("SASL: A Teacher, Friend & Family Resource for Beginners",
             "Wits University",
             "South African Sign Language vocabulary kit with 300+ signs organized by 27 themes. Includes illustrated sign guides for animals, food, family, emotions, and more with multilingual support.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "SASL", 336, "Beginner", "PDF"),
            ("ASL Worksheets Collection",
             "JuicyEnglish.com",
             "Collection of ASL worksheets covering alphabet, numbers, pronouns, starter signs, everyday statements, and sentence building. Designed for classroom use with matching exercises.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 69, "Education", "PDF"),
            ("ASL Picture Book for Better Communication in the Classroom",
             "Denis Dedic et al.",
             "Visual guide to ASL basics including the alphabet, fingerspelling rules, grammar, numbers, days, everyday signs, classroom vocabulary, verbs, and adjectives. Designed as an 8-day learning program.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 16, "Beginner", "PDF"),
            ("The Gallaudet Dictionary of American Sign Language",
             "Clayton Valli (Editor)",
             "Comprehensive ASL dictionary with 3,000+ signs illustrated with clear directional drawings. Published by Gallaudet University Press. Includes classifiers guide and fingerspelling reference.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 601, "Dictionary", "PDF"),
            ("Sutton's American Sign Language Picture Dictionary",
             "Valerie Sutton",
             "Visual ASL dictionary written in SignWriting notation with colorful illustrations for each sign. Creative Commons licensed. Organized using the Sign-Symbol-Sequence ordering system.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 148, "Dictionary", "PDF"),
            ("American Sign Language for Communication: New York State Teacher's Guide",
             "New York State Education Department",
             "Teacher's guide for developing ASL curricula in schools. Covers communication proficiency, Deaf culture appreciation, learning outcomes, and program setup guidelines.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 64, "Education", "PDF"),
            ("Sign Language Vocab Cards",
             "Arlington Public Schools",
             "Flashcards with 59 common first words in ASL. Includes pictures with signs on the back, designed for teaching vocabulary to young children.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 21, "Beginner", "PDF"),
            ("The Magic of Signing Songs",
             "Nellie Edge",
             "Guide to using ASL songs for enhancing children's language, literacy, and engagement. Covers ABC phonics with sign language, multisensory learning, and parent communication strategies.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "ASL", 37, "Education", "PDF"),
            ("Let's Sign: BSL Guide for Supporting Children's Language Development",
             "Oxfordshire County Council",
             "Practical BSL sign guide for supporting children's language development. Organized by categories including general signs, common objects, actions, animals, food, and people.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "BSL", 18, "Beginner", "PDF"),
            ("What is Sign Language?",
             "Linguistic Society of America",
             "Concise overview explaining why sign languages are true languages. Covers ASL grammar, how it differs from English, and the global diversity of sign languages.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "Multiple", 2, "Reference", "PDF"),
            ("Makaton Sign Language for Children's Services",
             "University Hospitals Coventry and Warwickshire",
             "Illustrated Makaton sign guide for healthcare and educational settings. Covers greetings, family, medical terms, daily routines, food, animals, and transport.",
             "https://infobooks.org/free-pdf-books/various-topics/sign-language/",
             "Makaton", 27, "Medical", "PDF"),
        ]

        cursor.executemany("""
            INSERT INTO resources (title, author, description, url, language, pages, category, format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, resources)

    def search_signs(self, query, language="ASL", category=None):
        conn = self._connect()
        cursor = conn.cursor()

        if category and category != "All":
            cursor.execute("""
                SELECT * FROM signs 
                WHERE (word LIKE ? OR meaning LIKE ?) 
                AND language = ? AND category = ?
                ORDER BY word
            """, (f"%{query}%", f"%{query}%", language, category))
        else:
            cursor.execute("""
                SELECT * FROM signs 
                WHERE (word LIKE ? OR meaning LIKE ?) 
                AND language = ?
                ORDER BY word
            """, (f"%{query}%", f"%{query}%", language))

        results = cursor.fetchall()
        conn.close()
        return results

    def get_sign_by_word(self, word, language="ASL"):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM signs WHERE word = ? AND language = ?
        """, (word.upper(), language))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_categories(self, language="ASL"):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category FROM signs WHERE language = ? ORDER BY category
        """, (language,))
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_signs(self, language="ASL", category=None):
        conn = self._connect()
        cursor = conn.cursor()

        if category and category != "All":
            cursor.execute("""
                SELECT * FROM signs WHERE language = ? AND category = ? ORDER BY word
            """, (language, category))
        else:
            cursor.execute("""
                SELECT * FROM signs WHERE language = ? ORDER BY word
            """, (language,))

        results = cursor.fetchall()
        conn.close()
        return results

    def add_translation(self, source_type, input_data, translated_text, confidence, language="ASL"):
        conn = self._connect()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO translation_history (timestamp, source_type, input_data, 
                                           translated_text, confidence, language)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, source_type, input_data, translated_text, confidence, language))
        conn.commit()
        conn.close()

    def get_history(self, limit=100):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM translation_history 
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        results = cursor.fetchall()
        conn.close()
        return results

    def clear_history(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM translation_history")
        conn.commit()
        conn.close()

    def delete_history_item(self, item_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM translation_history WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return json.loads(result[0]) if result else default

    def set_setting(self, key, value):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, json.dumps(value)))
        conn.commit()
        conn.close()

    def get_resources(self, language=None, category=None):
        """Get external learning resources."""
        conn = self._connect()
        cursor = conn.cursor()

        if language and language != "All":
            if category and category != "All":
                cursor.execute("""
                    SELECT * FROM resources WHERE language = ? AND category = ? ORDER BY title
                """, (language, category))
            else:
                cursor.execute("""
                    SELECT * FROM resources WHERE language = ? ORDER BY title
                """, (language,))
        else:
            if category and category != "All":
                cursor.execute("""
                    SELECT * FROM resources WHERE category = ? ORDER BY title
                """, (category,))
            else:
                cursor.execute("SELECT * FROM resources ORDER BY title")

        results = cursor.fetchall()
        conn.close()
        return results
