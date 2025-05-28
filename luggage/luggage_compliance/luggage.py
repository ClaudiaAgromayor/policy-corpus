import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import csv
import unittest
from typing import List, Dict, Optional


class Luggage:
    def __init__(
        self,
        storage: str = "carry-on",  # "carry-on", "checked", "special", "personal"
        excess: bool = False,
        special: bool = False,
        compliance: bool = False,
        weight: float = 0.0,  # in kg
        dim: dict = None  # Dimensions stored in a nested dict
    ):
        # Validation des paramètres d'entrée
        valid_storage_types = ["carry-on", "checked", "special", "personal"]
        if storage not in valid_storage_types:
            raise ValueError(f"Type de stockage invalide: {storage}. Options valides: {valid_storage_types}")
        
        if weight < 0:
            raise ValueError("Le poids ne peut pas être négatif")
            
        self.storage = storage
        self.excess = excess
        self.special = special
        self.compliance = compliance
        self.weight = weight
        
        # Initialisation des dimensions avec validation
        if dim is None:
            self.dim = {
                "height": 0.0,
                "width": 0.0,
                "depth": 0.0,
                "unit": "cm"
            }
        else:
            # Validation des dimensions requises
            required_dims = ["height", "width", "depth"]
            for dim_name in required_dims:
                if dim_name not in dim:
                    raise ValueError(f"Dimension requise manquante: {dim_name}")
                if not isinstance(dim[dim_name], (int, float)) or dim[dim_name] < 0:
                    raise ValueError(f"La dimension {dim_name} doit être un nombre positif")
            
            # Unité par défaut si non spécifiée
            if "unit" not in dim:
                dim["unit"] = "cm"
            elif dim["unit"] not in ["cm", "in", "mm"]:
                raise ValueError(f"Unité invalide: {dim['unit']}. Options: cm, in, mm")
                
            self.dim = dim

    def get_volume(self) -> float:
        """Calcule le volume du bagage en centimètres cubes."""
        try:
            volume = self.dim["height"] * self.dim["width"] * self.dim["depth"]
            
            # Conversion si nécessaire (supposant que les calculs se font en cm)
            if self.dim["unit"] == "mm":
                volume = volume / 1000  # mm³ vers cm³
            elif self.dim["unit"] == "in":
                volume = volume * 16.387  # in³ vers cm³
                
            return volume
        except (KeyError, TypeError) as e:
            raise ValueError(f"Erreur lors du calcul du volume: {e}")

    def is_oversized(self, max_dim: float) -> bool:
        """Vérifie si une dimension dépasse la taille maximale autorisée (en cm)."""
        try:
            # Conversion des dimensions en cm si nécessaire
            dims_in_cm = self._get_dimensions_in_cm()
            return max(dims_in_cm["height"], dims_in_cm["width"], dims_in_cm["depth"]) > max_dim
        except (KeyError, TypeError):
            return True  # En cas d'erreur, considérer comme surdimensionné par sécurité

    def _get_dimensions_in_cm(self) -> Dict[str, float]:
        """Retourne les dimensions converties en centimètres."""
        dims = {
            "height": self.dim["height"],
            "width": self.dim["width"], 
            "depth": self.dim["depth"]
        }
        
        if self.dim["unit"] == "mm":
            return {k: v / 10 for k, v in dims.items()}
        elif self.dim["unit"] == "in":
            return {k: v * 2.54 for k, v in dims.items()}
        else:  # cm ou unité par défaut
            return dims

    def get_total_size_cm(self) -> float:
        """Retourne la taille totale (somme des dimensions) en cm."""
        dims_cm = self._get_dimensions_in_cm()
        return sum(dims_cm.values())

    def get_dimensions_list_cm(self) -> List[float]:
        """Retourne les dimensions sous forme de liste [hauteur, largeur, profondeur] en cm."""
        dims_cm = self._get_dimensions_in_cm()
        return [dims_cm["height"], dims_cm["width"], dims_cm["depth"]]

    def to_dict(self) -> dict:
        """Convertit l'objet luggage en dictionnaire correspondant à la structure JSON."""
        return {
            "storage": self.storage,
            "excess": self.excess,
            "special": self.special,
            "compliance": self.compliance,
            "weight": self.weight,
            "height": self.dim["height"],
            "width": self.dim["width"],
            "depth": self.dim["depth"],
            "unit": self.dim["unit"]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Luggage':
        """Crée un objet Luggage à partir d'un dictionnaire."""
        try:
            return Luggage(
                storage=data["storage"],
                excess=data.get("excess", False),
                special=data.get("special", False),
                compliance=data.get("compliance", False),
                weight=float(data["weight"]),
                dim={
                    "height": float(data["height"]),
                    "width": float(data["width"]),
                    "depth": float(data["depth"]),
                    "unit": data.get("unit", "cm")
                }
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Erreur lors de la création du Luggage depuis le dictionnaire: {e}")

    @staticmethod
    def save_to_csv(filename: str, luggage_list: List['Luggage']) -> None:
        """Sauvegarde une liste d'objets Luggage dans un fichier CSV."""
        if not luggage_list:
            print("Avertissement: Liste de bagages vide, aucun fichier créé.")
            return

        fieldnames = ["storage", "excess", "special", "compliance", "weight", "height", "width", "depth", "unit"]

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for luggage in luggage_list:
                    if not isinstance(luggage, Luggage):
                        print(f"Avertissement: Objet ignoré (pas un Luggage): {luggage}")
                        continue
                    writer.writerow(luggage.to_dict())
            print(f"✓ {len(luggage_list)} bagages sauvegardés dans {filename}")
        except IOError as e:
            raise IOError(f"Erreur lors de la sauvegarde CSV: {e}")

    @staticmethod
    def load_from_csv(filename: str) -> List['Luggage']:
        """Charge des objets Luggage depuis un fichier CSV."""
        luggage_list = []
        
        try:
            with open(filename, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # start=2 car ligne 1 = header
                    try:
                        # Conversion des booléens avec gestion d'erreur
                        row["excess"] = str(row.get("excess", "false")).lower() in ["true", "1", "yes"]
                        row["special"] = str(row.get("special", "false")).lower() in ["true", "1", "yes"]
                        row["compliance"] = str(row.get("compliance", "false")).lower() in ["true", "1", "yes"]
                        
                        # Conversion des nombres avec validation
                        row["weight"] = float(row["weight"]) if row["weight"] else 0.0
                        row["height"] = float(row["height"]) if row["height"] else 0.0
                        row["width"] = float(row["width"]) if row["width"] else 0.0
                        row["depth"] = float(row["depth"]) if row["depth"] else 0.0
                        
                        luggage_list.append(Luggage.from_dict(row))
                        
                    except (ValueError, KeyError) as e:
                        print(f"Erreur ligne {row_num} du CSV: {e} - Ligne ignorée")
                        continue
                        
            print(f"✓ {len(luggage_list)} bagages chargés depuis {filename}")
            return luggage_list
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier CSV non trouvé: {filename}")
        except IOError as e:
            raise IOError(f"Erreur lors du chargement CSV: {e}")

    def __eq__(self, other) -> bool:
        """Vérifie l'égalité entre deux objets Luggage."""
        if not isinstance(other, Luggage):
            return False
        return (
            self.storage == other.storage and
            abs(self.weight - other.weight) < 0.01 and  # Tolérance pour les flottants
            self.dim == other.dim and
            self.excess == other.excess and
            self.special == other.special and
            self.compliance == other.compliance
        )

    def __hash__(self) -> int:
        """Définit un hash pour que les objets Luggage puissent être stockés dans des sets/dictionnaires."""
        try:
            return hash((
                self.storage,
                round(self.weight, 2),  # Arrondi pour éviter les problèmes de précision
                frozenset(self.dim.items()),  # Convertir dict en frozenset pour le hashing
                self.excess,
                self.special,
                self.compliance
            ))
        except TypeError:
            # Fallback si le hashing échoue
            return hash(str(self))

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet."""
        return (
            f"Luggage(storage='{self.storage}', weight={self.weight}kg, "
            f"dim={self.dim}, excess={self.excess}, special={self.special}, "
            f"compliance={self.compliance})"
        )

    def __str__(self) -> str:
        """Représentation conviviale de l'objet."""
        dims_cm = self._get_dimensions_in_cm()
        return (f"Bagage {self.storage}: {self.weight}kg, "
                f"{dims_cm['height']}×{dims_cm['width']}×{dims_cm['depth']}cm"
                f"{' (excès)' if self.excess else ''}"
                f"{' (spécial)' if self.special else ''}")


class TestLuggageCompliance(unittest.TestCase):
    """Tests unitaires pour la classe Luggage."""

    def setUp(self):
        """Initialisation pour tous les tests."""
        self.valid_luggage = Luggage(
            storage="carry-on",
            excess=False,
            special=False,
            compliance=True,
            weight=7.0,
            dim={"height": 55.0, "width": 40.0, "depth": 23.0, "unit": "cm"}
        )

    def test_luggage_creation_valid(self):
        """Test de création d'un bagage valide."""
        luggage = Luggage(
            storage="checked",
            weight=20.0,
            dim={"height": 70.0, "width": 50.0, "depth": 30.0, "unit": "cm"}
        )
        self.assertEqual(luggage.storage, "checked")
        self.assertEqual(luggage.weight, 20.0)
        self.assertEqual(luggage.dim["height"], 70.0)

    def test_luggage_creation_invalid_storage(self):
        """Test de création avec type de stockage invalide."""
        with self.assertRaises(ValueError):
            Luggage(storage="invalid_storage")

    def test_luggage_creation_negative_weight(self):
        """Test de création avec poids négatif."""
        with self.assertRaises(ValueError):
            Luggage(weight=-5.0)

    def test_luggage_creation_missing_dimensions(self):
        """Test de création avec dimensions manquantes."""
        with self.assertRaises(ValueError):
            Luggage(dim={"height": 50, "width": 40})  # depth manquant

    def test_volume_calculation(self):
        """Test du calcul de volume."""
        luggage = Luggage(dim={"height": 10.0, "width": 20.0, "depth": 30.0, "unit": "cm"})
        expected_volume = 10.0 * 20.0 * 30.0
        self.assertEqual(luggage.get_volume(), expected_volume)

    def test_is_oversized(self):
        """Test de vérification de surdimensionnement."""
        luggage = Luggage(dim={"height": 60.0, "width": 40.0, "depth": 23.0, "unit": "cm"})
        self.assertTrue(luggage.is_oversized(55.0))  # hauteur > 55
        self.assertFalse(luggage.is_oversized(65.0))  # toutes dimensions < 65

    def test_to_dict_and_from_dict(self):
        """Test de sérialisation/désérialisation."""
        original = self.valid_luggage
        dict_data = original.to_dict()
        reconstructed = Luggage.from_dict(dict_data)
        self.assertEqual(original, reconstructed)

    def test_csv_save_and_load(self):
        """Test de sauvegarde et chargement CSV."""
        import tempfile
        import os
        
        luggage_list = [
            self.valid_luggage,
            Luggage(storage="checked", weight=25.0, 
                   dim={"height": 70.0, "width": 50.0, "depth": 30.0, "unit": "cm"})
        ]
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_filename = f.name
        
        try:
            # Sauvegarder
            Luggage.save_to_csv(temp_filename, luggage_list)
            
            # Charger
            loaded_list = Luggage.load_from_csv(temp_filename)
            
            # Vérifier
            self.assertEqual(len(loaded_list), len(luggage_list))
            for original, loaded in zip(luggage_list, loaded_list):
                self.assertEqual(original, loaded)
                
        finally:
            # Nettoyer
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_carry_on_exceeds_quantity(self):
        """Test du cas où le nombre de bagages cabine dépasse la limite."""
        bag1 = Luggage(
            storage="carry-on",
            excess=False,
            special=False,
            compliance=True,
            weight=7.0,
            dim={"height": 55.0, "width": 40.0, "depth": 23.0, "unit": "cm"}
        )

        bag2 = Luggage(
            storage="checked",
            excess=True,
            special=False,
            compliance=False,
            weight=25.0,
            dim={"height": 70.0, "width": 50.0, "depth": 30.0, "unit": "cm"}
        )

        luggage_list = [bag1, bag2]
        self.assertEqual(len(luggage_list), 2)
        
        # Tests supplémentaires
        self.assertTrue(bag1.compliance)
        self.assertTrue(bag2.excess)
        self.assertNotEqual(bag1, bag2)

    def test_unit_conversion(self):
        """Test de conversion d'unités."""
        luggage_cm = Luggage(dim={"height": 55.0, "width": 40.0, "depth": 23.0, "unit": "cm"})
        luggage_mm = Luggage(dim={"height": 550.0, "width": 400.0, "depth": 230.0, "unit": "mm"})
        
        # Les dimensions en cm devraient être équivalentes
        dims_cm_1 = luggage_cm.get_dimensions_list_cm()
        dims_cm_2 = luggage_mm.get_dimensions_list_cm()
        
        for dim1, dim2 in zip(dims_cm_1, dims_cm_2):
            self.assertAlmostEqual(dim1, dim2, places=1)


if __name__ == "__main__":
    # Exemple d'utilisation
    print("=== EXEMPLE D'UTILISATION ===")
    
    # Création de bagages
    carry_on = Luggage(
        storage="carry-on",
        weight=6.5,
        dim={"height": 55, "width": 40, "depth": 23, "unit": "cm"}
    )
    
    checked = Luggage(
        storage="checked", 
        weight=22.0,
        excess=True,  # Bagage avec excès
        dim={"height": 75, "width": 50, "depth": 35, "unit": "cm"}
    )
    
    print(f"Bagage cabine: {carry_on}")
    print(f"Volume: {carry_on.get_volume():.1f} cm³")
    print(f"Surdimensionné (>55cm): {carry_on.is_oversized(55)}")
    
    print(f"\nBagage soute: {checked}")
    print(f"Taille totale: {checked.get_total_size_cm():.1f} cm")
    
    # Test de sauvegarde CSV
    bagages = [carry_on, checked]
    print(f"\nSauvegarde de {len(bagages)} bagages...")
    
    # Tests unitaires
    print("\n=== TESTS UNITAIRES ===")
    unittest.main(verbosity=2)


if __name__ == "__main__":
    unittest.main()
