import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time as time_module
from io import StringIO
import csv
import os
from pathlib import Path
import warnings
import hashlib
import base64
from collections import defaultdict

warnings.filterwarnings('ignore')

# Konfiguration
st.set_page_config(
    page_title="Substanz-Tagebuch mit KI-Therapeut",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Datenverzeichnis erstellen
DATA_DIR = Path("data")
BACKUP_DIR = Path("backups")
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# Passwortschutz (Einfache Implementierung - in Produktion bcrypt verwenden)
PASSWORD_HASH = ""  # Leer = kein Passwort erforderlich

# Alle Substanzen
ALL_SUBSTANCES = [
    'Cannabis', 'Alkohol', 'MDMA', 'LSD', 'Kokain',
    'Amphetamine', 'Psilocybin', 'Ketamin',
    'Benzodiazepine', 'Opioide'
]


# ============================================================================
# PASSWORT SCHUTZ
# ============================================================================

def check_password():
    """Überprüft Passwort oder setzt es"""
    if not PASSWORD_HASH:
        return True

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Passwort erforderlich")

        col1, col2 = st.columns([2, 1])
        with col1:
            password = st.text_input("Passwort:", type="password", key="password_input")

            if st.button("🔓 Entsperren", type="primary"):
                # Einfacher Hash-Vergleich
                input_hash = hashlib.sha256(password.encode()).hexdigest()
                if input_hash == PASSWORD_HASH:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Falsches Passwort")

        with col2:
            st.info("""
            **Erster Start?**  
            Standard-Passwort: `admin123`

            Ändere `PASSWORD_HASH` im Code für sicheres Passwort.
            """)

        st.stop()

    return True


# ============================================================================
# ERWEITERTE KI-KLASSE
# ============================================================================

class AdvancedKIAnalyzer:
    """Erweiterte KI-Analyse mit Predictive Features"""

    def __init__(self, entries, health_data):
        self.entries = entries
        self.health_data = health_data
        self.risk_factors = []
        self.predictions = {}

    def analyze_risk_patterns(self):
        """Analysiert Risikomuster"""
        if not self.entries:
            return []

        patterns = []

        # Häufigkeit Analyse
        last_7_days = []
        cutoff = datetime.now() - timedelta(days=7)

        for entry in self.entries:
            try:
                entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
                if entry_date >= cutoff:
                    last_7_days.append(entry)
            except:
                continue

        if len(last_7_days) >= 5:
            patterns.append({
                'type': 'frequency_high',
                'message': f"Hohe Konsumhäufigkeit: {len(last_7_days)} Tage in den letzten 7 Tagen",
                'severity': 'high'
            })

        # Kostenanalyse
        monthly_costs = defaultdict(float)
        for entry in self.entries:
            try:
                date = datetime.strptime(entry['date'], '%Y-%m-%d')
                month_key = f"{date.year}-{date.month:02d}"
                cost = float(entry.get('cost', 0))
                monthly_costs[month_key] += cost
            except:
                continue

        for month, cost in monthly_costs.items():
            if cost > 200:
                patterns.append({
                    'type': 'cost_high',
                    'message': f"Hohe monatliche Kosten ({month}): {cost:.2f}€",
                    'severity': 'medium'
                })

        # Substanz-Kombinationen
        substance_combinations = defaultdict(set)
        dates_with_multiple = []

        for entry in self.entries:
            date = entry['date']
            substance_combinations[date].add(entry['substance'])

        for date, substances in substance_combinations.items():
            if len(substances) > 1:
                dates_with_multiple.append((date, substances))

        if len(dates_with_multiple) > 2:
            patterns.append({
                'type': 'combinations_frequent',
                'message': f"Häufige Substanz-Kombinationen an {len(dates_with_multiple)} Tagen",
                'severity': 'high'
            })

        # Bewertungsmuster
        low_rating_entries = [e for e in self.entries if e.get('rating', 5) <= 2]
        if len(low_rating_entries) > 3:
            patterns.append({
                'type': 'low_rating_frequent',
                'message': f"Mehrere negative Erfahrungen ({len(low_rating_entries)} mit Bewertung ≤2)",
                'severity': 'medium'
            })

        self.risk_factors = patterns
        return patterns

    def generate_predictions(self):
        """Generiert Vorhersagen basierend auf Mustern"""
        predictions = []

        if not self.entries:
            return predictions

        # Analysiere Konsummuster
        entries_by_day = defaultdict(list)
        for entry in self.entries:
            date = entry['date']
            entries_by_day[date].append(entry)

        # Vorhersage für nächste Woche
        recent_dates = sorted(entries_by_day.keys())[-7:]
        recent_count = sum(len(entries_by_day[d]) for d in recent_dates)

        if recent_count > 0:
            avg_per_day = recent_count / len(recent_dates)
            predicted_next_week = avg_per_day * 7

            predictions.append({
                'type': 'consumption_next_week',
                'value': round(predicted_next_week, 1),
                'confidence': 'medium',
                'message': f"Vorhersage: {predicted_next_week:.1f} Konsumtage in der nächsten Woche"
            })

        # Kosten-Vorhersage
        recent_costs = []
        for entry in self.entries[-20:]:
            try:
                cost = float(entry.get('cost', 0))
                if cost > 0:
                    recent_costs.append(cost)
            except:
                continue

        if recent_costs:
            avg_cost = sum(recent_costs) / len(recent_costs)
            monthly_prediction = avg_cost * 30

            predictions.append({
                'type': 'monthly_cost_prediction',
                'value': round(monthly_prediction, 2),
                'confidence': 'low',
                'message': f"Monatliche Kosten-Vorhersage: ~{monthly_prediction:.2f}€"
            })

        self.predictions = predictions
        return predictions

    def get_personalized_recommendations(self):
        """Generiert personalisierte Empfehlungen"""
        recommendations = []

        if not self.entries:
            return ["Beginne mit der Dateneingabe für personalisierte Empfehlungen"]

        # Schlafanalyse
        sleep_entries = [h for h in self.health_data
                         if any(word in str(h.get('Type', '')).lower()
                                for word in ['sleep', 'schlaf'])]

        if sleep_entries:
            sleep_values = [float(h.get('value', 0)) for h in sleep_entries]
            avg_sleep = sum(sleep_values) / len(sleep_values)

            if avg_sleep < 360:  # Weniger als 6 Stunden
                recommendations.append("💤 Schlafoptimierung: Versuche, deine Schlafdauer auf 7-9 Stunden zu erhöhen")

        # Konsumpausen empfehlen
        if len(self.entries) > 10:
            dates = sorted(set(e['date'] for e in self.entries))
            date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

            gaps = []
            for i in range(1, len(date_objects)):
                gap = (date_objects[i] - date_objects[i - 1]).days
                gaps.append(gap)

            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                if avg_gap < 3:
                    recommendations.append("⏱️ Konsumpausen: Versuche, längere Pausen zwischen Konsumtagen einzulegen")

        # Wochenend-Muster
        weekend_entries = []
        weekday_entries = []

        for entry in self.entries:
            try:
                date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
                if date_obj.weekday() >= 5:  # Wochenende
                    weekend_entries.append(entry)
                else:
                    weekday_entries.append(entry)
            except:
                continue

        weekend_ratio = len(weekend_entries) / max(1, len(weekday_entries))
        if weekend_ratio > 3:
            recommendations.append("📅 Wochenend-Muster: Achte auf Konsum auch unter der Woche")

        # Alternative Aktivitäten vorschlagen
        if len(self.entries) > 5:
            recommendations.extend([
                "🎯 Ziele setzen: Definiere klare Konsumziele",
                "📝 Reflektieren: Dokumentiere deine Erfahrungen regelmäßig",
                "🧘 Alternativen: Suche nach nicht-substanzgebundenen Aktivitäten"
            ])

        return recommendations if recommendations else [
            "Weiter so! Deine aktuellen Muster sehen ausgewogen aus."
        ]


# ============================================================================
# GAMIFICATION SYSTEM
# ============================================================================

class GamificationSystem:
    """Spielerische Elemente zur Motivation"""

    def __init__(self):
        self.achievements = []
        self.streaks = {
            'current': 0,
            'best': 0,
            'last_entry_date': None
        }
        self.points = 0

    def calculate_streak(self, entries):
        """Berechnet aktuelle und beste Serie von konsumfreien Tagen"""
        if not entries:
            return self.streaks

        # Sortiere Einträge nach Datum
        sorted_entries = sorted(entries,
                                key=lambda x: x.get('date', '2000-01-01'),
                                reverse=True)

        # Finde letztes Konsumdatum
        last_consumption_date = None
        if sorted_entries:
            try:
                last_consumption_date = datetime.strptime(
                    sorted_entries[0]['date'],
                    '%Y-%m-%d'
                ).date()
            except:
                pass

        today = datetime.now().date()

        if last_consumption_date:
            days_since = (today - last_consumption_date).days
            self.streaks['current'] = days_since

            if days_since > self.streaks['best']:
                self.streaks['best'] = days_since

        return self.streaks

    def check_achievements(self, entries, goals, stats):
        """Überprüft und vergibt Achievements"""
        achievements = []

        # Meilenstein Achievements
        if stats and stats.get('totalEntries', 0) >= 10:
            achievements.append({
                'id': 'first_10',
                'title': '🏁 Erste 10 Einträge',
                'description': '10 Tagebucheinträge erreicht',
                'icon': '🏁',
                'unlocked': True
            })

        if stats and stats.get('totalEntries', 0) >= 30:
            achievements.append({
                'id': 'consistent_tracker',
                'title': '📅 Konsistenter Dokumentierer',
                'description': '30 Tagebucheinträge erreicht',
                'icon': '📅',
                'unlocked': True
            })

        # Streak Achievements
        if self.streaks['current'] >= 7:
            achievements.append({
                'id': 'week_clean',
                'title': '🌟 7-Tage-Serie',
                'description': '7 Tage ohne Konsum',
                'icon': '🌟',
                'unlocked': True
            })

        if self.streaks['current'] >= 30:
            achievements.append({
                'id': 'month_clean',
                'title': '🏆 30-Tage-Serie',
                'description': '30 Tage ohne Konsum',
                'icon': '🏆',
                'unlocked': True
            })

        # Ziel Achievements
        completed_goals = [g for g in goals if g.get('completed', False)]
        if len(completed_goals) >= 1:
            achievements.append({
                'id': 'goal_achiever',
                'title': '🎯 Ziel erreicht',
                'description': 'Erstes Ziel erfolgreich abgeschlossen',
                'icon': '🎯',
                'unlocked': True
            })

        # Reflexion Achievements
        entries_with_experience = [e for e in entries if e.get('experience', '').strip()]
        if len(entries_with_experience) >= 5:
            achievements.append({
                'id': 'reflective_writer',
                'title': '📝 Reflektierender Schreiber',
                'description': '5 detaillierte Erfahrungsberichte',
                'icon': '📝',
                'unlocked': True
            })

        # Kostenbewusstsein
        if stats and stats.get('totalCost', 0) > 0:
            monthly_cost = stats['totalCost'] / (stats['totalEntries'] / 30) if stats['totalEntries'] > 0 else 0
            if monthly_cost < 50:
                achievements.append({
                    'id': 'cost_conscious',
                    'title': '💰 Kostenbewusst',
                    'description': 'Monatliche Kosten unter 50€',
                    'icon': '💰',
                    'unlocked': True
                })

        self.achievements = achievements
        return achievements

    def calculate_points(self, entries, achievements):
        """Berechnet Punkte basierend auf Aktivitäten"""
        points = 0

        # Punkte für Einträge
        points += len(entries) * 10

        # Punkte für detaillierte Einträge
        detailed_entries = len([e for e in entries if e.get('experience', '').strip()])
        points += detailed_entries * 20

        # Punkte für Achievements
        points += len(achievements) * 100

        # Punkte für Streaks
        points += self.streaks['current'] * 50
        points += self.streaks['best'] * 25

        self.points = points
        return points


# ============================================================================
# KI-CHAT SYSTEM (OFFLINE)
# ============================================================================

class KIChatSystem:
    """Offline KI-Chat für Unterstützung und Reflexion"""

    def __init__(self, entries, health_data, goals, stats):
        self.entries = entries
        self.health_data = health_data
        self.goals = goals
        self.stats = stats
        self.context = []
        self.responses_db = self._load_responses()

    def _load_responses(self):
        """Lädt Antwortmuster und Wissen"""
        return {
            'greetings': {
                'patterns': ['hallo', 'hi', 'hey', 'guten tag', 'moin'],
                'responses': [
                    "Hallo! Ich bin dein KI-Therapeut. Wie kann ich dir helfen?",
                    "Hallo! Schön, dich zu sehen. Was beschäftigt dich heute?",
                    "Hi! Ich bin hier, um dir zuzuhören und zu unterstützen."
                ]
            },
            'how_are_you': {
                'patterns': ['wie geht', 'wie gehts', 'wie fühlst du', 'alles gut'],
                'responses': [
                    "Mir geht es gut, danke der Nachfrage! Ich bin hier, um dir zu helfen.",
                    "Alles bestens! Konzentriere ich mich ganz auf dich. Wie kann ich helfen?"
                ]
            },
            'help': {
                'patterns': ['hilfe', 'was kannst du', 'funktionen', 'unterstützung'],
                'responses': [
                    "Ich kann dir helfen bei: \n"
                    "• Analyse deiner Konsummuster \n"
                    "• Reflexion deiner Erfahrungen \n"
                    "• Zielsetzung und -verfolgung \n"
                    "• Risikobewertung \n"
                    "• Motivationsunterstützung \n"
                    "Frag mich einfach konkret!"
                ]
            },
            'patterns': {
                'patterns': ['muster', 'pattern', 'trend', 'entwicklung', 'verlauf'],
                'responses': [
                    self._analyze_patterns_response()
                ]
            },
            'risk': {
                'patterns': ['risiko', 'gefahr', 'problem', 'sorge', 'bedenken'],
                'responses': [
                    self._assess_risk_response()
                ]
            },
            'goals': {
                'patterns': ['ziel', 'vorhaben', 'plan', 'vorsatz'],
                'responses': [
                    self._goals_status_response()
                ]
            },
            'motivation': {
                'patterns': ['motivation', 'antrieb', 'energie', 'schwung', 'müde'],
                'responses': [
                    "Motivation kommt und geht in Wellen. Das ist normal! "
                    "Kleine Schritte sind oft nachhaltiger als große Sprünge.",
                    "Erinnere dich an deine Gründe für Veränderung. "
                    "Was war dein Auslöser, dieses Tagebuch zu führen?"
                ]
            },
            'relapse': {
                'patterns': ['rückfall', 'fehlschlag', 'gescheitert', 'versagt'],
                'responses': [
                    "Rückfälle sind Teil des Prozesses, nicht sein Scheitern. "
                    "Wichtig ist, was du daraus lernst.",
                    "Jeder Tag ist eine neue Chance. "
                    "Analysiere, was zum Rückfall führte und plane voraus."
                ]
            },
            'stress': {
                'patterns': ['stress', 'druck', 'überfordert', 'belastet'],
                'responses': [
                    "Stress ist ein häufiger Auslöser. "
                    "Welche alternativen Bewältigungsstrategien kennst du?",
                    "Atme tief durch. Erinnere dich: "
                    "Substanzen lösen Probleme nicht, sie verschieben sie nur."
                ]
            },
            'sleep': {
                'patterns': ['schlaf', 'müdigkeit', 'erschöpft', 'ausgeruht'],
                'responses': [
                    "Schlaf ist essenziell für Erholung. "
                    f"{self._sleep_analysis()}"
                ]
            },
            'default': {
                'patterns': [],
                'responses': [
                    "Das habe ich nicht ganz verstanden. Könntest du das anders formulieren?",
                    "Interessant! Erzähl mir mehr darüber.",
                    "Wie fühlst du dich dabei?",
                    "Was denkst du, wäre ein nächster Schritt?"
                ]
            }
        }

    def _analyze_patterns_response(self):
        """Generiert Muster-Analyse Antwort"""
        if not self.entries:
            return "Ich sehe noch keine Muster. Füge mehr Einträge hinzu für eine Analyse."

        response = "Basierend auf deinen Daten erkenne ich:\n\n"

        # Häufigste Substanz
        substance_counts = {}
        for entry in self.entries:
            sub = entry.get('substance', '')
            substance_counts[sub] = substance_counts.get(sub, 0) + 1

        if substance_counts:
            most_common = max(substance_counts.items(), key=lambda x: x[1])
            response += f"• Häufigste Substanz: {most_common[0]} ({most_common[1]}x)\n"

        # Zeitmuster
        if len(self.entries) > 5:
            dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in self.entries]
            weekdays = [d.weekday() for d in dates]
            weekend_count = sum(1 for w in weekdays if w >= 5)
            weekend_percent = (weekend_count / len(weekdays)) * 100

            response += f"• {weekend_percent:.0f}% deiner Einträge sind am Wochenende\n"

        # Bewertungstrend
        if len(self.entries) > 3:
            ratings = [e.get('rating', 3) for e in self.entries]
            avg_rating = sum(ratings) / len(ratings)
            response += f"• Durchschnittliche Bewertung: {avg_rating:.1f}/5\n"

        return response

    def _assess_risk_response(self):
        """Generiert Risiko-Bewertung"""
        if not self.entries:
            return "Noch keine Risikobewertung möglich. Bitte trage Daten ein."

        response = "Meine Einschätzung zu Risiken:\n\n"
        risk_factors = []

        # Häufigkeit
        last_7_days = []
        cutoff = datetime.now() - timedelta(days=7)
        for entry in self.entries:
            try:
                entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
                if entry_date >= cutoff:
                    last_7_days.append(entry)
            except:
                continue

        if len(last_7_days) >= 5:
            risk_factors.append(f"• Hohe Häufigkeit ({len(last_7_days)}x in 7 Tagen)")

        # Kosten
        total_cost = 0
        for e in self.entries[-30:]:
            try:
                cost = float(e.get('cost', 0))
                total_cost += cost
            except:
                continue

        if total_cost > 150:
            risk_factors.append(f"• Hohe Kosten (~{total_cost:.0f}€ in 30 Tagen)")

        # Negative Erfahrungen
        bad_experiences = len([e for e in self.entries if e.get('rating', 5) <= 2])
        if bad_experiences > 2:
            risk_factors.append(f"• Mehrere negative Erfahrungen ({bad_experiences}x)")

        if risk_factors:
            response += "\n".join(risk_factors)
            response += "\n\nEmpfehlung: Diese Faktoren im Auge behalten und ggf. professionelle Hilfe suchen."
        else:
            response += "• Aktuell keine alarmierenden Risikofaktoren erkannt\n"
            response += "• Weiterhin achtsam bleiben"

        return response

    def _goals_status_response(self):
        """Generiert Ziel-Status Antwort"""
        if not self.goals:
            return "Du hast noch keine Ziele gesetzt. Möchtest du welche erstellen?"

        response = "Deine Ziele im Überblick:\n\n"

        for goal in self.goals[:3]:
            completed = "✅" if goal.get('completed', False) else "⏳"
            response += f"{completed} {goal.get('substance', 'Ziel')}: {goal.get('type', '')}\n"

        completed_count = len([g for g in self.goals if g.get('completed', False)])
        response += f"\nFortschritt: {completed_count}/{len(self.goals)} Ziele erreicht"

        return response

    def _sleep_analysis(self):
        """Analysiert Schlafdaten"""
        if not self.health_data:
            return "Ich sehe keine Schlafdaten. Hast du Health-Daten importiert?"

        sleep_entries = [h for h in self.health_data
                         if any(word in str(h.get('Type', '')).lower()
                                for word in ['sleep', 'schlaf'])]

        if not sleep_entries:
            return "Keine Schlafdaten gefunden. Du kannst sie im Health-Tab importieren."

        sleep_values = []
        for entry in sleep_entries:
            try:
                value = float(entry.get('value', 0))
                sleep_values.append(value)
            except:
                continue

        if not sleep_values:
            return "Schlafdaten vorhanden, aber keine messbaren Werte."

        avg_sleep = sum(sleep_values) / len(sleep_values)

        if avg_sleep < 360:  # < 6 Stunden
            return f"Durchschnittlich nur {avg_sleep / 60:.1f}h Schlaf. Das ist wenig! Mehr Schlaf kann die Regeneration verbessern."
        elif avg_sleep > 540:  # > 9 Stunden
            return f"Durchschnittlich {avg_sleep / 60:.1f}h Schlaf. Viel Schlaf ist gut, aber achte auf die Qualität."
        else:
            return f"Durchschnittlich {avg_sleep / 60:.1f}h Schlaf. Gute Menge! Weiter so."

    def get_response(self, user_input):
        """Generiert KI-Antwort auf User-Input"""
        user_input_lower = user_input.lower()

        # Füge zum Kontext hinzu
        self.context.append({'role': 'user', 'content': user_input})

        # Prüfe Antwort-Typen
        for category, data in self.responses_db.items():
            for pattern in data['patterns']:
                if pattern in user_input_lower:
                    import random
                    response = random.choice(data['responses'])
                    self.context.append({'role': 'assistant', 'content': response})
                    return response

        # Default Antwort
        import random
        response = random.choice(self.responses_db['default']['responses'])
        self.context.append({'role': 'assistant', 'content': response})
        return response

    def get_context_aware_response(self, user_input, current_mood=None):
        """Kontext-sensitive Antwort"""
        base_response = self.get_response(user_input)

        # Füge bei spezifischer Stimmung zusätzliche Empathie hinzu
        if current_mood:
            mood_keywords = {
                'traurig': 'Es tut mir leid, dass du dich traurig fühlst. ',
                'gestresst': 'Stress kann herausfordernd sein. ',
                'müde': 'Bei Müdigkeit ist Selbstfürsorge besonders wichtig. ',
                'glücklich': 'Schön, dass du dich gut fühlst! '
            }

            for mood, prefix in mood_keywords.items():
                if mood in current_mood.lower():
                    return prefix + base_response

        return base_response


