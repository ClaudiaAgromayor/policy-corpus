import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Importation des classes du projet
from common.abstract_policy import Policy  # Classe Policy existante
from luggage import Luggage  # Notre nouvelle classe Luggage améliorée
from luggage_compliance_request import LuggageComplianceRequest

import unittest
from typing import List, Tuple, Any


class LuggageCompliance(Policy):
    """Politique de conformité des bagages pour les compagnies aériennes."""
    
    def __init__(self):
        self.classes = {
            "Economy": {
                "carry_on": {"quantity": 1, "weight_limit": 7, "size_limit": [55, 40, 23]},
                "checked": {"allowance": 1, "weight_limit": 23, "size_limit": 158}
            },
            "Business": {
                "carry_on": {"quantity": 2, "weight_limit": 12, "size_limit": [55, 40, 23]},
                "checked": {"allowance": 2, "weight_limit": 32, "size_limit": 158}
            },
            "First": {
                "carry_on": {"quantity": 2, "weight_limit": 12, "size_limit": [55, 40, 23]},
                "checked": {"allowance": 3, "weight_limit": 32, "size_limit": 158}
            }
        }
        
        self.child_allowances = {
            "child": {"checked": {"allowance": 1, "weight_limit": 23, "size_limit": 158}},
            "infant": {"checked": {"allowance": 1, "weight_limit": 10, "size_limit": 158},
                       "additional": "collapsible stroller"}
        }
        
        self.excess_fees = {
            "overweight": 75,
            "oversize": 100,
            "extra_piece": 150
        }

    def validate_carry_on(self, travel_class: str, carry_on_items: List[Luggage], 
                         personal_items: List[Luggage]) -> Tuple[bool, str, List[Luggage]]:
        """Valide les bagages cabine et articles personnels."""
        if travel_class not in self.classes:
            raise ValueError(f"Classe de voyage invalide: {travel_class}")
            
        class_policy = self.classes[travel_class]["carry_on"]
        checked_candidates = []

        total_items = carry_on_items + personal_items
        compliant_items = []
        
        for item in total_items:
            try:
                # Utilisation des nouvelles méthodes de la classe Luggage
                dimensions_cm = item.get_dimensions_list_cm()
                size_ok = all(dim <= lim for dim, lim in zip(dimensions_cm, class_policy["size_limit"]))
                weight_ok = item.weight <= class_policy["weight_limit"]
                
                if not size_ok or not weight_ok:
                    # Marquer comme non conforme et candidat pour la soute
                    item.compliance = False
                    if not size_ok:
                        print(f"Bagage {item.storage} trop grand: {dimensions_cm} > {class_policy['size_limit']}")
                    if not weight_ok:
                        print(f"Bagage {item.storage} trop lourd: {item.weight}kg > {class_policy['weight_limit']}kg")
                    checked_candidates.append(item)
                else:
                    item.compliance = True
                    compliant_items.append(item)
                    
            except Exception as e:
                print(f"Erreur lors de la validation du bagage {item}: {e}")
                item.compliance = False
                checked_candidates.append(item)

        # Vérification de la quantité autorisée
        max_items = class_policy["quantity"] + 1  # +1 pour l'article personnel
        if len(compliant_items) > max_items:
            # Déplacer les articles les plus lourds vers les bagages enregistrés
            compliant_items.sort(key=lambda x: x.weight, reverse=True)
            overflow = compliant_items[max_items:]
            
            # Marquer comme excès les bagages déplacés
            for item in overflow:
                item.excess = True
                item.compliance = False
                print(f"Bagage en excès déplacé: {item}")
                
            checked_candidates.extend(overflow)
            compliant_items = compliant_items[:max_items]

        message = "Bagages cabine conformes."
        if len(checked_candidates) > 0:
            message = f"Mais {len(checked_candidates)} bagage(s) doi(ven)t être déplacé(s) en soute"

        return True, message, checked_candidates

    def validate_checked_baggage(self, travel_class: str, checked_items: List[Luggage], 
                               passenger_type: str = "adult", 
                               carry_on_capacity: int = 0) -> Tuple[bool, str, List[Luggage], float]:
        """Valide les bagages enregistrés."""
        if travel_class not in self.classes:
            raise ValueError(f"Classe de voyage invalide: {travel_class}")
            
        class_policy = self.classes[travel_class]["checked"].copy()
        fees = 0.0
        cargo_items = []
        retained_checked_items = []
        message_parts = []

        # Application des allowances enfants
        if passenger_type in self.child_allowances:
            child_policy = self.child_allowances[passenger_type]["checked"]
            class_policy["allowance"] += child_policy["allowance"]
            class_policy["weight_limit"] = max(class_policy["weight_limit"], child_policy["weight_limit"])
            message_parts.append(f"Allowance enfant appliquée (+{child_policy['allowance']} bagage)")

        # Tentative de replacer des bagages légers en cabine si il y a de la place
        checked_items.sort(key=lambda x: x.weight)  # Essayer les plus légers d'abord
        carryon_candidates = []
        
        for item in checked_items:
            try:
                dimensions_cm = item.get_dimensions_list_cm()
                carry_on_limits = self.classes[travel_class]["carry_on"]["size_limit"]
                carry_on_weight_limit = self.classes[travel_class]["carry_on"]["weight_limit"]
                
                # Vérifier si le bagage peut retourner en cabine
                if (carry_on_capacity > 0 and
                        all(dim <= carry_on_limits[i] for i, dim in enumerate(dimensions_cm)) and
                        item.weight <= carry_on_weight_limit):
                    
                    item.storage = "carry-on"
                    item.compliance = True
                    item.excess = False
                    carryon_candidates.append(item)
                    carry_on_capacity -= 1
                    print(f"Bagage replacé en cabine: {item}")
                else:
                    retained_checked_items.append(item)
                    
            except Exception as e:
                print(f"Erreur lors de l'évaluation pour retour cabine: {e}")
                retained_checked_items.append(item)

        # Validation des bagages restants en soute
        for item in retained_checked_items:
            weight = item.weight
            
            try:
                total_size_cm = item.get_total_size_cm()
                dimensions_cm = item.get_dimensions_list_cm()
            except Exception as e:
                print(f"Erreur lors de l'obtention des dimensions: {e}")
                total_size_cm = float('inf')  # Force le passage en cargo
                dimensions_cm = [0, 0, 0]

            # Vérification des limites cargo (poids > 32kg ou taille > 203cm)
            if weight > 32 or total_size_cm > 203:
                item.special = True  # Marquer comme cargo/fret
                item.compliance = False
                cargo_items.append(item)
                print(f"Bagage dirigé vers cargo: {item} (poids: {weight}kg, taille: {total_size_cm:.1f}cm)")
                continue  # Pas de frais supplémentaires pour le cargo, juste refus

            # Vérification du poids pour frais
            if weight > class_policy["weight_limit"]:
                fees += self.excess_fees["overweight"]
                item.excess = True
                message_parts.append(f"Surpoids {dimensions_cm} ({weight}kg > {class_policy['weight_limit']}kg)")

            # Vérification de la taille pour frais (mais pas cargo)
            if total_size_cm > class_policy["size_limit"] and total_size_cm <= 203:
                fees += self.excess_fees["oversize"]
                item.excess = True
                message_parts.append(f"Surtaille {dimensions_cm} ({total_size_cm:.1f}cm > {class_policy['size_limit']}cm)")

        # Vérification du nombre de bagages
        excess_items = max(0, len(retained_checked_items) - class_policy["allowance"])
        if excess_items > 0:
            fees += self.excess_fees["extra_piece"] * excess_items
            message_parts.append(f"{excess_items} bagage(s) supplémentaire(s)")
            
            # Marquer les bagages en excès
            for item in retained_checked_items[-excess_items:]:
                item.excess = True

        # Construction du message final
        if message_parts:
            message = "Frais applicables: " + "; ".join(message_parts)
        else:
            message = "Bagages enregistrés conformes."

        # Si des articles doivent aller en cargo, c'est un échec
        if cargo_items:
            failure_message = f"ÉCHEC: {len(cargo_items)} article(s) doivent être expédiés comme fret. " + message
            return False, failure_message, cargo_items, fees

        return True, message, cargo_items, fees

    def test_eligibility(self, request: 'LuggageComplianceRequest') -> Tuple[bool, str, List[Luggage], List[Luggage], float]:
        """Test principal d'éligibilité des bagages."""
        try:
            # Séparation des bagages par type de stockage
            carry_on_items = [x for x in request.luggages if x.storage == "carry-on"]
            personal_items = [x for x in request.luggages if x.storage == "personal"]
            checked_items = [x for x in request.luggages if x.storage == "checked"]

            print(f"Analyse de {len(request.luggages)} bagages:")
            print(f"- Cabine: {len(carry_on_items)}, Personnel: {len(personal_items)}, Soute: {len(checked_items)}")

            # Validation des bagages cabine et récupération des articles à déplacer
            carry_on_valid, carry_on_msg, carry_on_to_check = self.validate_carry_on(
                request.travel_class, carry_on_items, personal_items
            )

            # Mise à jour du stockage des bagages déplacés
            for item in carry_on_to_check:
                item.storage = "checked"

            # Combinaison avec les bagages enregistrés originaux
            all_checked_items = checked_items + carry_on_to_check

            # Calcul de la capacité cabine restante après ajustement
            class_policy = self.classes[request.travel_class]["carry_on"]
            carry_on_capacity = max(0, class_policy["quantity"] + 1 - (
                        len(carry_on_items) + len(personal_items) - len(carry_on_to_check)))

            # Validation des bagages enregistrés (incluant ceux déplacés)
            checked_result, checked_message, cargo_items, fees = self.validate_checked_baggage(
                request.travel_class, all_checked_items, request.age_category, carry_on_capacity
            )

            # Construction du message final
            messages = []
            if carry_on_msg != "Bagages cabine conformes.":
                messages.append(carry_on_msg)
            if checked_message != "Bagages enregistrés conformes.":
                messages.append(checked_message)
                
            full_message = " | ".join(messages) if messages else "Tous les bagages sont conformes."
            
            # Détermination du résultat final
            final_result = checked_result and (len(cargo_items) == 0)
            
            return final_result, full_message, carry_on_to_check, cargo_items, fees
            
        except Exception as e:
            error_message = f"Erreur lors de la validation: {str(e)}"
            print(f"ERREUR: {error_message}")
            return False, error_message, [], [], 0.0

    def generate_detailed_report(self, request: 'LuggageComplianceRequest') -> dict:
        """Génère un rapport détaillé de l'analyse des bagages."""
        result = self.test_eligibility(request)
        valid, message, moved_to_checked, cargo_items, fees = result
        
        # Statistiques par type de bagage
        stats = {
            "carry_on": len([x for x in request.luggages if x.storage == "carry-on"]),
            "personal": len([x for x in request.luggages if x.storage == "personal"]),
            "checked": len([x for x in request.luggages if x.storage == "checked"]),
            "special": len([x for x in request.luggages if x.special]),
            "excess": len([x for x in request.luggages if x.excess]),
            "compliant": len([x for x in request.luggages if x.compliance])
        }
        
        return {
            "request_info": {
                "travel_class": request.travel_class,
                "age_category": request.age_category,
                "total_luggage": len(request.luggages)
            },
            "result": {
                "valid": valid,
                "message": message,
                "fees": fees
            },
            "statistics": stats,
            "actions": {
                "moved_to_checked": len(moved_to_checked),
                "sent_to_cargo": len(cargo_items)
            },
            "details": {
                "moved_items": [item.to_dict() for item in moved_to_checked],
                "cargo_items": [item.to_dict() for item in cargo_items]
            }
        }


