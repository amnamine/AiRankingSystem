from django.test import TestCase
from recruitment.ai_matching import compute_semantic_similarity

class AIMatchingTest(TestCase):
    def test_jina_similarity(self):
        text_en_1 = "Software engineer with python experience"
        text_en_2 = "Developer skilled in python programming"
        
        text_fr_1 = "Ingénieur logiciel avec expérience en Python"
        text_ar_1 = "مهندس برمجيات ذو خبرة في بايثون"

        sim_en = compute_semantic_similarity(text_en_1, text_en_2)
        sim_fr = compute_semantic_similarity(text_en_1, text_fr_1)
        sim_ar = compute_semantic_similarity(text_en_1, text_ar_1)

        print(f"\n[TEST] Similarity (EN-EN): {sim_en:.4f}")
        print(f"[TEST] Similarity (EN-FR): {sim_fr:.4f}")
        print(f"[TEST] Similarity (EN-AR): {sim_ar:.4f}")

        self.assertGreater(sim_en, 0.5)
        self.assertGreater(sim_fr, 0.5)
        self.assertGreater(sim_ar, 0.5)