# ============================================================================
# NOTFALL & WICHTIGE KONTAKTE
# ============================================================================

def show_emergency_contacts():
    """Zeigt wichtige Notfallkontakte"""
    st.markdown("""
    ## 🚨 Wichtige Notfallkontakte

    ### 📞 Soforthilfe-Telefonnummern:

    **Sucht- & Drogenhotline (kostenlos):**
    - **01806 31 30 31** (0,20 €/Verbindung)
    - **0800 1 81 07 71** (Drogennotdienst Berlin)

    **Telefonseelsorge (24/7, anonym):**
    - **0800 111 0 111** oder **0800 111 0 222**
    - **116 123** (Europaweit)

    **Ärztlicher Bereitschaftsdienst:**
    - **116 117** (Deutschlandweit)

    **Akute Vergiftungen:**
    - **030 192 40** (Giftnotruf Berlin)
    - **030 450 53 0** (Charité Notaufnahme)

    ### 🌐 Online-Hilfe:

    - [Sucht-und-drogen-hotline.de](https://www.sucht-und-drogen-hotline.de)
    - [Drugcom.de](https://www.drugcom.de)
    - [Check-your-drugs.de](https://www.check-your-drugs.de)

    ### 🏥 Drug Checking Services:

    - **Berlin:** Eve & Rave / [Safer Night Life](https://www.safernightlife.de)
    - **Hamburg:** Drugchecking Hamburg
    - **Zürich:** [Saferparty.ch](https://www.saferparty.ch)

    ### ⚠️ Bei diesen Symptomen SOFORT 112 wählen:

    - Atemstillstand oder schwere Atemprobleme
    - Krampfanfälle
    - Bewusstlosigkeit
    - Starke Brustschmerzen
    - Psychotische Zustände mit Gefahr für sich/andere

    **💡 Erste-Hilfe-Tipp:** Bei Opioid-Überdosierung – wenn verfügbar – Naloxon verabreichen und Notruf wählen!
    """)

    if st.button("📱 Kontakte zu meinen Kontakten hinzufügen"):
        # Code für Kontaktdaten-Export
        vcard = """BEGIN:VCARD
VERSION:3.0
FN:Sucht- und Drogenhotline
TEL;TYPE=work,voice:01806313031
URL:https://www.sucht-und-drogen-hotline.de
END:VCARD

BEGIN:VCARD
VERSION:3.0
FN:Telefonseelsorge
TEL;TYPE=work,voice:08001110111
URL:https://www.telefonseelsorge.de
END:VCARD"""

        st.download_button(
            label="📥 VCF-Datei herunterladen",
            data=vcard,
            file_name="notfallkontakte.vcf",
            mime="text/vcard"
        )


# ============================================================================
# WISSENSCHAFTLICHE ASSESSMENTS
# ============================================================================

def show_scientific_assessments():
    """Zeigt wissenschaftlich validierte Assessments"""

    tab1, tab2, tab3, tab4 = st.tabs(["AUDIT", "DUDIT", "CAGE", "PHQ-4"])

    with tab1:
        st.subheader("🔍 AUDIT (Alcohol Use Disorders Identification Test)")

        audit_questions = [
            "Wie oft trinken Sie alkoholische Getränke?",
            "Wie viele alkoholische Getränke trinken Sie an einem typischen Tag, an dem Sie Alkohol trinken?",
            "Wie oft trinken Sie sechs oder mehr Getränke bei einer Gelegenheit?",
            "Wie oft waren Sie im letzten Jahr nicht in der Lage, mit dem Trinken aufzuhören, nachdem Sie angefangen hatten?",
            "Wie oft sind Sie im letzten Jahr wegen Ihres Trinkens Ihren üblichen Pflichten nicht nachgekommen?",
            "Wie oft haben Sie im letzten Jahr morgens als erstes Alkohol getrunken, um 'in die Gänge zu kommen'?",
            "Wie oft hatten Sie im letzten Jahr nach dem Trinken Schuldgefühle oder Gewissensbisse?",
            "Wie oft konnten Sie sich im letzten Jahr an Ereignisse der vergangenen Nacht nicht mehr erinnern, weil Sie getrunken hatten?",
            "Wurden Sie oder jemand anderes wegen Ihres Trinkens verletzt?",
            "Hat sich schon einmal ein Verwandter, Freund, Arzt oder eine andere medizinische Fachkraft wegen Ihres Trinkens Sorgen gemacht oder vorgeschlagen, dass Sie weniger trinken sollten?"
        ]

        audit_scores = []
        for i, question in enumerate(audit_questions[:5]):
            score = st.slider(f"{i + 1}. {question}", 0, 4, 0,
                              help="0=nie, 1=monatlich oder weniger, 2=2-4x/Monat, 3=2-3x/Woche, 4=4+ mal/Woche")
            audit_scores.append(score)

        if st.button("AUDIT Auswerten"):
            total = sum(audit_scores)
            if total <= 7:
                st.success(f"Score: {total} - Niedriges Risiko")
            elif total <= 15:
                st.warning(f"Score: {total} - Mittleres Risiko")
            else:
                st.error(f"Score: {total} - Hohes Risiko, professionelle Hilfe empfohlen")

    with tab2:
        st.subheader("💊 DUDIT (Drug Use Disorders Identification Test)")

        dudit_questions = [
            "Wie oft nehmen Sie Drogen?",
            "Wie viele Drogeneinheiten nehmen Sie an einem typischen Tag?",
            "Wie oft nehmen Sie Drogen in großen Mengen?",
            "Wie oft haben Sie ein starkes Verlangen nach Drogen?",
            "Wie oft hatten Sie gesundheitliche Probleme wegen Drogen?",
            "Wie oft hatten Sie soziale Probleme wegen Drogen?",
            "Wie oft konnten Sie wegen Drogen Ihren Verpflichtungen nicht nachkommen?",
            "Wie oft mussten Sie morgens als erstes Drogen nehmen?"
        ]

        for i in range(4):
            st.slider(f"DUDIT Frage {i + 1}", 0, 4, 0)

        if st.button("DUDIT Auswerten"):
            st.info("Ein Score ≥6 bei Männern oder ≥2 bei Frauen deutet auf problematischen Drogenkonsum hin")

    with tab3:
        st.subheader("🚫 CAGE-Fragebogen")

        cage_questions = [
            "Haben Sie jemals das Gefühl gehabt, Sie sollten Ihren Alkohol- oder Drogenkonsum reduzieren?",
            "Haben sich Leute Sie durch Kritik an Ihrem Alkohol- oder Drogenkonsum genervt?",
            "Haben Sie jemals wegen Ihres Alkohol- oder Drogenkonsums Schuldgefühle gehabt?",
            "Haben Sie jemals morgens als erstes Alkohol/Drogen genommen, um 'in die Gänge zu kommen'?"
        ]

        yes_count = 0
        for question in cage_questions:
            if st.checkbox(question):
                yes_count += 1

        if yes_count >= 2:
            st.warning(f"{yes_count}/4 positiv - Möglicherweise problematischer Konsum")
        else:
            st.success(f"{yes_count}/4 positiv - Unauffällig")

    with tab4:
        st.subheader("😔 PHQ-4 (Depression & Angst)")

        phq_questions = [
            "Wie oft fühlten Sie sich im letzten Monat nervös, ängstlich oder angespannt?",
            "Wie oft konnten Sie im letzten Monat nicht aufhören, sich Sorgen zu machen?",
            "Wie oft fühlten Sie sich im letzten Monat wenig Interesse oder Freude an Ihren Tätigkeiten?",
            "Wie oft fühlten Sie sich im letzten Monat niedergeschlagen, depressiv oder hoffnungslos?"
        ]

        phq_score = 0
        for question in phq_questions:
            score = st.selectbox(question,
                                 ["Überhaupt nicht (0)", "An einzelnen Tagen (1)",
                                  "An mehr als der Hälfte der Tage (2)", "Beinahe jeden Tag (3)"])
            phq_score += ["Überhaupt nicht (0)", "An einzelnen Tagen (1)",
                          "An mehr als der Hälfte der Tage (2)", "Beinahe jeden Tag (3)"].index(score)

        if st.button("PHQ-4 Auswerten"):
            if phq_score >= 6:
                st.error(f"Score: {phq_score} - Deutliche Symptome von Depression/Ängstlichkeit")
            elif phq_score >= 3:
                st.warning(f"Score: {phq_score} - Leichte Symptome")
            else:
                st.success(f"Score: {phq_score} - Keine relevanten Symptome")


# ============================================================================
# PERSÖNLICHES JOURNAL
# ============================================================================