# Classe de demande adaptée (si elle n'existe pas déjà)
class LuggageComplianceRequest:
    """Classe représentant une demande de vérification de conformité des bagages."""
    
    def __init__(self, travel_class: str, age_category: str, luggages: List[Luggage]):
        self.travel_class = travel_class
        self.age_category = age_category
        self.luggages = luggages
        
        # Validation
        valid_classes = ["Economy", "Business", "First"]
        if travel_class not in valid_classes:
            raise ValueError(f"Classe invalide: {travel_class}")
            
        valid_ages = ["adult", "child", "infant"]
        if age_category not in valid_ages:
            raise ValueError(f"Âge invalide: {age_category}")


def test_integration():
    """Test d'intégration avec la nouvelle classe Luggage."""
    print("=== TEST D'INTÉGRATION ===\n")
    
    policy = LuggageCompliance()
    
    # Création de bagages avec la nouvelle classe
    bagages = [
        Luggage(
            storage="carry-on",
            weight=6.0,
            dim={"height": 55, "width": 40, "depth": 23, "unit": "cm"}
        ),
        Luggage(
            storage="personal", 
            weight=3.0,
            dim={"height": 35, "width": 25, "depth": 20, "unit": "cm"}
        ),
        Luggage(
            storage="checked",
            weight=22.0,
            dim={"height": 70, "width": 50, "depth": 30, "unit": "cm"}
        )
    ]
    
    request = LuggageComplianceRequest("Business", "adult", bagages)
    
    # Test de la méthode principale
    result = policy.test_eligibility(request)
    print("Résultat de test_eligibility:")
    print(f"Valide: {result[0]}")
    print(f"Message: {result[1]}")
    print(f"Bagages déplacés: {len(result[2])}")
    print(f"Bagages cargo: {len(result[3])}")
    print(f"Frais: {result[4]}€")
    
    # Test du rapport détaillé
    report = policy.generate_detailed_report(request)
    print(f"\n=== RAPPORT DÉTAILLÉ ===")
    print(f"Classe: {report['request_info']['travel_class']}")
    print(f"Total bagages: {report['request_info']['total_luggage']}")
    print(f"Conformes: {report['statistics']['compliant']}")
    print(f"En excès: {report['statistics']['excess']}")
    print(f"Frais totaux: {report['result']['fees']}€")


