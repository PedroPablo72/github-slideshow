import requests
import sys
import json
from datetime import datetime

class KetoMealPlannerTester:
    def __init__(self, base_url="https://keto-meal-planner-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "passed": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if success:
                try:
                    response_data = response.json()
                    details += f", Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'List data'}"
                    self.log_test(name, True, details)
                    return True, response_data
                except:
                    details += ", Response: Non-JSON"
                    self.log_test(name, True, details)
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Error: {response.text}"
                self.log_test(name, False, details)
                return False, {}

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Network error: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Unexpected error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_get_weekly_plan_initial(self):
        """Test getting initial weekly plan"""
        success, response = self.run_test("Get Initial Weekly Plan", "GET", "weekly-plan", 200)
        if success and response:
            # Validate structure
            if 'slots' in response and len(response['slots']) == 21:
                print("   ✅ Weekly plan has correct structure (21 slots)")
                return True, response
            else:
                print(f"   ❌ Weekly plan structure invalid - slots: {len(response.get('slots', []))}")
                return False, response
        return success, response

    def test_add_meal_to_slot(self):
        """Test adding meal to a specific slot"""
        meal_data = {
            "day": 0,  # Monday
            "meal_type": "desayuno",  # Breakfast
            "meal": {
                "name": "Huevos revueltos con aguacate",
                "ingredients": ["huevos", "aguacate", "mantequilla", "sal"]
            }
        }
        return self.run_test("Add Meal to Slot", "PUT", "weekly-plan/slot", 200, data=meal_data)

    def test_get_weekly_plan_with_meal(self):
        """Test getting weekly plan after adding meal"""
        success, response = self.run_test("Get Weekly Plan with Meal", "GET", "weekly-plan", 200)
        if success and response:
            # Check if meal was added correctly
            slots = response.get('slots', [])
            breakfast_slot = next((slot for slot in slots if slot['day'] == 0 and slot['meal_type'] == 'desayuno'), None)
            
            if breakfast_slot and breakfast_slot.get('meal'):
                meal = breakfast_slot['meal']
                if meal.get('name') == "Huevos revueltos con aguacate" and len(meal.get('ingredients', [])) == 4:
                    print("   ✅ Meal was added correctly to slot")
                    return True, response
                else:
                    print(f"   ❌ Meal data incorrect: {meal}")
                    return False, response
            else:
                print("   ❌ No meal found in expected slot")
                return False, response
        return success, response

    def test_get_shopping_list(self):
        """Test getting shopping list with ingredients"""
        success, response = self.run_test("Get Shopping List", "GET", "shopping-list", 200)
        if success and response:
            # Should have ingredients from the meal we added
            if isinstance(response, list) and len(response) >= 4:
                print(f"   ✅ Shopping list contains {len(response)} ingredients")
                # Print ingredients for verification
                ingredients = [item.get('name', '') for item in response if isinstance(item, dict)]
                print(f"   Ingredients: {ingredients}")
                return True, response
            else:
                print(f"   ❌ Shopping list structure invalid: {response}")
                return False, response
        return success, response

    def test_add_second_meal(self):
        """Test adding another meal to build shopping list"""
        meal_data = {
            "day": 1,  # Tuesday
            "meal_type": "comida",  # Lunch
            "meal": {
                "name": "Salmón a la plancha con brócoli",
                "ingredients": ["salmón", "brócoli", "aceite de oliva", "sal", "limón"]
            }
        }
        return self.run_test("Add Second Meal", "PUT", "weekly-plan/slot", 200, data=meal_data)

    def test_updated_shopping_list(self):
        """Test shopping list after adding second meal"""
        success, response = self.run_test("Get Updated Shopping List", "GET", "shopping-list", 200)
        if success and response:
            # Should have ingredients from both meals
            if isinstance(response, list) and len(response) >= 8:
                print(f"   ✅ Updated shopping list contains {len(response)} ingredients")
                return True, response
            else:
                print(f"   ❌ Shopping list not properly updated: {response}")
                return False, response
        return success, response

    def test_delete_meal_from_slot(self):
        """Test deleting a meal from slot"""
        params = {
            "day": 0,
            "meal_type": "desayuno"
        }
        return self.run_test("Delete Meal from Slot", "DELETE", "weekly-plan/slot", 200, params=params)

    def test_verify_meal_deleted(self):
        """Test that meal was actually deleted"""
        success, response = self.run_test("Verify Meal Deleted", "GET", "weekly-plan", 200)
        if success and response:
            slots = response.get('slots', [])
            breakfast_slot = next((slot for slot in slots if slot['day'] == 0 and slot['meal_type'] == 'desayuno'), None)
            
            if breakfast_slot and breakfast_slot.get('meal') is None:
                print("   ✅ Meal was successfully deleted")
                return True, response
            else:
                print(f"   ❌ Meal still exists in slot: {breakfast_slot}")
                return False, response
        return success, response

    def test_reset_weekly_plan(self):
        """Test resetting the entire weekly plan"""
        success, response = self.run_test("Reset Weekly Plan", "DELETE", "weekly-plan/reset", 200)
        if success and response:
            # Check if plan was returned in reset response
            if 'plan' in response and len(response['plan'].get('slots', [])) == 21:
                print("   ✅ Reset returned proper plan structure")
                return True, response
            else:
                print(f"   ❌ Reset response invalid: {response}")
                return False, response
        return success, response

    def test_verify_plan_reset(self):
        """Test that plan was completely reset"""
        success, response = self.run_test("Verify Plan Reset", "GET", "weekly-plan", 200)
        if success and response:
            slots = response.get('slots', [])
            meals_found = [slot for slot in slots if slot.get('meal') is not None]
            
            if len(meals_found) == 0:
                print("   ✅ Plan successfully reset - no meals found")
                return True, response
            else:
                print(f"   ❌ Plan not properly reset - {len(meals_found)} meals still exist")
                return False, response
        return success, response

    def test_empty_shopping_list(self):
        """Test shopping list is empty after reset"""
        success, response = self.run_test("Empty Shopping List After Reset", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list) and len(response) == 0:
                print("   ✅ Shopping list is empty after reset")
                return True, response
            else:
                print(f"   ❌ Shopping list not empty after reset: {response}")
                return False, response
        return success, response

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Keto Meal Planner API Tests")
        print("=" * 50)
        
        # Test sequence
        test_sequence = [
            self.test_health_check,
            self.test_get_weekly_plan_initial,
            self.test_add_meal_to_slot,
            self.test_get_weekly_plan_with_meal,
            self.test_get_shopping_list,
            self.test_add_second_meal,
            self.test_updated_shopping_list,
            self.test_delete_meal_from_slot,
            self.test_verify_meal_deleted,
            self.test_reset_weekly_plan,
            self.test_verify_plan_reset,
            self.test_empty_shopping_list
        ]
        
        for test in test_sequence:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = KetoMealPlannerTester()
    
    try:
        all_passed = tester.run_all_tests()
        return 0 if all_passed else 1
    except Exception as e:
        print(f"Test suite crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())