def show_personal_journal():
    """Persönliches Tagebuch neben Substanz-Tracking"""

    if 'journal_entries' not in st.session_state:
        st.session_state.journal_entries = []

    st.subheader("📖 Persönliches Tagebuch")

    tab1, tab2, tab3 = st.tabs(["Neuer Eintrag", "Meine Einträge", "Reflexionsübungen"])

    with tab1:
        with st.form("journal_form"):
            col1, col2 = st.columns(2)

            with col1:
                entry_date = st.date_input("Datum", value=datetime.now())
                mood = st.select_slider(
                    "Stimmung",
                    options=["😢 Sehr schlecht", "😞 Schlecht", "😐 Neutral",
                             "🙂 Gut", "😊 Sehr gut"]
                )

            with col2:
                entry_type = st.selectbox(
                    "Eintragstyp",
                    ["Tagesreflexion", "Erfolg", "Herausforderung",
                     "Dankbarkeit", "Ideen", "Träume/Ziele"]
                )
                tags = st.multiselect(
                    "Tags",
                    ["Arbeit", "Beziehung", "Familie", "Freunde", "Gesundheit",
                     "Hobbys", "Finanzen", "Persönliches Wachstum"]
                )

            title = st.text_input("Titel", placeholder="Was beschäftigt dich?")
            content = st.text_area(
                "Inhalt",
                placeholder="Schreibe hier deine Gedanken...",
                height=200,
                help="Schreibe frei, ohne Filter. Dies ist nur für dich."
            )

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Eintrag speichern", type="primary")
            with col2:
                if st.form_submit_button("❌ Abbrechen"):
                    st.rerun()

            if submitted and content.strip():
                new_entry = {
                    'id': int(time_module.time() * 1000),
                    'date': entry_date.strftime('%Y-%m-%d'),
                    'title': title,
                    'content': content,
                    'mood': mood,
                    'type': entry_type,
                    'tags': tags,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.journal_entries.append(new_entry)
                st.success("✅ Tagebucheintrag gespeichert!")
                time_module.sleep(1)
                st.rerun()

    with tab2:
        if not st.session_state.journal_entries:
            st.info("📝 Noch keine Tagebucheinträge. Beginne mit deiner ersten Reflexion!")
        else:
            # Filter
            col1, col2 = st.columns(2)
            with col1:
                filter_date = st.date_input("Nach Datum filtern", value=None)
            with col2:
                filter_tags = st.multiselect(
                    "Nach Tags filtern",
                    options=["Arbeit", "Beziehung", "Familie", "Freunde",
                             "Gesundheit", "Hobbys", "Finanzen", "Persönliches Wachstum"]
                )

            # Einträge anzeigen
            filtered_entries = st.session_state.journal_entries.copy()

            if filter_date:
                filter_str = filter_date.strftime('%Y-%m-%d')
                filtered_entries = [e for e in filtered_entries if e['date'] == filter_str]

            if filter_tags:
                filtered_entries = [e for e in filtered_entries
                                    if any(tag in e.get('tags', []) for tag in filter_tags)]

            for entry in sorted(filtered_entries,
                                key=lambda x: x['date'],
                                reverse=True):
                with st.expander(f"{entry['date']} - {entry.get('title', 'Ohne Titel')} {entry.get('mood', '')}"):
                    st.write(f"**Typ:** {entry.get('type', 'Unbekannt')}")
                    if entry.get('tags'):
                        st.write(f"**Tags:** {', '.join(entry['tags'])}")
                    st.divider()
                    st.write(entry['content'])

                    if st.button("🗑️ Löschen", key=f"del_journal_{entry['id']}"):
                        st.session_state.journal_entries = [
                            e for e in st.session_state.journal_entries
                            if e['id'] != entry['id']
                        ]
                        st.rerun()

    with tab3:
        st.subheader("🧘 Reflexionsübungen")

        exercises = {
            "Dankbarkeits-Tagebuch": "Nenne 3 Dinge, für die du heute dankbar bist.",
            "Erfolgsmoment": "Was ist heute gut gelaufen? Worauf bist du stolz?",
            "Herausforderung": "Was war heute schwierig? Wie bist du damit umgegangen?",
            "Lernerfahrung": "Was hast du heute über dich gelernt?",
            "Morgen-Vorsatz": "Was möchtest du morgen anders/besser machen?",
            "Selbstmitgefühl": "Was würdest du einem Freund sagen, der deine Situation hat?"
        }

        selected_exercise = st.selectbox("Wähle eine Übung:", list(exercises.keys()))

        st.write(f"**{selected_exercise}**")
        st.info(exercises[selected_exercise])

        response = st.text_area("Deine Antwort:", height=150)

        if st.button("Antwort speichern", type="secondary"):
            if response.strip():
                journal_entry = {
                    'id': int(time_module.time() * 1000),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'title': f"Reflexion: {selected_exercise}",
                    'content': response,
                    'type': 'Reflexionsübung',
                    'tags': ['Reflexion', selected_exercise],
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.journal_entries.append(journal_entry)
                st.success("✅ Reflexion gespeichert!")
                time_module.sleep(1)
                st.rerun()


# ============================================================================
# KI-CHAT INTERFACE
# ============================================================================

def show_ki_chat():
    """Zeigt den KI-Chat Interface"""
    st.header("💬 KI-Chat - Dein persönlicher Therapeut")

    # Initialisiere KI-Chat
    if 'ki_chat' not in st.session_state:
        stats = get_statistics() or {}
        st.session_state.ki_chat = KIChatSystem(
            st.session_state.entries,
            st.session_state.health_data,
            st.session_state.goals,
            stats
        )

    # Initialisiere Chat-Historie
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Chat Container
    chat_container = st.container()

    with chat_container:
        # Chat-Historie anzeigen
        for message in st.session_state.chat_history[-20:]:  # Zeige nur letzte 20 Nachrichten
            if message['role'] == 'user':
                st.markdown(f"""
                <div style='background-color: #2b313e; padding: 10px; 
                            border-radius: 10px; margin: 5px 0; text-align: right;'>
                    <strong>Du:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #1e3a5f; padding: 10px; 
                            border-radius: 10px; margin: 5px 0;'>
                    <strong>KI-Therapeut:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)

    # Vorgeschlagene Fragen
    st.subheader("💡 Mögliche Fragen")

    suggested_questions = [
        "Analysiere meine Konsummuster",
        "Wie hoch ist mein Risiko?",
        "Wie stehe ich mit meinen Zielen?",
        "Ich fühle mich gestresst",
        "Ich hatte einen Rückfall",
        "Wie kann ich meine Motivation steigern?",
        "Was sagt du zu meinen Schlafdaten?",
        "Hilfe, ich brauche Unterstützung"
    ]

    cols = st.columns(4)
    for i, question in enumerate(suggested_questions):
        with cols[i % 4]:
            if st.button(question, key=f"suggest_{i}"):
                # Direkte Antwort auf vorgeschlagene Frage
                response = st.session_state.ki_chat.get_response(question)
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': question
                })
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
                st.rerun()

    # Eingabe
    st.divider()
    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.text_input(
            "Deine Nachricht:",
            placeholder="Frag mich etwas über deine Daten, Muster oder Emotionen...",
            key="chat_input"
        )

    with col2:
        send_button = st.button("📤 Senden", type="primary", use_container_width=True)

    if send_button and user_input.strip():
        # User-Nachricht hinzufügen
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        # KI-Antwort generieren
        with st.spinner("🧠 KI denkt nach..."):
            # Hole aktuelle Stimmung vom letzten Eintrag
            current_mood = None
            if st.session_state.entries:
                last_entry = st.session_state.entries[-1]
                current_mood = last_entry.get('mood', '')

            response = st.session_state.ki_chat.get_context_aware_response(
                user_input,
                current_mood
            )

            # KI-Antwort hinzufügen
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })

        st.rerun()

    # Chat-Steuerung
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑️ Chat leeren", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        if st.button("💾 Chat exportieren", type="secondary"):
            chat_text = "KI-Chat Verlauf\n"
            chat_text += f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            chat_text += "=" * 50 + "\n\n"

            for msg in st.session_state.chat_history:
                role = "Du" if msg['role'] == 'user' else "KI-Therapeut"
                chat_text += f"{role}: {msg['content']}\n\n"

            st.download_button(
                label="📥 Chat herunterladen",
                data=chat_text,
                file_name=f"chat_verlauf_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

    with col3:
        if st.button("🔄 KI neu starten", type="secondary"):
            stats = get_statistics() or {}
            st.session_state.ki_chat = KIChatSystem(
                st.session_state.entries,
                st.session_state.health_data,
                st.session_state.goals,
                stats
            )
            st.session_state.chat_history = []
            st.success("KI neu initialisiert!")
            time_module.sleep(1)
            st.rerun()

    # Erweiterte KI-Analyse Optionen
    with st.expander("🤖 Erweiterte KI-Analyse", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Risikoanalyse durchführen", type="secondary"):
                analyzer = AdvancedKIAnalyzer(
                    st.session_state.entries,
                    st.session_state.health_data
                )
                risks = analyzer.analyze_risk_patterns()

                if risks:
                    response = "**Risikoanalyse Ergebnisse:**\n\n"
                    for risk in risks:
                        severity_icon = "🔴" if risk['severity'] == 'high' else "🟡" if risk[
                                                                                          'severity'] == 'medium' else "🟢"
                        response += f"{severity_icon} {risk['message']}\n"

                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    st.rerun()
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': "✅ Keine besorgniserregenden Risikomuster erkannt."
                    })
                    st.rerun()

        with col2:
            if st.button("📈 Vorhersagen generieren", type="secondary"):
                analyzer = AdvancedKIAnalyzer(
                    st.session_state.entries,
                    st.session_state.health_data
                )
                predictions = analyzer.generate_predictions()

                if predictions:
                    response = "**Vorhersagen basierend auf deinen Daten:**\n\n"
                    for pred in predictions:
                        confidence = "🔴 Hoch" if pred['confidence'] == 'high' else "🟡 Mittel" if pred[
                                                                                                     'confidence'] == 'medium' else "🟢 Niedrig"
                        response += f"• {pred['message']} ({confidence})\n"

                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    st.rerun()
                else:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': "❌ Nicht genug Daten für Vorhersagen vorhanden."
                    })
                    st.rerun()


# ============================================================================
# GAMIFICATION & MOTIVATION
# ============================================================================

def show_gamification():
    """Zeigt Gamification und Motivations-Features"""

    if 'gamification' not in st.session_state:
        st.session_state.gamification = GamificationSystem()

    gamification = st.session_state.gamification
    stats = get_statistics() or {}

    # Aktualisiere Streaks und Achievements
    streaks = gamification.calculate_streak(st.session_state.entries)
    achievements = gamification.check_achievements(
        st.session_state.entries,
        st.session_state.goals,
        stats
    )
    points = gamification.calculate_points(st.session_state.entries, achievements)

    st.header("🎮 Gamification & Motivation")

    # Top Stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🏆 Punkte", f"{points:,}")

    with col2:
        st.metric("🔥 Aktuelle Serie", f"{streaks['current']} Tage")

    with col3:
        st.metric("📈 Beste Serie", f"{streaks['best']} Tage")

    st.divider()

    # Achievements
    st.subheader("🏅 Deine Achievements")

    if achievements:
        unlocked = [a for a in achievements if a.get('unlocked', False)]
        locked_count = len(achievements) - len(unlocked)

        cols = st.columns(3)
        for i, achievement in enumerate(unlocked[:6]):
            with cols[i % 3]:
                st.markdown(f"""
                <div style='background-color: #2b313e; padding: 15px; 
                            border-radius: 10px; margin: 5px; text-align: center;'>
                    <div style='font-size: 30px;'>{achievement.get('icon', '🏆')}</div>
                    <strong>{achievement.get('title', '')}</strong><br>
                    <small>{achievement.get('description', '')}</small>
                </div>
                """, unsafe_allow_html=True)

        if locked_count > 0:
            st.info(f"🔒 Noch {locked_count} Achievements zu entsperren!")
    else:
        st.info("🎯 Beginne mit der Dateneingabe, um Achievements zu sammeln!")

    st.divider()

    # Motivations-Tools
    st.subheader("💪 Motivations-Tools")

    tab1, tab2, tab3 = st.tabs(["Ziel-Visualisierung", "Motivationssprüche", "Fortschritts-Challenge"])

    with tab1:
        if st.session_state.goals:
            goal = st.selectbox(
                "Wähle ein Ziel zur Visualisierung:",
                [g for g in st.session_state.goals],
                format_func=lambda x: f"{x.get('substance', 'Ziel')} - {x.get('type', '')}"
            )

            if goal:
                start_date = datetime.fromisoformat(goal['start_date']).date()
                days_since = (datetime.now().date() - start_date).days + 1

                if goal['type'] == "Tage Pause":
                    target_days = int(goal['value'])
                    progress = min(100, (streaks['current'] / target_days) * 100)

                    st.write(f"**Fortschritt:** {streaks['current']} von {target_days} Tagen")
                    st.progress(progress / 100)

                    # Visualisierung
                    if progress >= 100:
                        st.balloons()
                        st.success("🎉 Ziel erreicht! Fantastische Leistung!")
                    else:
                        remaining = target_days - streaks['current']
                        st.info(f"💪 Noch {remaining} Tage bis zum Ziel!")
        else:
            st.info("🎯 Setze zuerst Ziele in der Ziele-Ansicht")

    with tab2:
        st.subheader("💭 Motivationssprüche")

        quotes = [
            "Jede Reise beginnt mit einem ersten Schritt.",
            "Rückfälle sind nicht das Ende, sie sind Teil des Weges.",
            "Du bist stärker als du denkst.",
            "Heute ist ein neuer Tag, eine neue Chance.",
            "Kleine Fortschritte sind immer noch Fortschritte.",
            "Vertraue dem Prozess. Du schaffst das.",
            "Selbstfürsorge ist kein Luxus, sondern eine Notwendigkeit.",
            "Du kontrollierst deine Entscheidungen, nicht umgekehrt.",
            "Jeder Tag ohne ist ein Sieg.",
            "Deine Gesundheit ist dein wertvollstes Gut."
        ]

        import random
        if st.button("🎲 Zufälligen Spruch anzeigen"):
            quote = random.choice(quotes)
            st.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 20px; 
                        border-radius: 10px; margin: 10px 0; 
                        text-align: center; font-style: italic;'>
                "{quote}"
            </div>
            """, unsafe_allow_html=True)

        # Persönlicher Spruch basierend auf Daten
        if streaks['current'] > 0:
            st.info(f"🎊 Du hast bereits {streaks['current']} Tage geschafft! Weiter so!")

    with tab3:
        st.subheader("🏁 30-Tage Challenge")

        challenge_days = min(30, streaks['current'])

        st.write(f"**Aktueller Stand:** Tag {challenge_days} von 30")
        st.progress(challenge_days / 30)

        # Meilensteine
        milestones = {
            3: "🎯 Erste Woche gemeistert!",
            7: "🌟 Erste Woche geschafft!",
            14: "🚀 Zwei Wochen - Respekt!",
            21: "💫 Drei Wochen - Du rockst das!",
            30: "🏆 Monat vollendet - Unglaublich!"
        }

        for day, message in milestones.items():
            if challenge_days >= day:
                st.success(f"Tag {day}: {message}")
            else:
                days_to_go = day - challenge_days
                st.info(f"Tag {day}: Noch {days_to_go} Tage - {message}")

        # Challenge starten
        if challenge_days == 0:
            if st.button("🏁 30-Tage Challenge starten", type="primary"):
                st.session_state.challenge_start_date = datetime.now().isoformat()
                st.success("Challenge gestartet! Halte durch!")
                st.rerun()


# ============================================================================
# ERWEITERTE HEALTH-ANSICHT
# ============================================================================

def show_advanced_health_view():
    """Erweiterte Health-Ansicht mit allen neuen Features"""

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🧠 KI-Chat",
        "🎮 Gamification",
        "📖 Journal",
        "🔬 Assessments",
        "🚨 Notfallkontakte",
        "📱 Health-Daten"
    ])

    with tab1:
        show_ki_chat()

    with tab2:
        show_gamification()

    with tab3:
        show_personal_journal()

    with tab4:
        show_scientific_assessments()

    with tab5:
        show_emergency_contacts()

    with tab6:
        # Deine originale Health-Daten Funktion
        show_health_data_management()


# ============================================================================
# KI-THERAPEUT ANALYZER KLASSE (OFFLINE-KI) - ORIGINAL CODE
# ============================================================================