class TestLuggageComplianceIntegration(unittest.TestCase):
    """Tests d'intégration avec la nouvelle classe Luggage."""

    def setUp(self):
        self.policy = LuggageCompliance()

    def test_with_new_luggage_class(self):
        """Test avec la nouvelle classe Luggage."""
        bagages = [
            Luggage(storage="carry-on", weight=5.0, 
                   dim={"height": 55, "width": 40, "depth": 23, "unit": "cm"}),
            Luggage(storage="checked", weight=20.0,
                   dim={"height": 70, "width": 50, "depth": 30, "unit": "cm"})
        ]
        
        request = LuggageComplianceRequest("Economy", "adult", bagages)
        result = self.policy.test_eligibility(request)
        
        self.assertTrue(result[0])  # Doit être valide
        self.assertEqual(result[4], 0)  # Pas de frais

    def test_unit_conversion_handling(self):
        """Test de gestion des conversions d'unités."""
        # Bagage en millimètres (équivalent à 55x40x23 cm)
        bagage_mm = Luggage(
            storage="carry-on", 
            weight=6.0,
            dim={"height": 550, "width": 400, "depth": 230, "unit": "mm"}
        )
        
        request = LuggageComplianceRequest("Economy", "adult", [bagage_mm])
        result = self.policy.test_eligibility(request)
        
        self.assertTrue(result[0])  # Doit être valide après conversion

    def test_detailed_report_generation(self):
        """Test de génération de rapport détaillé."""
        bagages = [
            Luggage(storage="carry-on", weight=8.0,  # Trop lourd
                   dim={"height": 55, "width": 40, "depth": 23, "unit": "cm"})
        ]
        
        request = LuggageComplianceRequest("Economy", "adult", bagages)
        report = self.policy.generate_detailed_report(request)
        
        self.assertIn("request_info", report)
        self.assertIn("result", report)
        self.assertIn("statistics", report)
        self.assertEqual(report["actions"]["moved_to_checked"], 1)


if __name__ == "__main__":
    test_integration()
    print("\n" + "="*50)
    unittest.main(verbosity=2)
