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

    def test_add_ingredients_to_shopping_list(self):
        """Test adding ingredients directly to shopping list"""
        ingredients_data = {
            "ingredients": ["pollo", "brócoli", "aceite de oliva", "sal"]
        }
        success, response = self.run_test("Add Ingredients to Shopping List", "POST", "shopping-list/add", 200, data=ingredients_data)
        if success and response:
            if 'added' in response and len(response['added']) == 4:
                print("   ✅ 4 ingredients added successfully")
                return True, response
            else:
                print(f"   ❌ Addition response invalid: {response}")
                return False, response
        return success, response

    def test_verify_shopping_list_has_items(self):
        """Test shopping list contains added items"""
        success, response = self.run_test("Verify Shopping List Has Items", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list) and len(response) == 4:
                print(f"   ✅ Shopping list has {len(response)} items")
                # Print items for verification
                items = [item.get('name', '') for item in response if isinstance(item, dict)]
                print(f"   Items: {items}")
                return True, response
            else:
                print(f"   ❌ Shopping list wrong count: {len(response) if isinstance(response, list) else 'not list'}")
                return False, response
        return success, response

    def test_add_duplicate_ingredients(self):
        """Test adding duplicate ingredients (should increment count)"""
        ingredients_data = {
            "ingredients": ["pollo", "brócoli"]  # These should increment count
        }
        success, response = self.run_test("Add Duplicate Ingredients", "POST", "shopping-list/add", 200, data=ingredients_data)
        if success and response:
            if 'added' in response and len(response['added']) == 2:
                print("   ✅ Duplicate ingredients processed")
                return True, response
            else:
                print(f"   ❌ Duplicate addition response invalid: {response}")
                return False, response
        return success, response

    def test_verify_incremented_counts(self):
        """Test that duplicate ingredients have incremented counts"""
        success, response = self.run_test("Verify Incremented Counts", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list) and len(response) == 4:
                # Find chicken and broccoli items to check their counts
                pollo_item = next((item for item in response if item.get('name', '').lower() == 'pollo'), None)
                brocoli_item = next((item for item in response if item.get('name', '').lower() == 'brócoli'), None)
                
                if pollo_item and pollo_item.get('count') == 2 and brocoli_item and brocoli_item.get('count') == 2:
                    print("   ✅ Duplicate ingredients have correct counts (x2)")
                    return True, response
                else:
                    print(f"   ❌ Count increments incorrect - Pollo: {pollo_item}, Brócoli: {brocoli_item}")
                    return False, response
            else:
                print(f"   ❌ Shopping list count changed: {len(response) if isinstance(response, list) else 'not list'}")
                return False, response
        return success, response

    def test_toggle_shopping_item(self):
        """Test toggling an item's checked status"""
        # Toggle first item
        params = {"name": "Pollo"}
        success, response = self.run_test("Toggle Shopping Item", "PUT", "shopping-list/toggle", 200, params=params)
        if success and response:
            if 'checked' in response:
                print(f"   ✅ Item toggled - checked: {response['checked']}")
                return True, response
            else:
                print(f"   ❌ Toggle response invalid: {response}")
                return False, response
        return success, response

    def test_verify_item_toggled(self):
        """Test that item was actually toggled"""
        success, response = self.run_test("Verify Item Toggled", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list):
                pollo_item = next((item for item in response if item.get('name', '').lower() == 'pollo'), None)
                if pollo_item and pollo_item.get('checked') == True:
                    print("   ✅ Item is now checked")
                    return True, response
                else:
                    print(f"   ❌ Item not properly toggled: {pollo_item}")
                    return False, response
            else:
                print(f"   ❌ Shopping list response invalid")
                return False, response
        return success, response

    def test_remove_individual_item(self):
        """Test removing individual item from shopping list"""
        params = {"name": "Brócoli"}
        success, response = self.run_test("Remove Individual Item", "DELETE", "shopping-list/item", 200, params=params)
        if success and response:
            if 'message' in response and 'eliminado' in response['message']:
                print("   ✅ Item removed successfully")
                return True, response
            else:
                print(f"   ❌ Remove response invalid: {response}")
                return False, response
        return success, response

    def test_verify_item_removed(self):
        """Test that item was actually removed"""
        success, response = self.run_test("Verify Item Removed", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list) and len(response) == 3:
                # Check brócoli is no longer in list
                brocoli_item = next((item for item in response if 'brócoli' in item.get('name', '').lower()), None)
                if brocoli_item is None:
                    print("   ✅ Brócoli successfully removed from list")
                    return True, response
                else:
                    print(f"   ❌ Brócoli still in list: {brocoli_item}")
                    return False, response
            else:
                print(f"   ❌ Shopping list count incorrect: {len(response) if isinstance(response, list) else 'not list'}")
                return False, response
        return success, response

    def test_clear_shopping_list(self):
        """Test clearing entire shopping list"""
        success, response = self.run_test("Clear Shopping List", "DELETE", "shopping-list/clear", 200)
        if success and response:
            if 'message' in response and 'vaciada' in response['message']:
                print("   ✅ Shopping list cleared")
                return True, response
            else:
                print(f"   ❌ Clear response invalid: {response}")
                return False, response
        return success, response

    def test_verify_list_cleared(self):
        """Test that shopping list is actually empty"""
        success, response = self.run_test("Verify List Cleared", "GET", "shopping-list", 200)
        if success and response:
            if isinstance(response, list) and len(response) == 0:
                print("   ✅ Shopping list is completely empty")
                return True, response
            else:
                print(f"   ❌ Shopping list not empty: {response}")
                return False, response
        return success, response

    def test_export_json(self):
        """Test JSON export functionality"""
        success, response = self.run_test("Export JSON", "GET", "export/json", 200)
        if success and response:
            if 'weekly_plan' in response and 'export_date' in response:
                print("   ✅ JSON export successful")
                return True, response
            else:
                print(f"   ❌ JSON export structure invalid: {list(response.keys()) if isinstance(response, dict) else response}")
                return False, response
        return success, response

    def test_export_csv(self):
        """Test CSV export functionality"""
        success, _ = self.run_test("Export CSV", "GET", "export/csv", 200)
        return success, {}

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