class KITherapeutAnalyzer:
    def __init__(self):
        self.data = {
            'sleep_data': None,
            'heart_rate_data': None,
            'consumption_data': None,
            'combined_data': None
        }
        self.results = {}
        self.correlation_results = {}

    def _parse_timestamp(self, date_str, time_str):
        """Parst Datum und Uhrzeit in datetime-Objekt"""
        try:
            datetime_str = f"{date_str} {time_str}"
            return pd.to_datetime(datetime_str)
        except Exception:
            try:
                return pd.to_datetime(date_str)
            except Exception:
                return pd.NaT

    def load_consumption_data(self, entries_data):
        """Lädt Konsumdaten mit Uhrzeiten"""
        if not entries_data:
            return None

        consumption_data = []
        for entry in entries_data:
            try:
                # Parse Datum und Uhrzeit
                entry_date = entry.get('date', '')
                entry_time = entry.get('time', '00:00')

                datetime_obj = self._parse_timestamp(entry_date, entry_time)

                if pd.isna(datetime_obj):
                    continue

                consumption_data.append({
                    'datetime': datetime_obj,
                    'date': entry_date,
                    'time': entry_time,
                    'type': entry.get('substance', 'Unbekannt'),
                    'amount': 1,
                    'dosage': entry.get('dosage', ''),
                    'rating': float(entry.get('rating', 0)),
                    'cost': float(entry.get('cost', 0)),
                    'mood': entry.get('mood', ''),
                    'setting': entry.get('setting', ''),
                    'experience': entry.get('experience', '')
                })
            except Exception:
                continue

        if consumption_data:
            df = pd.DataFrame(consumption_data)
            df = df.sort_values('datetime')
            self.data['consumption_data'] = df
            return df
        return None

    def load_health_data(self, health_data):
        """Lädt Gesundheitsdaten mit Uhrzeiten"""
        if not health_data:
            return

        sleep_data = []
        heart_rate_data = []

        for entry in health_data:
            try:
                entry_type = str(entry.get('Type', '')).lower()
                entry_value = entry.get('value', 0)
                entry_date = entry.get('date', '')
                entry_time = entry.get('time', '00:00')

                datetime_obj = self._parse_timestamp(entry_date, entry_time)

                if pd.isna(datetime_obj):
                    continue

                # Schlafdaten erkennen
                if any(word in entry_type for word in ['sleep', 'schlaf', 'deep', 'shallow', 'rem', 'wake']):
                    sleep_type = 'unknown'
                    if 'deep' in entry_type or 'tief' in entry_type:
                        sleep_type = 'deep'
                    elif 'shallow' in entry_type or 'leicht' in entry_type:
                        sleep_type = 'light'
                    elif 'rem' in entry_type:
                        sleep_type = 'rem'
                    elif 'wake' in entry_type or 'wach' in entry_type:
                        sleep_type = 'wake'
                    else:
                        sleep_type = 'total'

                    sleep_data.append({
                        'datetime': datetime_obj,
                        'date': entry_date,
                        'time': entry_time,
                        'sleep_type': sleep_type,
                        'value_minutes': float(entry_value),
                        'source': entry.get('source', 'manual')
                    })

                # Herzfrequenz erkennen
                elif any(word in entry_type for word in ['heart', 'herz', 'hr', 'pulse', 'puls']):
                    heart_rate_data.append({
                        'datetime': datetime_obj,
                        'date': entry_date,
                        'time': entry_time,
                        'heart_rate': float(entry_value),
                        'context': entry.get('notes', ''),
                        'source': entry.get('source', 'manual')
                    })

            except Exception:
                continue

        if sleep_data:
            df_sleep = pd.DataFrame(sleep_data)
            df_sleep = df_sleep.sort_values('datetime')
            self.data['sleep_data'] = df_sleep

        if heart_rate_data:
            df_hr = pd.DataFrame(heart_rate_data)
            df_hr = df_hr.sort_values('datetime')
            self.data['heart_rate_data'] = df_hr

    def combine_data(self):
        """Kombiniert alle Daten für die Analyse"""
        try:
            combined_records = []

            # Schlafdaten aggregieren (pro Tag)
            if self.data['sleep_data'] is not None and not self.data['sleep_data'].empty:
                sleep_daily = self.data['sleep_data'].copy()
                sleep_daily['date_only'] = sleep_daily['datetime'].dt.date

                for date, group in sleep_daily.groupby('date_only'):
                    record = {
                        'date': pd.to_datetime(date),
                        'date_str': str(date),
                        'total_sleep_min': group[group['sleep_type'] == 'total']['value_minutes'].sum(),
                        'deep_sleep_min': group[group['sleep_type'] == 'deep']['value_minutes'].sum(),
                        'light_sleep_min': group[group['sleep_type'] == 'light']['value_minutes'].sum(),
                        'rem_sleep_min': group[group['sleep_type'] == 'rem']['value_minutes'].sum(),
                        'wake_min': group[group['sleep_type'] == 'wake']['value_minutes'].sum(),
                        'has_sleep_data': True
                    }
                    combined_records.append(record)

            # Herzfrequenzdaten aggregieren (pro Tag)
            if self.data['heart_rate_data'] is not None and not self.data['heart_rate_data'].empty:
                hr_daily = self.data['heart_rate_data'].copy()
                hr_daily['date_only'] = hr_daily['datetime'].dt.date

                for date, group in hr_daily.groupby('date_only'):
                    # Finde oder erstelle Datensatz für diesen Tag
                    existing_record = next((r for r in combined_records if r['date_str'] == str(date)), None)

                    if existing_record:
                        existing_record['avg_heart_rate'] = group['heart_rate'].mean()
                        existing_record['max_heart_rate'] = group['heart_rate'].max()
                        existing_record['min_heart_rate'] = group['heart_rate'].min()
                        existing_record['heart_rate_std'] = group['heart_rate'].std()
                        existing_record['heart_rate_entries'] = len(group)
                        existing_record['has_heart_rate_data'] = True
                    else:
                        record = {
                            'date': pd.to_datetime(date),
                            'date_str': str(date),
                            'avg_heart_rate': group['heart_rate'].mean(),
                            'max_heart_rate': group['heart_rate'].max(),
                            'min_heart_rate': group['heart_rate'].min(),
                            'heart_rate_std': group['heart_rate'].std(),
                            'heart_rate_entries': len(group),
                            'has_heart_rate_data': True,
                            'has_sleep_data': False
                        }
                        combined_records.append(record)

            # Konsumdaten hinzufügen
            if self.data['consumption_data'] is not None and not self.data['consumption_data'].empty:
                consumption_daily = self.data['consumption_data'].copy()
                consumption_daily['date_only'] = consumption_daily['datetime'].dt.date

                for date, group in consumption_daily.groupby('date_only'):
                    existing_record = next((r for r in combined_records if r['date_str'] == str(date)), None)

                    substances = group['type'].unique().tolist()
                    avg_rating = group['rating'].mean()
                    total_cost = group['cost'].sum()

                    if existing_record:
                        existing_record['substances_today'] = substances
                        existing_record['consumption_count'] = len(group)
                        existing_record['avg_consumption_rating'] = avg_rating
                        existing_record['total_daily_cost'] = total_cost
                        existing_record['has_consumption_data'] = True

                        # Finde Konsum in den 6 Stunden vor Mitternacht (angenommene Schlafenszeit)
                        evening_consumption = group[
                            (group['datetime'].dt.hour >= 18) &
                            (group['datetime'].dt.hour <= 24)
                            ]
                        if not evening_consumption.empty:
                            existing_record['evening_substances'] = evening_consumption['type'].unique().tolist()
                            existing_record['evening_consumption_count'] = len(evening_consumption)
                    else:
                        record = {
                            'date': pd.to_datetime(date),
                            'date_str': str(date),
                            'substances_today': substances,
                            'consumption_count': len(group),
                            'avg_consumption_rating': avg_rating,
                            'total_daily_cost': total_cost,
                            'has_consumption_data': True,
                            'has_sleep_data': False,
                            'has_heart_rate_data': False
                        }
                        combined_records.append(record)

            if combined_records:
                df = pd.DataFrame(combined_records)

                # Fülle fehlende Werte
                numeric_cols = ['total_sleep_min', 'deep_sleep_min', 'light_sleep_min',
                                'rem_sleep_min', 'wake_min', 'avg_heart_rate', 'max_heart_rate',
                                'min_heart_rate', 'heart_rate_std', 'avg_consumption_rating',
                                'total_daily_cost']

                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].fillna(0)

                df = df.sort_values('date')
                self.data['combined_data'] = df
                return df

        except Exception as e:
            st.error(f"Fehler beim Kombinieren der Daten: {str(e)}")

        return None

    def perform_correlation_analysis(self):
        """Führt detaillierte Korrelationsanalyse durch (ohne scipy)"""
        if self.data['combined_data'] is None or self.data['combined_data'].empty:
            return {"status": "no_data", "message": "Keine kombinierten Daten verfügbar"}

        df = self.data['combined_data'].copy()

        # Berechne Schlafeffizienz wenn möglich
        if 'total_sleep_min' in df.columns and 'wake_min' in df.columns:
            total_bed_time = df['total_sleep_min'] + df['wake_min']
            df['sleep_efficiency'] = np.where(
                total_bed_time > 0,
                (df['total_sleep_min'] / total_bed_time) * 100,
                0
            )

        # Berechne Herzfrequenzvariabilität (HRV) Proxy
        if 'heart_rate_std' in df.columns:
            df['hrv_proxy'] = df['heart_rate_std']

        # Korrelationen berechnen (einfache Version ohne scipy)
        correlations = {}

        # Numerische Spalten für Korrelationen
        numeric_cols = []
        for col in ['total_sleep_min', 'deep_sleep_min', 'light_sleep_min',
                    'rem_sleep_min', 'sleep_efficiency', 'avg_heart_rate',
                    'hrv_proxy', 'avg_consumption_rating', 'total_daily_cost']:
            if col in df.columns and df[col].notna().any() and len(df[col].unique()) > 1:
                numeric_cols.append(col)

        # Einfache Korrelationsberechnung (ohne p-Werte)
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1:]:
                valid_data = df[[col1, col2]].dropna()
                if len(valid_data) >= 3:
                    try:
                        # Einfache Pearson-Korrelation ohne scipy
                        corr = valid_data[col1].corr(valid_data[col2])

                        if not pd.isna(corr) and abs(corr) > 0.3:
                            correlations[f"{col1}_{col2}"] = {
                                "correlation": float(corr),
                                "n": len(valid_data),
                                "interpretation": self._interpret_correlation(col1, col2, corr)
                            }
                    except Exception:
                        continue

        # Substanz-spezifische Analysen
        substance_correlations = {}
        if 'substances_today' in df.columns:
            substances_list = []
            for substances in df['substances_today'].dropna():
                if isinstance(substances, list):
                    substances_list.extend(substances)
                elif isinstance(substances, str) and substances:
                    substances_list.append(substances)

            unique_substances = list(set(substances_list))

            for substance in unique_substances:
                # Erstelle Substanz-Indikator
                df[f'used_{substance}'] = df['substances_today'].apply(
                    lambda x: substance in x if isinstance(x, list) else False
                )

                # Vergleiche Tage mit/ohne Substanz
                if df[f'used_{substance}'].any() and (~df[f'used_{substance}']).any():
                    for metric in ['avg_heart_rate', 'total_sleep_min', 'sleep_efficiency']:
                        if metric in df.columns:
                            with_substance = df[df[f'used_{substance}']][metric].mean()
                            without_substance = df[~df[f'used_{substance}']][metric].mean()

                            if with_substance > 0 and without_substance > 0:
                                diff = ((with_substance - without_substance) / without_substance) * 100

                                substance_correlations[f"{substance}_{metric}"] = {
                                    "with_substance": float(with_substance),
                                    "without_substance": float(without_substance),
                                    "difference_percent": float(diff),
                                    "interpretation": self._interpret_substance_effect(substance, metric, diff)
                                }

        self.correlation_results = {
            "status": "success",
            "total_days": len(df),
            "numeric_columns": numeric_cols,
            "correlations": correlations,
            "substance_effects": substance_correlations,
            "data_summary": {
                "days_with_sleep_data": df['has_sleep_data'].sum() if 'has_sleep_data' in df.columns else 0,
                "days_with_heart_rate_data": df[
                    'has_heart_rate_data'].sum() if 'has_heart_rate_data' in df.columns else 0,
                "days_with_consumption_data": df[
                    'has_consumption_data'].sum() if 'has_consumption_data' in df.columns else 0,
                "unique_substances": len(unique_substances) if 'substances_today' in df.columns else 0
            }
        }

        return self.correlation_results

    def _interpret_correlation(self, col1, col2, corr):
        """Interpretiert Korrelationsergebnisse"""
        interpretations = {
            ("total_sleep_min",
             "avg_heart_rate"): "Mehr Schlaf → Niedrigere Herzfrequenz" if corr < 0 else "Mehr Schlaf → Höhere Herzfrequenz",
            ("deep_sleep_min",
             "avg_heart_rate"): "Mehr Tiefschlaf → Niedrigere Herzfrequenz" if corr < 0 else "Mehr Tiefschlaf → Höhere Herzfrequenz",
            ("avg_consumption_rating",
             "avg_heart_rate"): "Höhere Bewertung → Höhere Herzfrequenz" if corr > 0 else "Höhere Bewertung → Niedrigere Herzfrequenz",
            ("total_daily_cost",
             "total_sleep_min"): "Höhere Kosten → Weniger Schlaf" if corr < 0 else "Höhere Kosten → Mehr Schlaf"
        }

        key1 = (col1, col2)
        key2 = (col2, col1)

        if key1 in interpretations:
            return interpretations[key1]
        elif key2 in interpretations:
            return interpretations[key2]
        else:
            strength = "stark" if abs(corr) > 0.7 else "mäßig" if abs(corr) > 0.4 else "schwach"
            direction = "positive" if corr > 0 else "negative"
            return f"{strength} {direction} Korrelation"

    def _interpret_substance_effect(self, substance, metric, diff):
        """Interpretiert Substanz-Effekte"""
        interpretations = {
            "Alkohol": {
                "avg_heart_rate": "Erhöht typischerweise Herzfrequenz",
                "total_sleep_min": "Reduziert oft Schlafqualität",
                "sleep_efficiency": "Senkt üblicherweise Schlafeffizienz"
            },
            "Cannabis": {
                "avg_heart_rate": "Kann Herzfrequenz erhöhen",
                "total_sleep_min": "Kann Schlafdauer beeinflussen",
                "sleep_efficiency": "Kann Schlafmuster verändern"
            },
            "MDMA": {
                "avg_heart_rate": "Stark erhöht Herzfrequenz",
                "total_sleep_min": "Beeinträchtigt Schlaf stark",
                "sleep_efficiency": "Reduziert Schlafeffizienz deutlich"
            }
        }

        if substance in interpretations and metric in interpretations[substance]:
            return interpretations[substance][metric]

        if abs(diff) > 10:
            effect = "erhöht" if diff > 0 else "verringert"
            return f"{substance} {effect} {metric} um {abs(diff):.1f}%"
        else:
            return f"{substance} zeigt keinen klaren Effekt auf {metric}"

    def perform_machine_learning_analysis(self):
        """Führt Machine Learning Analyse durch (vereinfacht ohne sklearn)"""
        if self.data['combined_data'] is None or self.data['combined_data'].empty:
            return {"status": "no_data", "message": "Keine Daten für ML-Analyse"}

        df = self.data['combined_data'].copy()

        # Vereinfachte Anomalie-Erkennung ohne sklearn
        ml_results = {
            "status": "success",
            "total_days_analyzed": len(df),
            "anomaly_percentage": 0,
            "clusters_identified": 1,
            "patterns": self._identify_simple_patterns(df),
            "recommendations": self._generate_simple_recommendations(df)
        }

        # Einfache Anomalie-Erkennung basierend auf statistischen Grenzwerten
        anomalies = []

        if 'avg_heart_rate' in df.columns:
            mean_hr = df['avg_heart_rate'].mean()
            std_hr = df['avg_heart_rate'].std()

            if std_hr > 0:
                for idx, row in df.iterrows():
                    if abs(row['avg_heart_rate'] - mean_hr) > 2 * std_hr:
                        anomalies.append(idx)

        ml_results['anomaly_days'] = len(anomalies)
        ml_results['anomaly_percentage'] = (len(anomalies) / len(df)) * 100 if len(df) > 0 else 0

        return ml_results

    def _identify_simple_patterns(self, df):
        """Identifiziert einfache Muster ohne sklearn"""
        patterns = []

        # Wochentags-Muster
        if 'date' in df.columns:
            df['weekday'] = df['date'].dt.day_name()

            if 'consumption_count' in df.columns:
                weekday_consumption = df.groupby('weekday')['consumption_count'].mean()
                if len(weekday_consumption) > 0:
                    max_day = weekday_consumption.idxmax()
                    max_value = weekday_consumption.max()
                    patterns.append(f"Höchster Konsum typischerweise am {max_day} ({max_value:.1f} Einträge)")

        # Zusammenhänge zwischen Schlaf und Herzfrequenz
        if 'total_sleep_min' in df.columns and 'avg_heart_rate' in df.columns:
            # Einfache Regression
            sleep_above_avg = df[df['total_sleep_min'] > df['total_sleep_min'].mean()]
            sleep_below_avg = df[df['total_sleep_min'] <= df['total_sleep_min'].mean()]

            if len(sleep_above_avg) > 0 and len(sleep_below_avg) > 0:
                hr_above = sleep_above_avg['avg_heart_rate'].mean()
                hr_below = sleep_below_avg['avg_heart_rate'].mean()

                if hr_above < hr_below:
                    patterns.append("Tage mit mehr Schlaf haben tendenziell niedrigere Herzfrequenz")

        return patterns if patterns else ["Keine klaren Muster identifiziert"]

    def _generate_simple_recommendations(self, df):
        """Generiert einfache Empfehlungen"""
        recommendations = []

        # Schlaf-Empfehlungen
        if 'total_sleep_min' in df.columns:
            avg_sleep = df['total_sleep_min'].mean()
            if avg_sleep < 360:  # Weniger als 6 Stunden
                recommendations.append(f"Schlafdauer erhöhen: Aktuell Ø {avg_sleep / 60:.1f}h, Ziel: 7-9h")
            elif avg_sleep > 540:  # Mehr als 9 Stunden
                recommendations.append(f"Schlafdauer möglicherweise zu hoch: Ø {avg_sleep / 60:.1f}h")

        # Herzfrequenz-Empfehlungen
        if 'avg_heart_rate' in df.columns:
            avg_hr = df['avg_heart_rate'].mean()
            if avg_hr > 80:
                recommendations.append(f"Ruheherzfrequenz senken: Aktuell Ø {avg_hr:.1f} bpm, Ziel: <70 bpm")

        # Konsum-Empfehlungen
        if 'consumption_count' in df.columns:
            avg_consumption = df['consumption_count'].mean()
            if avg_consumption > 1:
                recommendations.append(f"Konsumhäufigkeit reduzieren: Aktuell Ø {avg_consumption:.1f} Einträge/Tag")

        return recommendations if recommendations else ["Keine spezifischen Empfehlungen"]

    def generate_comprehensive_report(self):
        """Generiert einen umfassenden KI-Therapeuten Bericht"""
        if not self.data['combined_data'] or self.data['combined_data'].empty:
            return "Keine ausreichenden Daten für eine Analyse verfügbar."

        report = []
        report.append("=" * 70)
        report.append("🧠 KI-THERAPEUT ANALYSEBERICHT")
        report.append("=" * 70)
        report.append("")

        # Daten-Übersicht
        df = self.data['combined_data']
        report.append("📊 DATENÜBERSICHT:")
        report.append("-" * 40)
        report.append(f"Analysierte Tage: {len(df)}")

        if 'has_sleep_data' in df.columns:
            report.append(f"Tage mit Schlafdaten: {df['has_sleep_data'].sum()}")
        if 'has_heart_rate_data' in df.columns:
            report.append(f"Tage mit Pulsdaten: {df['has_heart_rate_data'].sum()}")
        if 'has_consumption_data' in df.columns:
            report.append(f"Tage mit Konsumdaten: {df['has_consumption_data'].sum()}")

        report.append("")

        # Korrelationsanalyse
        if self.correlation_results and self.correlation_results.get('status') == 'success':
            report.append("🔗 KORRELATIONSANALYSE:")
            report.append("-" * 40)

            correlations = self.correlation_results.get('correlations', {})
            if correlations:
                report.append("Signifikante Korrelationen gefunden:")
                for key, corr_info in list(correlations.items())[:5]:  # Zeige max 5
                    col1, col2 = key.split('_', 1)
                    report.append(f"  • {col1} ↔ {col2}: r = {corr_info['correlation']:.3f}")
                    report.append(f"    → {corr_info['interpretation']}")
            else:
                report.append("Keine signifikanten Korrelationen gefunden")

            report.append("")

            # Substanz-Effekte
            substance_effects = self.correlation_results.get('substance_effects', {})
            if substance_effects:
                report.append("💊 SUBSTANZ-EFFEKTE:")
                report.append("-" * 40)
                for key, effect_info in list(substance_effects.items())[:3]:  # Zeige max 3
                    substance, metric = key.split('_', 1)
                    report.append(f"  • {substance}:")
                    report.append(f"    - Mit Substanz: {effect_info['with_substance']:.1f}")
                    report.append(f"    - Ohne Substanz: {effect_info['without_substance']:.1f}")
                    report.append(f"    - Unterschied: {effect_info['difference_percent']:+.1f}%")
                    report.append(f"    → {effect_info['interpretation']}")

        # Machine Learning Ergebnisse
        ml_results = self.perform_machine_learning_analysis()
        if ml_results.get('status') == 'success':
            report.append("")
            report.append("🤖 MASCHINELLES LERNEN:")
            report.append("-" * 40)
            report.append(f"Anomalie-Tage: {ml_results['anomaly_days']} ({ml_results['anomaly_percentage']:.1f}%)")
            report.append(f"Identifizierte Cluster: {ml_results['clusters_identified']}")

            if ml_results['patterns']:
                report.append("Erkannte Muster:")
                for pattern in ml_results['patterns']:
                    report.append(f"  • {pattern}")

            if ml_results['recommendations']:
                report.append("Empfehlungen:")
                for rec in ml_results['recommendations']:
                    report.append(f"  → {rec}")

        # Persönliche Einschätzung
        report.append("")
        report.append("💭 PERSÖNLICHE EINSCHÄTZUNG DES KI-THERAPEUTEN:")
        report.append("-" * 40)

        insights = self._generate_personal_insights()
        for insight in insights:
            report.append(f"• {insight}")

        # Warnungen bei Risikofaktoren
        warnings = self._identify_risk_factors()
        if warnings:
            report.append("")
            report.append("⚠️ WARNUNGEN:")
            report.append("-" * 40)
            for warning in warnings:
                report.append(f"• {warning}")

        # Weitere Schritte
        report.append("")
        report.append("🔄 NÄCHSTE SCHRITTE:")
        report.append("-" * 40)
        report.append("1. Konsistente Datenerfassung fortsetzen")
        report.append("2. Auffällige Muster im Auge behalten")
        report.append("3. Bei Bedarf professionelle Hilfe suchen")
        report.append("4. Regelmäßig analysieren und anpassen")

        report.append("")
        report.append("=" * 70)
        report.append("Ende des Berichts")
        report.append("=" * 70)

        return "\n".join(report)

    def _generate_personal_insights(self):
        """Generiert persönliche Einschätzungen basierend auf den Daten"""
        insights = []
        df = self.data['combined_data']

        if 'total_sleep_min' in df.columns:
            avg_sleep = df['total_sleep_min'].mean()
            if avg_sleep < 360:
                insights.append(
                    "Deine durchschnittliche Schlafdauer scheint gering. Ausreichender Schlaf ist wichtig für Regeneration.")
            elif avg_sleep > 540:
                insights.append("Deine Schlafdauer ist überdurchschnittlich hoch. Prüfe die Schlafqualität.")

        if 'avg_heart_rate' in df.columns:
            avg_hr = df['avg_heart_rate'].mean()
            if avg_hr > 80:
                insights.append(
                    "Deine Ruheherzfrequenz ist erhöht. Dies könnte auf Stress oder körperliche Belastung hinweisen.")

        if 'has_consumption_data' in df.columns:
            consumption_days = df['has_consumption_data'].sum()
            total_days = len(df)
            consumption_ratio = consumption_days / total_days if total_days > 0 else 0

            if consumption_ratio > 0.5:
                insights.append(
                    "Konsumtage machen mehr als 50% der erfassten Zeit aus. Eine Reflexion der Konsummuster könnte hilfreich sein.")

        if not insights:
            insights.append("Basierend auf den aktuellen Daten liegen keine auffälligen Muster vor.")

        return insights

    def _identify_risk_factors(self):
        """Identifiziert potenzielle Risikofaktoren"""
        warnings = []
        df = self.data['combined_data']

        # Kombination aus hoher Herzfrequenz und wenig Schlaf
        if 'avg_heart_rate' in df.columns and 'total_sleep_min' in df.columns:
            high_hr_low_sleep = df[(df['avg_heart_rate'] > 85) & (df['total_sleep_min'] < 300)]
            if len(high_hr_low_sleep) > 3:
                warnings.append(
                    f"An {len(high_hr_low_sleep)} Tagen kombinierte sich hohe Herzfrequenz (>85 bpm) mit wenig Schlaf (<5h)")

        # Häufiger Alkoholkonsum mit schlechtem Schlaf
        if 'substances_today' in df.columns:
            alcohol_days = df[df['substances_today'].apply(
                lambda x: 'Alkohol' in x if isinstance(x, list) else False
            )]

            if len(alcohol_days) > 0 and 'sleep_efficiency' in df.columns:
                avg_efficiency_alcohol = alcohol_days[
                    'sleep_efficiency'].mean() if 'sleep_efficiency' in alcohol_days.columns else 0
                if avg_efficiency_alcohol < 75:
                    warnings.append(
                        f"An Tagen mit Alkoholkonsum war die Schlafeffizienz deutlich reduziert (Ø {avg_efficiency_alcohol:.1f}%)")

        return warnings


# ============================================================================
# HILFSFUNKTIONEN (ORIGINAL)
# ============================================================================

def get_statistics():
    """Berechnet Statistiken"""
    if not st.session_state.get('entries'):
        return None

    entries = st.session_state.entries

    # Letzte 7 und 30 Tage
    cutoff_7 = datetime.now() - timedelta(days=7)
    cutoff_30 = datetime.now() - timedelta(days=30)

    last_7_days = []
    last_30_days = []

    for entry in entries:
        try:
            entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
            if entry_date >= cutoff_30:
                last_30_days.append(entry)
                if entry_date >= cutoff_7:
                    last_7_days.append(entry)
        except Exception:
            continue

    # Substanz-Zählung
    substance_counts = {}
    for entry in entries:
        substance = entry['substance']
        substance_counts[substance] = substance_counts.get(substance, 0) + 1

    most_used = max(substance_counts.items(), key=lambda x: x[1]) if substance_counts else ('Keine', 0)

    # Durchschnittsbewertung
    ratings = [e.get('rating', 0) for e in entries if isinstance(e.get('rating'), (int, float))]
    avg_rating = np.mean(ratings) if ratings else 0

    # Gesamtkosten
    total_cost = 0
    for e in entries:
        try:
            cost_val = e.get('cost', 0)
            if isinstance(cost_val, (int, float)):
                total_cost += float(cost_val)
            elif isinstance(cost_val, str):
                # Versuche String zu float zu konvertieren
                cleaned = cost_val.replace('€', '').replace(',', '.').strip()
                if cleaned:
                    total_cost += float(cleaned)
        except (ValueError, TypeError):
            continue

    # Warnstufe
    warning = 'high' if len(last_7_days) >= 5 else 'medium' if len(last_7_days) >= 3 else 'low'

    return {
        'mostUsed': most_used,
        'avgRating': round(avg_rating, 1),
        'totalEntries': len(entries),
        'last7Days': len(last_7_days),
        'last30Days': len(last_30_days),
        'totalCost': round(total_cost, 2),
        'warning': warning,
        'substanceCounts': substance_counts
    }


def init_session_state():
    """Initialisiert alle Session State Variablen"""
    defaults = {
        'entries': [],
        'goals': [],
        'health_data': [],
        'selected_entries': [],
        'average_data': None,
        'show_form': False,
        'editing_entry': None,
        'last_save_time': None,
        'auto_backup_counter': 0,
        'editing_health_entry': None,
        'current_page': "📋 Einträge",
        'entry_to_delete': None,
        'health_to_delete': None,
        'selected_health_date': "Alle Daten",
        'ki_therapeut_analyzer': KITherapeutAnalyzer(),
        'ki_analysis_results': None,
        'correlation_analysis_results': None,
        'journal_entries': [],
        'gamification': GamificationSystem(),
        'chat_history': []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Lade gespeicherte Daten
    load_all_data()


def save_all_data():
    """Speichert alle Daten in JSON-Dateien"""
    try:
        # Hauptdaten
        main_data = {
            'entries': st.session_state.entries,
            'goals': st.session_state.goals,
            'health_data': st.session_state.health_data,
            'journal_entries': st.session_state.journal_entries,
            'last_save': datetime.now().isoformat(),
            'version': '4.0'
        }

        with open(DATA_DIR / 'main_data.json', 'w', encoding='utf-8') as f:
            json.dump(main_data, f, ensure_ascii=False, indent=2, default=str)

        st.session_state.last_save_time = datetime.now()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False


def load_all_data():
    """Lädt alle Daten aus JSON-Dateien"""
    try:
        main_file = DATA_DIR / 'main_data.json'
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Prüfe Version
                version = data.get('version', '1.0')
                st.session_state.entries = data.get('entries', [])
                st.session_state.goals = data.get('goals', [])
                st.session_state.health_data = data.get('health_data', [])
                st.session_state.journal_entries = data.get('journal_entries', [])

                # Konvertiere Datum-Strings zurück zu datetime für last_save_time
                last_save_str = data.get('last_save', datetime.now().isoformat())
                try:
                    st.session_state.last_save_time = datetime.fromisoformat(last_save_str)
                except Exception:
                    st.session_state.last_save_time = datetime.now()
    except Exception as e:
        st.warning(f"Konnte gespeicherte Daten nicht laden: {e}")


def create_backup():
    """Erstellt automatisches Backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f"backup_{timestamp}.json"

        backup_data = {
            'entries': st.session_state.entries,
            'goals': st.session_state.goals,
            'health_data': st.session_state.health_data,
            'journal_entries': st.session_state.journal_entries,
            'backup_date': datetime.now().isoformat(),
            'version': '4.0'
        }

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

        # Behalte nur die letzten 7 Backups
        backup_files = sorted(BACKUP_DIR.glob("backup_*.json"))
        if len(backup_files) > 7:
            for old_file in backup_files[:-7]:
                try:
                    old_file.unlink()
                except Exception:
                    pass

        return True
    except Exception as e:
        st.error(f"Backup-Fehler: {e}")
        return False


def auto_save_check():
    """Prüft ob automatisch gespeichert werden soll"""
    if not st.session_state.entries:
        return

    # Speichere alle 10 neuen Einträge oder nach 5 Minuten
    save_trigger = False

    if st.session_state.last_save_time:
        time_since_save = (datetime.now() - st.session_state.last_save_time).total_seconds()
        if time_since_save > 300:  # 5 Minuten
            save_trigger = True

    if st.session_state.auto_backup_counter >= 10:
        save_trigger = True
        st.session_state.auto_backup_counter = 0

    if save_trigger:
        if save_all_data():
            create_backup()
            st.session_state.auto_backup_counter = 0


def get_time_since(timestamp):
    """Berechnet die vergangene Zeit seit einem Timestamp"""
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except Exception:
            return "Unbekannt"

    now = datetime.now()
    diff = now - timestamp
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    return "Gerade eben"


def parse_health_csv(csv_text, filename=None):
    """Parst Health CSV-Daten mit verbesserter Uhrzeit-Verarbeitung"""
    entries = []
    try:
        # Prüfe verschiedene Trennzeichen
        possible_delimiters = [',', ';', '\t']

        for delimiter in possible_delimiters:
            try:
                csv_reader = csv.DictReader(StringIO(csv_text), delimiter=delimiter)
                first_row = next(csv_reader)
                csv_reader = csv.DictReader(StringIO(csv_text), delimiter=delimiter)
                break
            except Exception:
                continue
        else:
            # Fallback auf Komma
            csv_reader = csv.DictReader(StringIO(csv_text))

        for row in csv_reader:
            processed_row = {}

            # 1. Datum und Uhrzeit finden und verarbeiten
            date_str = ""
            time_str = "00:00"

            for field_name, field_value in row.items():
                if field_value and field_name:
                    field_lower = field_name.lower()
                    field_value_str = str(field_value).strip()

                    # Datum extrahieren
                    if any(word in field_lower for word in ['date', 'datum', 'tag', 'day']):
                        date_str = field_value_str

                    # Uhrzeit extrahieren
                    elif any(word in field_lower for word in ['time', 'zeit', 'timestamp', 'uhrzeit']):
                        # Versuche Uhrzeit zu extrahieren
                        time_formats = ['%H:%M:%S', '%H:%M', '%H.%M.%S', '%H.%M']
                        for fmt in time_formats:
                            try:
                                time_obj = datetime.strptime(field_value_str, fmt)
                                time_str = time_obj.strftime('%H:%M')
                                break
                            except Exception:
                                continue

                    # Falls das Feld sowohl Datum als auch Uhrzeit enthält
                    elif ' ' in field_value_str and any(sep in field_value_str for sep in ['-', '.', '/']):
                        parts = field_value_str.split(' ')
                        if len(parts) >= 2:
                            date_str = parts[0]
                            time_part = parts[1]
                            for fmt in ['%H:%M:%S', '%H:%M', '%H.%M.%S', '%H.%M']:
                                try:
                                    time_obj = datetime.strptime(time_part, fmt)
                                    time_str = time_obj.strftime('%H:%M')
                                    break
                                except Exception:
                                    continue

            # Wenn kein Datum gefunden, verwende aktuelles Datum
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d')

            # Versuche Datum zu parsen
            date_formats = [
                '%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d', '%m/%d/%Y',
                '%d-%m-%Y', '%Y.%m.%d', '%d.%m.%y', '%y-%m-%d'
            ]

            date_obj = None
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except Exception:
                    continue

            if date_obj is None:
                # Fallback: Versuche verschiedene Trennzeichen
                for sep in ['-', '.', '/']:
                    parts = date_str.split(sep)
                    if len(parts) == 3:
                        try:
                            # Versuche verschiedene Reihenfolgen
                            for order in [('%Y', '%m', '%d'), ('%d', '%m', '%Y'), ('%m', '%d', '%Y')]:
                                fmt = sep.join(order)
                                try:
                                    date_obj = datetime.strptime(date_str, fmt)
                                    break
                                except Exception:
                                    continue
                            if date_obj:
                                break
                        except Exception:
                            continue

            if date_obj is None:
                # Wenn alles fehlschlägt, aktuelles Datum verwenden
                date_obj = datetime.now()
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = date_obj.strftime('%Y-%m-%d')

            # 2. Datentyp und Wert extrahieren
            data_type = "Unknown"
            value = 0

            for field_name, field_value in row.items():
                field_lower = field_name.lower()
                if field_lower in ['date', 'datum', 'time', 'zeit', 'timestamp', 'uhrzeit']:
                    continue

                if field_value and str(field_value).strip():
                    try:
                        # Versuche numerischen Wert zu extrahieren
                        val_str = str(field_value).replace(',', '.').strip()
                        # Entferne nicht-numerische Zeichen (außer Punkt und Minus)
                        val_clean = ''.join(c for c in val_str if c.isdigit() or c in '.-')
                        if val_clean:
                            value = float(val_clean)

                            # Bestimme Datentyp basierend auf Feldnamen
                            if any(word in field_lower for word in ['heart', 'herz', 'hr', 'pulse', 'puls']):
                                data_type = "Herzfrequenz"
                            elif any(word in field_lower for word in ['sleep', 'schlaf', 'ruhe']):
                                data_type = "Schlaf"
                            elif any(word in field_lower for word in ['deep', 'tief']):
                                data_type = "Tiefschlaf"
                            elif any(word in field_lower for word in ['shallow', 'leicht']):
                                data_type = "Leichtschlaf"
                            elif 'rem' in field_lower:
                                data_type = "REM-Schlaf"
                            elif any(word in field_lower for word in ['wake', 'wach']):
                                data_type = "Wachzeit"
                            elif any(word in field_lower for word in ['step', 'schritt']):
                                data_type = "Schritte"
                            else:
                                # Allgemeiner Datentyp
                                data_type = field_name

                            break
                    except Exception:
                        continue

            processed_row = {
                'id': int(time_module.time() * 1000) + len(entries),
                'Type': data_type,
                'value': value,
                'date': date_str,
                'time': time_str,
                'source': filename or 'imported',
                'original_row': row
            }

            entries.append(processed_row)

        return entries
    except Exception as e:
        st.error(f"Fehler beim Parsen der CSV: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return []


def validate_entry(entry):
    """Validiert Tagebuch-Einträge"""
    errors = []

    if not entry.get('substance') or not str(entry.get('substance')).strip():
        errors.append("Substanz ist erforderlich")

    try:
        datetime.strptime(entry.get('date', ''), '%Y-%m-%d')
    except (ValueError, TypeError):
        errors.append("Ungültiges Datumsformat (YYYY-MM-DD erforderlich)")

    try:
        cost = float(entry.get('cost', 0))
        if cost < 0:
            errors.append("Kosten dürfen nicht negativ sein")
    except (ValueError, TypeError):
        errors.append("Ungültiger Kostenwert")

    rating = entry.get('rating', 0)
    if not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
        errors.append("Bewertung muss zwischen 1 und 5 liegen")

    return errors


def anonymize_export_data(entries, full_export=False):
    """Entfernt persönlich identifizierbare Informationen für sicheren Export"""
    if full_export:
        return entries.copy()

    anonymized = []
    for entry in entries:
        anonymized.append({
            'substance': entry.get('substance'),
            'date': entry.get('date', '')[:7] if entry.get('date') else '',  # Nur Jahr-Monat
            'dosage': entry.get('dosage'),
            'rating': entry.get('rating'),
            'cost': entry.get('cost')
            # Erfahrung, Stimmung, Setting werden entfernt für Anonymität
        })
    return anonymized


def export_data(selected_only=False, anonymize=True):
    """Exportiert Daten als Text"""
    if selected_only and st.session_state.selected_entries:
        data_to_export = [e for e in st.session_state.entries if e['id'] in st.session_state.selected_entries]
    else:
        data_to_export = st.session_state.entries

    if not data_to_export:
        return ""

    # Anonymisiere Daten wenn gewünscht
    if anonymize:
        export_data_list = anonymize_export_data(data_to_export, full_export=False)
    else:
        export_data_list = data_to_export

    export_text = f"""SUBSTANZ-TAGEBUCH EXPORT
Erstellt von: Substanz-Tagebuch App mit KI-Therapeut (© {datetime.now().year})
Export-Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Anzahl Einträge: {len(export_data_list)}
Anonymisiert: {'Ja' if anonymize else 'Nein'}

{'=' * 50}

"""

    for e in export_data_list:
        export_text += f"""Substanz: {e.get('substance', 'N/A')}
Datum: {e.get('date', 'N/A')} {e.get('time', '')}
Dosierung: {e.get('dosage', 'Keine Angabe')}
Kosten: {e.get('cost', '0.00')} €
Bewertung: {e.get('rating', 'N/A')}/5
"""
        if not anonymize:
            export_text += f"""Stimmung: {e.get('mood', 'Keine Angabe')}
Setting: {e.get('setting', 'Keine Angabe')}
Erfahrung: {e.get('experience', 'Keine Angabe')}
"""
        export_text += f"{'=' * 50}\n\n"

    return export_text


def perform_ki_therapeut_analysis():
    """Führt KI-Therapeut Analyse durch"""
    if not st.session_state.health_data and not st.session_state.entries:
        st.error("Bitte importiere zuerst Health-Daten und/oder trage Konsumeinträge ein.")
        return False

    with st.spinner("🧠 KI-Therapeut analysiert Daten..."):
        try:
            # Initialisiere Analyzer
            analyzer = st.session_state.ki_therapeut_analyzer

            # Lade alle verfügbaren Daten
            if st.session_state.health_data:
                analyzer.load_health_data(st.session_state.health_data)

            if st.session_state.entries:
                analyzer.load_consumption_data(st.session_state.entries)

            # Kombiniere Daten
            combined_data = analyzer.combine_data()

            if combined_data is None or combined_data.empty:
                st.error("Keine kombinierbaren Daten gefunden.")
                return False

            # Führe Korrelationsanalyse durch
            correlation_results = analyzer.perform_correlation_analysis()

            # Generiere Bericht
            report = analyzer.generate_comprehensive_report()

            # Speichere Ergebnisse
            st.session_state.ki_analysis_results = report
            st.session_state.correlation_analysis_results = correlation_results

            st.success("✅ KI-Therapeut Analyse abgeschlossen!")
            return True

        except Exception as e:
            st.error(f"❌ Fehler bei der KI-Therapeut Analyse: {str(e)}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            return False


def handle_health_import(health_entries, import_option):
    """Verarbeitet Health-Daten Import"""
    if import_option == "Bestehende Daten ersetzen":
        st.session_state.health_data = health_entries
        st.success("✅ Alle bestehenden Daten wurden ersetzt!")
    elif import_option == "Nur neue Daten hinzufügen":
        existing_keys = set()
        for h in st.session_state.health_data:
            key = f"{h.get('date', '')}_{h.get('time', '')}_{h.get('Type', '')}_{h.get('value', '')}"
            existing_keys.add(key)

        new_entries = []
        for h in health_entries:
            key = f"{h.get('date', '')}_{h.get('time', '')}_{h.get('Type', '')}_{h.get('value', '')}"
            if key not in existing_keys:
                new_entries.append(h)

        st.session_state.health_data.extend(new_entries)
        st.success(f"✅ {len(new_entries)} neue Datenpunkte hinzugefügt")
    else:
        st.session_state.health_data.extend(health_entries)
        st.success(f"✅ {len(health_entries)} Datenpunkte hinzugefügt")

    st.session_state.auto_backup_counter += 1
    save_all_data()
    time_module.sleep(1)
    st.rerun()


# ============================================================================
# SEITEN-FUNKTIONEN (ORIGINAL)
# ============================================================================

def show_list_view():
    """Zeigt Listen-Ansicht"""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("📋 Einträge")

    with col2:
        if st.button("➕ Neuer Eintrag", type="primary", width='stretch'):
            st.session_state.show_form = True
            st.session_state.editing_entry = None

    # Bearbeitungsmodus
    if st.session_state.editing_entry:
        # Finde den zu bearbeitenden Eintrag
        entry_to_edit = None
        for e in st.session_state.entries:
            if e['id'] == st.session_state.editing_entry:
                entry_to_edit = e
                break

        if entry_to_edit:
            st.subheader("✏️ Eintrag bearbeiten")
            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    substance = st.text_input(
                        "Substanz *",
                        value=entry_to_edit.get('substance', '')
                    )
                    date = st.date_input(
                        "Datum *",
                        value=datetime.strptime(entry_to_edit['date'], '%Y-%m-%d')
                    )
                    time_val = st.time_input(
                        "Uhrzeit *",
                        value=datetime.strptime(entry_to_edit['time'], '%H:%M').time()
                    )

                with col2:
                    dosage = st.text_input(
                        "Dosierung (optional)",
                        value=entry_to_edit.get('dosage', '')
                    )
                    cost = st.number_input(
                        "Kosten € (optional)",
                        min_value=0.0,
                        value=float(entry_to_edit.get('cost', 0)),
                        step=0.5,
                        format="%.2f"
                    )
                    rating = st.slider(
                        "Bewertung (1-5)",
                        1, 5,
                        value=int(entry_to_edit.get('rating', 3))
                    )

                mood = st.selectbox(
                    "Stimmung vorher (optional)",
                    ["", "Sehr gut", "Gut", "Neutral", "Schlecht", "Sehr schlecht",
                     "Gestresst", "Entspannt", "Müde", "Energetisch", "Traurig", "Glücklich"],
                    index=0 if not entry_to_edit.get('mood') else [
                        "", "Sehr gut", "Gut", "Neutral", "Schlecht", "Sehr schlecht",
                        "Gestresst", "Entspannt", "Müde", "Energetisch", "Traurig", "Glücklich"
                    ].index(entry_to_edit.get('mood', ''))
                )

                setting = st.selectbox(
                    "Setting (optional)",
                    ["", "Zuhause", "Party/Club", "Natur", "Alleine", "Mit Freunden",
                     "In Gesellschaft", "Konzert", "Festival", "Arbeit"],
                    index=0 if not entry_to_edit.get('setting') else [
                        "", "Zuhause", "Party/Club", "Natur", "Alleine", "Mit Freunden",
                        "In Gesellschaft", "Konzert", "Festival", "Arbeit"
                    ].index(entry_to_edit.get('setting', ''))
                )

                experience = st.text_area(
                    "Erfahrung (optional)",
                    value=entry_to_edit.get('experience', ''),
                    height=100
                )

                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Änderungen speichern", type="primary")
                with col2:
                    if st.form_submit_button("❌ Abbrechen"):
                        st.session_state.editing_entry = None
                        st.rerun()

                if submitted:
                    if not substance.strip():
                        st.error("❌ Bitte gib eine Substanz an!")
                    else:
                        # Validiere Eingaben
                        new_entry = {
                            'id': entry_to_edit['id'],
                            'substance': substance.strip(),
                            'date': date.strftime('%Y-%m-%d'),
                            'time': time_val.strftime('%H:%M'),
                            'dosage': dosage.strip() if dosage else "",
                            'rating': rating,
                            'experience': experience.strip() if experience else "",
                            'mood': mood if mood else "",
                            'setting': setting if setting else "",
                            'cost': float(cost),
                            'timestamp': datetime.combine(date, time_val).timestamp()
                        }

                        errors = validate_entry(new_entry)
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            # Aktualisiere den Eintrag
                            for i, e in enumerate(st.session_state.entries):
                                if e['id'] == entry_to_edit['id']:
                                    st.session_state.entries[i] = new_entry
                                    break

                            st.session_state.editing_entry = None
                            st.session_state.auto_backup_counter += 1
                            save_all_data()
                            st.success("✅ Eintrag aktualisiert!")
                            time_module.sleep(1)
                            st.rerun()

    # Neuer Eintrag-Formular
    elif st.session_state.show_form:
        with st.form("entry_form", clear_on_submit=True):
            st.subheader("Neuer Eintrag")

            col1, col2 = st.columns(2)

            with col1:
                substance = st.selectbox(
                    "Substanz *",
                    options=[""] + ALL_SUBSTANCES + ["Andere..."],
                    help="Wähle eine Substanz oder gib eine eigene ein"
                )
                if substance == "Andere...":
                    substance = st.text_input("Eigene Substanz")

                date = st.date_input("Datum *", value=datetime.now())
                time_val = st.time_input("Uhrzeit *", value=datetime.now().time())

            with col2:
                dosage = st.text_input("Dosierung (optional)", placeholder="z.B. 10mg, 1 Joint")
                cost = st.number_input("Kosten € (optional)", min_value=0.0, value=0.0, step=0.5, format="%.2f")
                rating = st.slider("Bewertung (1-5)", 1, 5, 3)

            mood = st.selectbox(
                "Stimmung vorher (optional)",
                ["", "Sehr gut", "Gut", "Neutral", "Schlecht", "Sehr schlecht",
                 "Gestresst", "Entspannt", "Müde", "Energetisch", "Traurig", "Glücklich"]
            )

            setting = st.selectbox(
                "Setting (optional)",
                ["", "Zuhause", "Party/Club", "Natur", "Alleine", "Mit Freunden",
                 "In Gesellschaft", "Konzert", "Festival", "Arbeit"]
            )

            experience = st.text_area("Erfahrung (optional)",
                                      placeholder="Beschreibe deine Erfahrung...",
                                      height=100)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Eintrag speichern", type="primary")
            with col2:
                if st.form_submit_button("❌ Abbrechen"):
                    st.session_state.show_form = False
                    st.rerun()

            if submitted:
                if not substance:
                    st.error("❌ Bitte gib eine Substanz an!")
                else:
                    new_entry = {
                        'id': int(time_module.time() * 1000),
                        'substance': substance if substance != "Andere..." else "",
                        'date': date.strftime('%Y-%m-%d'),
                        'time': time_val.strftime('%H:%M'),
                        'dosage': dosage if dosage else "",
                        'rating': rating,
                        'experience': experience if experience else "",
                        'mood': mood if mood else "",
                        'setting': setting if setting else "",
                        'cost': float(cost),
                        'timestamp': datetime.combine(date, time_val).timestamp()
                    }

                    # Validiere Eingaben
                    errors = validate_entry(new_entry)
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        st.session_state.entries.append(new_entry)
                        st.session_state.show_form = False
                        st.session_state.auto_backup_counter += 1
                        save_all_data()
                        st.success("✅ Eintrag gespeichert!")
                        time_module.sleep(1)
                        st.rerun()

    # Einträge anzeigen
    if not st.session_state.entries:
        st.info("📝 Noch keine Einträge vorhanden. Füge deinen ersten Eintrag hinzu!")
        return

    # Filter-Optionen
    with st.expander("🔍 Filter", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            substances = sorted(set(e['substance'] for e in st.session_state.entries))
            filter_substance = st.multiselect(
                "Nach Substanz filtern",
                options=substances,
                default=[]
            )

        with col2:
            dates = sorted(set(e['date'] for e in st.session_state.entries))
            if dates:
                min_date = datetime.strptime(min(dates), '%Y-%m-%d').date()
                max_date = datetime.strptime(max(dates), '%Y-%m-%d').date()
                date_range = st.date_input(
                    "Zeitraum",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                date_range = None

        with col3:
            min_rating = st.slider("Minimale Bewertung", 1, 5, 1)

    # Einträge filtern
    filtered_entries = st.session_state.entries.copy()

    if filter_substance:
        filtered_entries = [e for e in filtered_entries if e['substance'] in filter_substance]

    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        filtered_entries = [e for e in filtered_entries if start_str <= e['date'] <= end_str]

    filtered_entries = [e for e in filtered_entries if e.get('rating', 0) >= min_rating]

    # Sortieren (neueste zuerst)
    filtered_entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    # Bulk-Auswahl
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"**Gefundene Einträge:** {len(filtered_entries)}")
    with col2:
        if st.button("📋 Alle auswählen", width='stretch'):
            st.session_state.selected_entries = [e['id'] for e in filtered_entries]
            st.rerun()

    # Einträge anzeigen
    for entry in filtered_entries:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                # Header
                st.markdown(f"### {entry['substance']}")

                # Metadaten
                metadata = []
                metadata.append(f"📅 {entry['date']}")
                metadata.append(f"⏰ {entry['time']}")
                if entry.get('dosage'):
                    metadata.append(f"⚖️ {entry['dosage']}")
                if entry.get('cost') and float(entry['cost']) > 0:
                    metadata.append(f"💰 {entry['cost']}€")

                st.write(" • ".join(metadata))

                # Bewertung
                rating_val = entry.get('rating', 0)
                stars = "⭐" * rating_val + "☆" * (5 - rating_val)
                st.write(f"**Bewertung:** {stars}")

                # Weitere Details
                if entry.get('mood'):
                    st.write(f"**Stimmung:** {entry['mood']}")
                if entry.get('setting'):
                    st.write(f"**Setting:** {entry['setting']}")

                # Erfahrung (kollabiert)
                if entry.get('experience'):
                    with st.expander("📝 Erfahrung lesen"):
                        st.write(entry['experience'])

            with col2:
                # Auswahl-Button
                is_selected = entry['id'] in st.session_state.selected_entries
                button_text = "✓ Ausgewählt" if is_selected else "○ Auswählen"
                button_type = "primary" if is_selected else "secondary"

                if st.button(button_text, key=f"sel_{entry['id']}", width='stretch', type=button_type):
                    if is_selected:
                        st.session_state.selected_entries.remove(entry['id'])
                    else:
                        st.session_state.selected_entries.append(entry['id'])
                    st.rerun()

            with col3:
                # Bearbeiten & Löschen Buttons
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️", key=f"edit_{entry['id']}", width='stretch', help="Bearbeiten"):
                        st.session_state.editing_entry = entry['id']
                        st.session_state.show_form = False
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{entry['id']}", width='stretch', help="Löschen"):
                        st.session_state['entry_to_delete'] = entry['id']

            # Lösch-Bestätigung außerhalb des Containers
            if st.session_state.get('entry_to_delete') == entry['id']:
                st.warning(f"Möchtest du den Eintrag '{entry['substance']}' am {entry['date']} wirklich löschen?")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button(f"✅ Ja, löschen", key=f"confirm_del_{entry['id']}"):
                        st.session_state.entries = [e for e in st.session_state.entries
                                                    if e['id'] != entry['id']]
                        st.session_state.auto_backup_counter += 1
                        save_all_data()
                        st.session_state['entry_to_delete'] = None
                        st.success("🗑️ Eintrag gelöscht!")
                        time_module.sleep(0.5)
                        st.rerun()
                with col2:
                    if st.button("❌ Nein, abbrechen", key=f"cancel_del_{entry['id']}"):
                        st.session_state['entry_to_delete'] = None
                        st.rerun()

            st.divider()


def show_analytics_view():
    """Zeigt Statistiken-Ansicht"""
    st.header("📊 Statistiken & Analysen")

    if not st.session_state.entries:
        st.info("📝 Keine Daten verfügbar. Füge zuerst Einträge hinzu.")
        return

    stats = get_statistics()
    if not stats:
        return

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Gesamte Einträge", stats['totalEntries'])

    with col2:
        st.metric("Ø Bewertung", f"{stats['avgRating']}/5")

    with col3:
        warning_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(stats['warning'], "⚪")
        st.metric("Aktivität (7 Tage)", f"{warning_icon} {stats['last7Days']}")

    with col4:
        if stats['totalCost'] > 0:
            st.metric("Gesamtkosten", f"{stats['totalCost']}€")
        else:
            st.metric("Häufigste Substanz", stats['mostUsed'][0])

    st.divider()

    # Charts
    tab1, tab2, tab3 = st.tabs(["📈 Verlauf", "🍃 Verteilung", "😊 Stimmungen"])

    with tab1:
        # Zeitverlauf der Bewertungen
        if len(st.session_state.entries) > 1:
            # Daten für Plot vorbereiten
            plot_data = []
            for entry in st.session_state.entries:
                try:
                    date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
                    plot_data.append({
                        'Datum': date_obj,
                        'Bewertung': entry.get('rating', 0),
                        'Substanz': entry['substance'],
                        'Kosten': float(entry.get('cost', 0))
                    })
                except Exception:
                    continue

            if plot_data:
                df = pd.DataFrame(plot_data)
                df = df.sort_values('Datum')

                # Letzte 30 Tage
                cutoff = datetime.now() - timedelta(days=30)
                df_recent = df[df['Datum'] >= cutoff]

                if not df_recent.empty:
                    fig = px.line(df_recent, x='Datum', y='Bewertung',
                                  color='Substanz', markers=True,
                                  title='Bewertungsverlauf (letzte 30 Tage)')
                    fig.update_layout(xaxis_title='Datum', yaxis_title='Bewertung (1-5)',
                                      yaxis_range=[0, 5.5])
                    st.plotly_chart(fig, width='stretch')

                    # Kostenverlauf
                    if df_recent['Kosten'].sum() > 0:
                        fig2 = px.bar(df_recent, x='Datum', y='Kosten',
                                      color='Substanz',
                                      title='Kostenverlauf (letzte 30 Tage)')
                        fig2.update_layout(xaxis_title='Datum', yaxis_title='Kosten (€)')
                        st.plotly_chart(fig2, width='stretch')
                else:
                    st.info("Keine Daten der letzten 30 Tage verfügbar")
        else:
            st.info("📈 Mehrere Einträge benötigt für Zeitverlauf")

    with tab2:
        # Substanz-Verteilung
        if st.session_state.entries:
            substance_counts = stats['substanceCounts']

            if substance_counts:
                # Balkendiagramm
                fig = px.bar(
                    x=list(substance_counts.keys()),
                    y=list(substance_counts.values()),
                    title='Verteilung nach Substanzen',
                    labels={'x': 'Substanz', 'y': 'Anzahl'},
                    color=list(substance_counts.values()),
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, width='stretch')

                # Auch als Tabelle
                with st.expander("📋 Detaillierte Tabelle"):
                    df_counts = pd.DataFrame(
                        list(substance_counts.items()),
                        columns=['Substanz', 'Anzahl']
                    ).sort_values('Anzahl', ascending=False)

                    # Füge durchschnittliche Bewertung hinzu
                    avg_ratings = []
                    for substance in df_counts['Substanz']:
                        ratings = [e.get('rating', 0) for e in st.session_state.entries
                                   if e['substance'] == substance and isinstance(e.get('rating'), (int, float))]
                        avg_rating = np.mean(ratings) if ratings else 0
                        avg_ratings.append(round(avg_rating, 1))

                    df_counts['Ø Bewertung'] = avg_ratings
                    st.dataframe(df_counts, width='stretch', hide_index=True)
            else:
                st.info("Keine Substanz-Daten verfügbar")

    with tab3:
        # Stimmungs-Verteilung
        mood_counts = {}
        for entry in st.session_state.entries:
            if entry.get('mood'):
                mood = entry['mood']
                mood_counts[mood] = mood_counts.get(mood, 0) + 1

        if mood_counts:
            fig = px.pie(
                values=list(mood_counts.values()),
                names=list(mood_counts.keys()),
                title='Stimmungsverteilung',
                hole=0.3
            )
            st.plotly_chart(fig, width='stretch')

            # Korrelation Stimmung - Bewertung
            mood_rating_data = []
            for entry in st.session_state.entries:
                if entry.get('mood') and entry.get('rating'):
                    mood_rating_data.append({
                        'Stimmung': entry['mood'],
                        'Bewertung': entry['rating']
                    })

            if mood_rating_data:
                df_mood_rating = pd.DataFrame(mood_rating_data)
                mood_avg_rating = df_mood_rating.groupby('Stimmung')['Bewertung'].mean().reset_index()

                fig2 = px.bar(mood_avg_rating, x='Stimmung', y='Bewertung',
                              title='Durchschnittliche Bewertung nach Stimmung')
                fig2.update_layout(yaxis_title='Ø Bewertung', yaxis_range=[0, 5.5])
                st.plotly_chart(fig2, width='stretch')
        else:
            st.info("😊 Keine Stimmungsdaten verfügbar")


def show_calendar_view():
    """Zeigt Kalender-Ansicht"""
    st.header("📅 Kalender-Übersicht")

    if not st.session_state.entries:
        st.info("📅 Keine Einträge verfügbar")
        return

    # Filter nach Jahr/Monat
    years_months = []
    for e in st.session_state.entries:
        try:
            date_obj = datetime.strptime(e['date'], '%Y-%m-%d')
            year_month = date_obj.strftime('%Y-%m')
            if year_month not in years_months:
                years_months.append(year_month)
        except Exception:
            continue

    years_months = sorted(years_months, reverse=True)

    selected_period = st.selectbox(
        "Zeitraum auswählen",
        options=["Alle Monate"] + years_months,
        index=0
    )

    # Monate extrahieren und gruppieren
    months_data = {}
    for entry in st.session_state.entries:
        try:
            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            year_month = date_obj.strftime('%Y-%m')

            if selected_period != "Alle Monate" and year_month != selected_period:
                continue

            if year_month not in months_data:
                months_data[year_month] = []
            months_data[year_month].append(entry)
        except Exception:
            continue

    # Für jeden Monat Kalender anzeigen
    for year_month in sorted(months_data.keys(), reverse=True):
        year, month = map(int, year_month.split('-'))
        month_name = datetime(year, month, 1).strftime('%B %Y')

        st.subheader(month_name)

        # Kalender erstellen
        first_day = datetime(year, month, 1)
        days_in_month = (datetime(year, month + 1, 1) if month < 12
                         else datetime(year + 1, 1, 1)) - timedelta(days=1)
        days_in_month = days_in_month.day

        # Wochentage-Header
        cols = st.columns(7)
        weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekdays[i]}</div>",
                            unsafe_allow_html=True)

        # Tage des Monats
        day_counter = 0
        for week in range(6):  # Max 6 Wochen
            cols = st.columns(7)

            for day_of_week in range(7):
                with cols[day_of_week]:
                    if day_counter < days_in_month:
                        day_num = day_counter + 1
                        date_str = f"{year}-{month:02d}-{day_num:02d}"

                        # Einträge an diesem Tag finden
                        day_entries = [e for e in months_data[year_month]
                                       if e['date'] == date_str]

                        if day_entries:
                            # Tag mit Einträgen - farbig markieren
                            substances = list(set(e['substance'] for e in day_entries))

                            # Anzahl der Einträge
                            num_entries = len(day_entries)

                            # Farbe basierend auf Anzahl der Einträge
                            if num_entries >= 3:
                                bg_color = "#ef4444"  # Rot für viele Einträge
                            elif num_entries == 2:
                                bg_color = "#f59e0b"  # Orange für 2 Einträge
                            else:
                                bg_color = "#10b981"  # Grün für 1 Eintrag

                            st.markdown(
                                f'<div style="background-color: {bg_color}; color: white; '
                                f'padding: 8px; border-radius: 8px; margin: 2px; '
                                f'text-align: center;">'
                                f'<strong>{day_num}</strong><br>'
                                f'<small>{num_entries} Eintr.</small>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                            # Info-Button
                            col_info, col_empty = st.columns([1, 5])
                            with col_info:
                                if st.button(f"ℹ️", key=f"info_{date_str}"):
                                    st.session_state[f"show_info_{date_str}"] = True

                            # Info Popover simulieren
                            if st.session_state.get(f"show_info_{date_str}"):
                                with st.expander(f"Details für {date_str}", expanded=True):
                                    st.write(f"**{num_entries} Einträge**")
                                    for i, entry in enumerate(day_entries, 1):
                                        st.write(f"**{i}. {entry['substance']}**")
                                        st.write(f"⏰ {entry['time']}")
                                        if entry.get('dosage'):
                                            st.write(f"⚖️ {entry['dosage']}")
                                        rating = entry.get('rating', 0)
                                        stars = "★" * int(rating) + "☆" * (5 - int(rating))
                                        st.write(f"⭐ {stars}")
                                        if entry.get('mood'):
                                            st.write(f"😊 {entry['mood']}")
                                        if entry.get('experience'):
                                            with st.expander("Erfahrung"):
                                                st.write(entry['experience'])
                                        st.divider()

                                    if st.button("Schließen", key=f"close_info_{date_str}"):
                                        st.session_state[f"show_info_{date_str}"] = False
                                        st.rerun()
                        else:
                            # Leerer Tag
                            st.markdown(
                                f'<div style="background-color: rgba(255,255,255,0.05); '
                                f'padding: 8px; border-radius: 8px; margin: 2px; '
                                f'text-align: center;">{day_num}</div>',
                                unsafe_allow_html=True
                            )

                        day_counter += 1

                if day_counter >= days_in_month:
                    break

            if day_counter >= days_in_month:
                break

        # Monatsstatistik
        month_entries = months_data[year_month]
        if month_entries:
            month_substances = set(e['substance'] for e in month_entries)
            ratings = [e.get('rating', 0) for e in month_entries if isinstance(e.get('rating'), (int, float))]
            month_avg_rating = np.mean(ratings) if ratings else 0

            month_total_cost = 0
            for e in month_entries:
                try:
                    cost_val = e.get('cost', 0)
                    if isinstance(cost_val, (int, float)):
                        month_total_cost += float(cost_val)
                except (ValueError, TypeError):
                    continue

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Einträge", len(month_entries))
            with col2:
                st.metric("Ø Bewertung", f"{month_avg_rating:.1f}/5")
            with col3:
                if month_total_cost > 0:
                    st.metric("Gesamtkosten", f"{month_total_cost:.2f}€")
                else:
                    st.write(f"**Substanzen:** {', '.join(sorted(month_substances))}")

        st.divider()


def show_goals_view():
    """Zeigt Ziele-Ansicht"""
    st.header("🎯 Meine Ziele")

    # Neues Ziel Formular
    with st.expander("➕ Neues Ziel hinzufügen", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            goal_substance = st.selectbox(
                "Substanz",
                options=[""] + ALL_SUBSTANCES + ["Andere..."],
                key="new_goal_substance"
            )
            if goal_substance == "Andere...":
                goal_substance = st.text_input("Eigene Substanz", key="new_goal_custom")

        with col2:
            goal_type = st.selectbox(
                "Zieltyp",
                ["Tage Pause", "Kosten reduzieren", "Konsum reduzieren", "Alternative finden"]
            )

            if goal_type == "Tage Pause":
                goal_value = st.number_input("Tage", min_value=1, max_value=365, value=7)
                goal_unit = "Tage"
            elif goal_type == "Kosten reduzieren":
                goal_value = st.number_input("Maximale Kosten (€)", min_value=0, max_value=1000, value=50)
                goal_unit = "€"
            elif goal_type == "Konsum reduzieren":
                goal_value = st.number_input("Maximale Konsumtage/Monat", min_value=1, max_value=31, value=4)
                goal_unit = "Tage/Monat"
            else:
                goal_value = st.text_input("Alternative Aktivität")
                goal_unit = "Alternative"

        goal_description = st.text_area("Beschreibung (optional)",
                                        placeholder="Warum ist dir dieses Ziel wichtig?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Ziel speichern", type="primary", key="save_goal", width='stretch'):
                if goal_substance and goal_value:
                    new_goal = {
                        'id': int(time_module.time() * 1000),
                        'substance': goal_substance,
                        'type': goal_type,
                        'value': goal_value,
                        'unit': goal_unit,
                        'description': goal_description,
                        'start_date': datetime.now().isoformat(),
                        'completed': False,
                        'progress': []
                    }
                    st.session_state.goals.append(new_goal)
                    st.session_state.auto_backup_counter += 1
                    save_all_data()
                    st.success("✅ Ziel gespeichert!")
                    st.rerun()
                else:
                    st.error("❌ Bitte fülle alle erforderlichen Felder aus")

        with col2:
            if st.button("❌ Abbrechen", key="cancel_goal", width='stretch'):
                st.rerun()

    # Ziele anzeigen
    if not st.session_state.goals:
        st.info("📝 Noch keine Ziele gesetzt. Füge dein erstes Ziel hinzu!")
    else:
        # Ziele anzeigen
        for goal in st.session_state.goals:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"### {goal['substance']}")
                    st.caption(f"🎯 {goal['type']}: {goal['value']} {goal['unit']}")
                    if goal.get('description'):
                        st.caption(f"📝 {goal['description']}")
                    st.caption(f"▶️ Start: {goal['start_date'][:10]}")

                with col2:
                    # Fortschritt berechnen
                    try:
                        start_date = datetime.fromisoformat(goal['start_date']).date()
                        days_since = (datetime.now().date() - start_date).days + 1
                    except Exception:
                        days_since = 1

                    # Erfolgreiche Tage (kein Konsum)
                    successful_days = 0
                    if goal.get('progress'):
                        successful_days = len([p for p in goal.get('progress', [])
                                               if not p.get('consumed', True)])

                    if goal['type'] == "Tage Pause":
                        target_days = int(goal['value'])
                        progress_percent = min(100, (successful_days / target_days) * 100) if target_days > 0 else 0
                        progress_text = f"{successful_days} von {target_days} Tagen ({progress_percent:.0f}%)"
                    else:
                        progress_percent = min(100, (successful_days / days_since) * 100) if days_since > 0 else 0
                        progress_text = f"{successful_days} von {days_since} Tagen ({progress_percent:.0f}%)"

                    # Fortschrittsbalken
                    st.progress(progress_percent / 100, text=progress_text)

                    # Status
                    if goal['type'] == "Tage Pause" and successful_days >= int(goal['value']):
                        st.success("🎉 Ziel erreicht!")
                        goal['completed'] = True
                    elif days_since > 0:
                        if goal['type'] == "Tage Pause":
                            remaining = int(goal['value']) - successful_days
                            if remaining > 0:
                                st.info(f"⏳ Noch {remaining} Tage")
                            else:
                                st.success("✅ Ziel erreicht!")
                        else:
                            success_rate = (successful_days / days_since) * 100
                            if success_rate >= 80:
                                st.success(f"✅ {success_rate:.0f}% Erfolg")
                            elif success_rate >= 50:
                                st.info(f"📈 {success_rate:.0f}% Erfolg")
                            else:
                                st.warning(f"⚠️ {success_rate:.0f}% Erfolg")

                with col3:
                    # Löschen-Button
                    if st.button("🗑️", key=f"del_goal_{goal['id']}", width='stretch', help="Löschen"):
                        st.session_state.goals = [g for g in st.session_state.goals
                                                  if g['id'] != goal['id']]
                        st.session_state.auto_backup_counter += 1
                        save_all_data()
                        st.rerun()

                st.divider()


def show_health_data_management():
    """Zeigt Health-Daten Verwaltung"""
    st.subheader("📱 Health-Daten Import")

    uploaded_file = st.file_uploader(
        "Lade Health-CSV-Datei hoch (Apple Health, Google Fit, etc.)",
        type=['csv', 'txt'],
        help="Lade eine CSV-Datei mit Gesundheitsdaten hoch. Verschiedene Formate werden unterstützt.",
        key="health_import"
    )

    if uploaded_file is not None:
        try:
            csv_text = uploaded_file.getvalue().decode('utf-8')
            filename = uploaded_file.name

            with st.spinner(f"Verarbeite Datei {filename}..."):
                health_entries = parse_health_csv(csv_text, filename)

                if health_entries:
                    st.success(f"✅ {len(health_entries)} Health-Datenpunkte gefunden!")

                    with st.expander("📋 Vorschau der importierten Daten", expanded=True):
                        preview_data = []
                        for entry in health_entries[:10]:
                            preview_data.append({
                                'Datum': entry.get('date', 'N/A'),
                                'Uhrzeit': entry.get('time', 'N/A'),
                                'Typ': entry.get('Type', 'Unknown'),
                                'Wert': entry.get('value', 'N/A'),
                                'Quelle': entry.get('source', 'imported')
                            })

                        if preview_data:
                            df_preview = pd.DataFrame(preview_data)
                            st.dataframe(df_preview, width='stretch', hide_index=True)

                    # Import-Optionen
                    col1, col2 = st.columns(2)
                    with col1:
                        import_option = st.radio(
                            "Import-Option",
                            ["Alle Daten hinzufügen", "Bestehende Daten ersetzen", "Nur neue Daten hinzufügen"],
                            index=0
                        )

                    with col2:
                        if st.button("📥 Daten importieren", type="primary", width='stretch'):
                            handle_health_import(health_entries, import_option)
        except Exception as e:
            st.error(f"❌ Fehler beim Import: {str(e)}")

    # Health-Daten anzeigen und bearbeiten
    if st.session_state.health_data:
        st.subheader("📊 Health-Daten Übersicht")

        # Statistiken
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            heart_rate = len([h for h in st.session_state.health_data
                              if any(word in str(h.get('Type', '')).lower()
                                     for word in ['heart', 'herz', 'hr', 'pulse', 'puls'])])
            st.metric("❤️ Herzfrequenz", heart_rate)

        with col2:
            steps = len([h for h in st.session_state.health_data
                         if any(word in str(h.get('Type', '')).lower()
                                for word in ['step', 'schritt', 'steps', 'distance'])])
            st.metric("👣 Schritte/Bewegung", steps)

        with col3:
            sleep = len([h for h in st.session_state.health_data
                         if any(word in str(h.get('Type', '')).lower()
                                for word in ['sleep', 'schlaf', 'ruhe'])])
            st.metric("😴 Schlaf/Ruhe", sleep)

        with col4:
            other = len(st.session_state.health_data) - heart_rate - steps - sleep
            st.metric("📊 Andere", other)

        # Health-Daten anzeigen und bearbeiten
        st.subheader("📋 Health-Daten bearbeiten")

        # Filter und Suche
        col1, col2 = st.columns(2)
        with col1:
            # Datentyp-Filter
            data_types = sorted(set(str(h.get('Type', 'Unknown')) for h in st.session_state.health_data))
            selected_types = st.multiselect(
                "Nach Datentyp filtern",
                options=data_types,
                default=[]
            )

        with col2:
            # Datumsfilter
            selected_date = st.session_state.get('selected_health_date', "Alle Daten")
            if st.session_state.health_data:
                dates = sorted(set(h.get('date') for h in st.session_state.health_data if h.get('date')))
                if dates:
                    selected_date = st.selectbox(
                        "Nach Datum filtern",
                        options=["Alle Daten"] + dates,
                        index=0,
                        key="health_date_filter"
                    )
                    st.session_state.selected_health_date = selected_date

        # Daten filtern
        filtered_health_data = st.session_state.health_data.copy()

        if selected_types:
            filtered_health_data = [h for h in filtered_health_data
                                    if str(h.get('Type', 'Unknown')) in selected_types]

        if selected_date and selected_date != "Alle Daten":
            filtered_health_data = [h for h in filtered_health_data
                                    if h.get('date') == selected_date]

        # Daten anzeigen mit Bearbeitungsfunktion
        for i, health_entry in enumerate(filtered_health_data[:50]):
            entry_id = health_entry.get('id', f"health_{i}")

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**{health_entry.get('Type', 'Unknown')}**")
                    st.write(f"📅 {health_entry.get('date', 'N/A')}")
                    st.write(f"⏰ {health_entry.get('time', 'N/A')}")
                    st.write(f"📊 Wert: {health_entry.get('value', 'N/A')}")

                    if health_entry.get('source'):
                        st.caption(f"Quelle: {health_entry.get('source')}")

                with col2:
                    # Bearbeiten-Button
                    if st.button("✏️", key=f"edit_health_{entry_id}",
                                 width='stretch', help="Bearbeiten"):
                        st.session_state.editing_health_entry = entry_id
                        st.rerun()

                with col3:
                    # Löschen-Button
                    if st.button("🗑️", key=f"del_health_{entry_id}",
                                 width='stretch', help="Löschen"):
                        st.session_state['health_to_delete'] = entry_id

                # Lösch-Bestätigung
                if st.session_state.get('health_to_delete') == entry_id:
                    st.warning(
                        f"Möchtest du den Health-Eintrag '{health_entry.get('Type', 'Unknown')}' am {health_entry.get('date', 'N/A')} wirklich löschen?")
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button(f"✅ Ja, löschen", key=f"confirm_del_health_{entry_id}"):
                            st.session_state.health_data = [h for h in st.session_state.health_data
                                                            if h.get('id') != entry_id]
                            st.session_state.auto_backup_counter += 1
                            save_all_data()
                            st.session_state['health_to_delete'] = None
                            st.success("🗑️ Health-Eintrag gelöscht!")
                            time_module.sleep(0.5)
                            st.rerun()
                    with col2:
                        if st.button("❌ Nein, abbrechen", key=f"cancel_del_health_{entry_id}"):
                            st.session_state['health_to_delete'] = None
                            st.rerun()

                st.divider()

        # Health-Eintrag bearbeiten
        if st.session_state.editing_health_entry:
            health_entry_to_edit = None
            for h in st.session_state.health_data:
                if h.get('id') == st.session_state.editing_health_entry:
                    health_entry_to_edit = h
                    break

            if health_entry_to_edit:
                st.subheader("✏️ Health-Eintrag bearbeiten")
                with st.form("edit_health_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        data_type = st.text_input(
                            "Datentyp *",
                            value=health_entry_to_edit.get('Type', '')
                        )

                        date_str = health_entry_to_edit.get('date', datetime.now().strftime('%Y-%m-%d'))
                        try:
                            date_val = st.date_input(
                                "Datum *",
                                value=datetime.strptime(date_str, '%Y-%m-%d')
                            )
                        except Exception:
                            date_val = st.date_input(
                                "Datum *",
                                value=datetime.now()
                            )

                    with col2:
                        value = st.number_input(
                            "Wert *",
                            value=float(health_entry_to_edit.get('value', 0)),
                            step=0.1,
                            format="%.2f"
                        )

                        time_str = health_entry_to_edit.get('time', '00:00')
                        try:
                            time_val = st.time_input(
                                "Uhrzeit *",
                                value=datetime.strptime(time_str, '%H:%M').time()
                            )
                        except Exception:
                            time_val = st.time_input(
                                "Uhrzeit *",
                                value=datetime.now().time()
                            )

                    notes = st.text_area(
                        "Notizen",
                        value=health_entry_to_edit.get('notes', '')
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Änderungen speichern", type="primary")
                    with col2:
                        if st.form_submit_button("❌ Abbrechen"):
                            st.session_state.editing_health_entry = None
                            st.rerun()

                    if submitted:
                        if not data_type.strip():
                            st.error("❌ Bitte gib einen Datentyp an!")
                        else:
                            health_entry_to_edit['Type'] = data_type.strip()
                            health_entry_to_edit['date'] = date_val.strftime('%Y-%m-%d')
                            health_entry_to_edit['time'] = time_val.strftime('%H:%M')
                            health_entry_to_edit['value'] = value
                            health_entry_to_edit['notes'] = notes.strip()

                            st.session_state.editing_health_entry = None
                            st.session_state.auto_backup_counter += 1
                            save_all_data()
                            st.success("✅ Health-Eintrag aktualisiert!")
                            time_module.sleep(1)
                            st.rerun()

    else:
        # Anleitung anzeigen wenn keine Daten vorhanden
        st.info("""
        **📱 Anleitung zum Health-Daten Import:**

        1. **Exportiere deine Gesundheitsdaten** aus deiner Health-App:
           - **Apple Health:** Profil → Exportiere alle Gesundheitsdaten
           - **Google Fit:** Menu → Einstellungen → Daten verwalten → Daten exportieren
           - **Andere Apps:** Suche nach Export-Funktion

        2. **Lade die CSV-Datei hier hoch**

        3. **Die App unterstützt verschiedene Formate:**
           - Apple Health CSV
           - Google Fit CSV
           - Allgemeine CSV-Dateien mit Datum und Werten

        **📊 Alternative:** Du kannst auch manuell Gesundheitsdaten eingeben.
        """)

        # Manuelle Eingabe
        with st.expander("✍️ Manuelle Health-Daten eingeben", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                manual_type = st.selectbox(
                    "Datentyp",
                    ["Herzfrequenz", "Blutdruck (systolisch)", "Blutdruck (diastolisch)",
                     "Schritte", "Schlaf (Stunden)", "Schlaf (Minuten)", "Tiefschlaf (Minuten)",
                     "REM-Schlaf (Minuten)", "Leichtschlaf (Minuten)", "Wachzeit (Minuten)",
                     "Gewicht (kg)", "Blutzucker", "Andere"],
                    key="manual_type"
                )
                manual_value = st.number_input("Wert", min_value=0.0, value=0.0, step=0.1, key="manual_value")
                manual_date = st.date_input("Datum", value=datetime.now(), key="manual_date")

            with col2:
                manual_time = st.time_input("Uhrzeit", value=datetime.now().time(), key="manual_time")
                manual_unit = st.text_input("Einheit (optional)",
                                            value="bpm" if manual_type == "Herzfrequenz" else
                                            "mmHg" if "Blutdruck" in manual_type else
                                            "Schritte" if manual_type == "Schritte" else
                                            "h" if manual_type == "Schlaf (Stunden)" else
                                            "min" if "Schlaf" in manual_type or "Minuten" in manual_type else
                                            "kg" if manual_type == "Gewicht (kg)" else
                                            "mg/dL" if manual_type == "Blutzucker" else "",
                                            key="manual_unit")
                manual_notes = st.text_area("Notizen (optional)", key="manual_notes")

            if st.button("➕ Datenpunkt hinzufügen", type="primary", width='stretch', key="add_manual"):
                new_health_entry = {
                    'id': int(time_module.time() * 1000),
                    'Type': manual_type,
                    'value': manual_value,
                    'date': manual_date.strftime('%Y-%m-%d'),
                    'time': manual_time.strftime('%H:%M'),
                    'Unit': manual_unit,
                    'notes': manual_notes,
                    'source': 'manual'
                }

                st.session_state.health_data.append(new_health_entry)
                st.session_state.auto_backup_counter += 1
                save_all_data()
                st.success("✅ Health-Datenpunkt hinzugefügt!")
                st.rerun()


def show_ki_therapeut_analysis():
    """Zeigt KI-Therapeut Analyse"""
    st.subheader("🧠 KI-Therapeut Analyse")

    st.info("""
    **Vorteile des KI-Therapeuten:**
    • 100% Offline – Deine Daten bleiben privat
    • Maschinelles Lernen erkennt Muster in deinen Daten
    • Korreliert Puls, Schlaf und Konsum
    • Gibt persönliche Einschätzungen basierend auf deinen Daten
    """)

    # Starte KI-Therapeut Analyse
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 KI-Therapeut Analyse starten", type="primary", width='stretch'):
            perform_ki_therapeut_analysis()

    with col2:
        if st.button("🔄 Daten aktualisieren", width='stretch'):
            st.session_state.ki_therapeut_analyzer = KITherapeutAnalyzer()
            st.session_state.ki_analysis_results = None
            st.session_state.correlation_analysis_results = None
            st.rerun()

    # Zeige Analyse Ergebnisse
    if st.session_state.ki_analysis_results:
        st.subheader("📋 KI-Therapeut Analysebericht")

        with st.expander("📄 Vollständigen Bericht anzeigen", expanded=True):
            st.text(st.session_state.ki_analysis_results)

        # Zeige Korrelationsergebnisse
        if st.session_state.correlation_analysis_results:
            corr_results = st.session_state.correlation_analysis_results

            if corr_results.get('status') == 'success':
                st.subheader("🔗 Korrelationsanalyse")

                # Datenübersicht
                st.write(f"**Datenübersicht:**")
                st.write(f"- Analysierte Tage: {corr_results['total_days']}")

                data_summary = corr_results.get('data_summary', {})
                if data_summary:
                    st.write(f"- Tage mit Schlafdaten: {data_summary.get('days_with_sleep_data', 0)}")
                    st.write(f"- Tage mit Pulsdaten: {data_summary.get('days_with_heart_rate_data', 0)}")
                    st.write(f"- Tage mit Konsumdaten: {data_summary.get('days_with_consumption_data', 0)}")
                    st.write(f"- Einzigartige Substanzen: {data_summary.get('unique_substances', 0)}")

                # Signifikante Korrelationen
                correlations = corr_results.get('correlations', {})
                if correlations:
                    st.write(f"**Signifikante Korrelationen gefunden:** {len(correlations)}")

                    # Zeige die stärksten Korrelationen
                    strong_correlations = sorted(
                        [(k, v) for k, v in correlations.items()],
                        key=lambda x: abs(x[1]['correlation']),
                        reverse=True
                    )[:3]

                    for key, corr_info in strong_correlations:
                        col1, col2 = key.split('_', 1)
                        st.write(f"• **{col1} ↔ {col2}**:")
                        st.write(f"  - Korrelation: {corr_info['correlation']:.3f}")
                        st.write(f"  - Interpretation: {corr_info['interpretation']}")

                # Substanz-Effekte
                substance_effects = corr_results.get('substance_effects', {})
                if substance_effects:
                    st.write(f"**Substanz-Effekte:**")

                    for key, effect_info in list(substance_effects.items())[:3]:
                        substance, metric = key.split('_', 1)
                        diff = effect_info['difference_percent']

                        if abs(diff) > 10:  # Nur signifikante Effekte anzeigen
                            icon = "📈" if diff > 0 else "📉"
                            st.write(f"{icon} **{substance}**: {effect_info['interpretation']}")
                            st.write(
                                f"  - Mit: {effect_info['with_substance']:.1f}, Ohne: {effect_info['without_substance']:.1f}")
                            st.write(f"  - Unterschied: {diff:+.1f}%")

                if not correlations and not substance_effects:
                    st.info("Keine signifikanten Korrelationen oder Substanz-Effekte gefunden.")
            else:
                st.warning(f"Korrelationsanalyse: {corr_results.get('message', 'Keine Ergebnisse')}")


def show_health_view():
    """Erweiterte Health-Ansicht mit KI-Therapeut"""
    st.header("🧠 KI-Therapeut Health-Analyse")

    # Tabs für verschiedene Funktionen
    tab1, tab2 = st.tabs(["📱 Daten Import & Verwaltung", "🤖 KI-Therapeut Analyse"])

    with tab1:
        show_health_data_management()

    with tab2:
        show_ki_therapeut_analysis()


# ============================================================================
# HAUPTFUNKTION
# ============================================================================

def main():
    """Hauptfunktion der App"""
    # Passwortschutz prüfen
    if not check_password():
        return

    # Initialisiere Session State
    init_session_state()

    # Prüfe Auto-Save
    auto_save_check()

    # Custom CSS
    st.markdown("""
    <style>
    .stButton button {
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .st-emotion-cache-16idsys p {
        font-size: 1rem;
    }
    .stDataFrame {
        font-size: 0.9rem;
    }
    .chat-message-user {
        background-color: #2b313e;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: right;
    }
    .chat-message-assistant {
        background-color: #1e3a5f;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🧠 Substanz-Tagebuch mit KI-Therapeut")
    st.caption(
        "Dokumentiere und analysiere deine Erfahrungen • 100% Offline KI • Für Harm Reduction & Selbstreflexion")

    # Sidebar Navigation
    with st.sidebar:
        st.header("🚀 Navigation")

        # Seitenauswahl
        page = st.radio(
            "Wähle eine Ansicht:",
            ["📋 Einträge", "📊 Statistiken", "📅 Kalender", "🎯 Ziele", "🧠 Erweiterte KI", "💬 KI-Chat"],
            index=0
        )

        st.divider()

        # Schnelle Statistiken
        stats = get_statistics()
        if stats:
            st.subheader("📈 Schnellstatistik")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Einträge", stats['totalEntries'])
                st.metric("Letzte 7 Tage", stats['last7Days'])
            with col2:
                st.metric("Ø Bewertung", f"{stats['avgRating']}/5")
                if stats['totalCost'] > 0:
                    st.metric("Gesamtkosten", f"{stats['totalCost']}€")
                else:
                    st.metric("Aktivität", stats['warning'].capitalize())

        # Gamification Status
        if 'gamification' in st.session_state and st.session_state.entries:
            gamification = st.session_state.gamification
            streaks = gamification.calculate_streak(st.session_state.entries)

            st.divider()
            st.subheader("🎮 Gamification")
            st.metric("🔥 Aktuelle Serie", f"{streaks['current']} Tage")
            st.metric("🏆 Punkte", f"{gamification.points:,}")

        # Health Daten Status
        if st.session_state.health_data:
            st.divider()
            st.subheader("❤️ Health-Daten")
            health_types = set(str(h.get('Type', '')) for h in st.session_state.health_data)
            st.write(f"**{len(st.session_state.health_data)}** Datenpunkte")
            st.write(f"**{len(health_types)}** verschiedene Typen")

        # Auto-Save Status
        if st.session_state.last_save_time:
            st.caption(f"💾 Zuletzt gespeichert: {get_time_since(st.session_state.last_save_time)}")

        st.divider()

        # Datenverwaltung
        st.subheader("💾 Datenverwaltung")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Jetzt speichern", width='stretch',
                         disabled=not st.session_state.entries):
                if save_all_data():
                    st.success("✅ Gespeichert!")
                    time_module.sleep(1)
                    st.rerun()

        with col2:
            if st.button("🔄 Daten laden", width='stretch'):
                load_all_data()
                st.success("✅ Daten geladen!")
                time_module.sleep(1)
                st.rerun()

        # Backup erstellen
        if st.button("📂 Backup erstellen", width='stretch',
                     disabled=not st.session_state.entries):
            if create_backup():
                st.success("✅ Backup erstellt!")
                time_module.sleep(1)
                st.rerun()

        st.divider()

        # Export-Sektion
        st.subheader("📤 Export")

        if st.session_state.entries:
            export_format = st.selectbox(
                "Export-Format",
                ["Text", "JSON", "CSV"],
                index=0
            )

            anonymize = st.checkbox("Daten anonymisieren", value=True,
                                    help="Entfernt persönliche Informationen")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📋 Exportieren", width='stretch'):
                    if export_format == "Text":
                        export_text = export_data(anonymize=anonymize)
                        st.code(export_text[:1000] + "..." if len(export_text) > 1000 else export_text,
                                language='text')
                        st.info("Text wurde generiert - kopiere ihn mit Strg+C")

                    elif export_format == "JSON":
                        export_data_dict = {
                            'entries': anonymize_export_data(st.session_state.entries, not anonymize),
                            'goals': st.session_state.goals,
                            'health_data': st.session_state.health_data,
                            'journal_entries': st.session_state.journal_entries,
                            'export_date': datetime.now().isoformat(),
                            'version': '4.0',
                            'anonymized': anonymize
                        }
                        export_json_text = json.dumps(export_data_dict, indent=2, ensure_ascii=False)
                        st.code(export_json_text[:1000] + "..." if len(export_json_text) > 1000 else export_json_text,
                                language='json')
                        st.info("JSON wurde generiert - kopiere es mit Strg+C")

                    elif export_format == "CSV":
                        export_df = pd.DataFrame(anonymize_export_data(st.session_state.entries, not anonymize))
                        csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 CSV herunterladen",
                            data=csv_data,
                            file_name=f"substance_diary_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            type="primary",
                            width='stretch'
                        )

            with col2:
                if st.session_state.selected_entries:
                    if st.button("📊 Auswahl exportieren", width='stretch'):
                        export_text = export_data(selected_only=True, anonymize=anonymize)
                        st.code(export_text[:500] + "..." if len(export_text) > 500 else export_text,
                                language='text')
                        st.info(f"{len(st.session_state.selected_entries)} ausgewählte Einträge exportiert")
        else:
            st.info("📝 Keine Daten zum Export verfügbar")

        st.divider()

        # Hilfe & Informationen
        with st.expander("ℹ️ Hilfe & Kontakt", expanded=False):
            st.info("""
            **📞 Wichtige Kontakte:**

            **Sucht-Hotline:** 01806 31 30 31  
            **Drogennotdienst:** 030 192 37  
            **Telefonseelsorge:** 0800 111 0 111

            **🌐 Websites:**
            - www.sucht-und-drogen-hotline.de
            - www.drogenhilfe.de
            - www.harmreduction.de

            **⚠️ Wichtiger Hinweis:**
            Diese App dient der **Selbstreflexion und Dokumentation**.
            Sie ist **KEIN ERSATZ** für professionelle Beratung oder Behandlung.

            Bei Suchtproblemen oder gesundheitlichen Bedenken
            **SUCHE IMMER PROFESSIONELLE HILFE AUF!**

            ---
            **🔒 Datenschutz:**
            - Alle Daten werden lokal gespeichert
            - Automatische Backups werden erstellt
            - Anonymisierungsoption für sicheren Export

            © 2025 Substanz-Tagebuch App mit KI-Therapeut  
            Made with ❤️ for harm reduction
            """)

    # Hauptbereich basierend auf ausgewählter Seite
    if page == "📋 Einträge":
        show_list_view()
    elif page == "📊 Statistiken":
        show_analytics_view()
    elif page == "📅 Kalender":
        show_calendar_view()
    elif page == "🎯 Ziele":
        show_goals_view()
    elif page == "🧠 Erweiterte KI":
        show_advanced_health_view()
    elif page == "💬 KI-Chat":
        show_ki_chat()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col2:
        st.caption(
            f"© {datetime.now().year} • Version 4.0 • 100% Offline KI-Therapeut • Für verantwortungsvollen Umgang")


# ============================================================================
# START DER APP
# ============================================================================

if __name__ == "__main__":
    main()